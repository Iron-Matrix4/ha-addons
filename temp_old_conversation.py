"""
Conversation brain for Jarvis using Vertex AI Gemini with function calling and persistent memory.
"""
import logging
import os
from google.cloud import aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration
import config_helper as config
from memory import Memory

logger = logging.getLogger(__name__)

class JarvisConversation:
    """
    Jarvis conversation agent powered by Vertex AI Gemini.
    Integrates with persistent memory for preferences and context.
    """
    
    def __init__(self, memory: Memory):
        """
        Initialize Jarvis conversation brain.
        
        Args:
            memory: Memory instance for persistent storage
        """
        self.memory = memory
        
        # Check mode: Vertex AI or AI Studio
        if config.GCP_PROJECT_ID:
            # Vertex AI mode - no API key needed
            logger.info("Initializing in Vertex AI mode")
        else:
            # AI Studio mode - require API key
            if not config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured!")
            logger.info("Initializing in AI Studio mode")
        
        # Initialize Vertex AI
        credentials_path = "/data/gcp-credentials.json"
        if os.path.exists(credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            logger.info(f"Using GCP credentials from {credentials_path}")
        else:
            logger.warning(f"GCP credentials not found at {credentials_path}, attempting default credentials")
        
        vertexai.init(
            project=config.GCP_PROJECT_ID,
            location=config.GCP_LOCATION
        )
        
        # Get configured model (defaults to gemini-2.5-flash-lite)
        model_name = config.GEMINI_MODEL
        
        # Import Vertex AI tools
        from vertex_tools import jarvis_tool
       
        # Initialize system instruction
        system_instruction = self._build_system_prompt()
        
        # Initialize with tools and system instruction
        self.model = GenerativeModel(
            model_name,
            tools=[jarvis_tool],
            system_instruction=system_instruction
        )
        
        # Start chat with internal history management
        self.chat = self.model.start_chat()
        self.history_limit = 10  # Restored history limit


        
        logger.info(f"Jarvis conversation brain initialized with Vertex AI {model_name}")
        logger.info(f"GCP Project: {config.GCP_PROJECT_ID}")
        logger.info("Function calling tools enabled: HA control, weather, search")
    
    def _build_system_prompt(self) -> str:
        """Build dynamic system prompt including user preferences from memory."""
        
        # Load user preferences from memory
        prefs = self.memory.get_all_preferences()
        pref_str = "\n".join([f"- {k}: {v}" for k, v in prefs.items()]) if prefs else "None"

        base_prompt = f"""You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), Tony Stark's AI assistant.

PERSONA:
- Helpful, polite, and slightly witty
- Address user as 'Sir' (or 'Ma'am' if corrected)
- Keep responses concise and suitable for voice output
- DO NOT use markdown formatting (asterisks, hash signs, etc.) - it will be read aloud

USER PREFERENCES & MEMORY:
{pref_str}

HOME ASSISTANT CONTROL:
- If you're not 100% certain of the exact entity_id, use search_ha_entities() FIRST
- Use control_home_assistant() to control devices
- Use get_ha_state() to query device states  
- When user gives multiple commands, infer room context from earlier commands. 
- Example: "Turn on the office light and set the heating to 22" -> applies "office" to both (light.office and climate.office)

LOCATIONS & TOOLS:
- Handle weather queries by checking 'home_location' or asking if unknown.
- Use query_unifi_controller() for all network statistics and WAN IP queries.
- When describing camera snapshots, be descriptive but avoid bulleted lists. Use 2-3 natural sentences.

Proactive Intelligence: 
- Answer general questions directly using your knowledge.
- Only use google_search() for news or specific live data you don't know.
- Call save_preference() IMMEDIATELY when the user shares personal info or rules.
"""
        return base_prompt.strip()

    
    def process(self, text: str) -> str:
        """
        Process user input and return Jarvis response.
        
        Args:
            text: User input text from STT
            
        Returns:
            str: Jarvis response text (for TTS)
        """
        try:
            # Manual memory command detection (temporary workaround)
            text_lower = text.lower()
            
            # Handle "remember [location name] is [address]" / "save [location] as [address]"
            if "remember" in text_lower or "save" in text_lower or "set" in text_lower:
                # Try to extract location name and address
                # Patterns: "remember work is 123 Main St", "save gym as Fitness Center", "set mom to 456 Oak Ave"
                for pattern in [" is ", " as ", " to "]:
                    if pattern in text_lower:
                        parts = text.split(pattern, 1)
                        prefix = parts[0].lower()
                        address = parts[1].strip().rstrip('.')
                        
                        # Extract location name from prefix
                        location_name = None
                        if "remember" in prefix:
                            location_name = prefix.replace("remember", "").replace("my", "").strip()
                        elif "save" in prefix:
                            location_name = prefix.replace("save", "").replace("my", "").strip()
                        elif "set" in prefix:
                            location_name = prefix.replace("set", "").replace("my", "").strip()
                        
                        if location_name:
                            # Special handling for "home" vs other locations
                            if "home" in location_name or "location" in location_name:
                                pref_key = "home_location"
                                display_name = "your home"
                            else:
                                # Remove words like "location", "address" from the name
                                location_name = location_name.replace("location", "").replace("address", "").strip()
                                pref_key = f"{location_name}_location"
                                display_name = location_name
                            
                            self.memory.set_preference(pref_key, address)
                            return f"Understood, Sir. I've logged {display_name} as {address}."
            
            # Handle "what's my home" / "where do I live"
            if (("what" in text_lower or "where" in text_lower) and 
                ("home" in text_lower or "live" in text_lower)):
                home = self.memory.get_preference("home_location")
                if home:
                    return f"Your home is in {home}, Sir."
            
            # Build dynamic system prompt (for preferences only - Vertex handles base prompt via instruction)
            current_prefs = self.memory.get_all_preferences()
            if current_prefs:
                pref_msg = "Current preferences: " + str(current_prefs)
                # We append preferences to the user message to keep them fresh without re-init
                chat_message = f"{text}\n\n(Context: {pref_msg})"
            else:
                chat_message = text
            
            # Limit history if it gets too long
            if len(self.chat.history) > self.history_limit * 2:
                logger.info(f"Trimming chat history (current size: {len(self.chat.history)})")
                # Use internal _history as 'history' property is read-only
                try:
                    self.chat._history = self.chat.history[-(self.history_limit * 2):]
                except Exception as history_err:
                    logger.warning(f"Could not trim history via _history: {history_err}")
                    # Fallback: start a new chat if trimming fails
                    self.chat = self.model.start_chat(history=self.chat.history[-(self.history_limit * 2):])

            logger.info(f"User: {text}")
            
            response = self.chat.send_message(
                chat_message,
                generation_config={"temperature": 0.7, "max_output_tokens": 256}
            )

            
            # Loop through function calls until we get text
            max_function_calls = 5  # Prevent infinite loops
            function_call_count = 0
            
            while function_call_count < max_function_calls:
                # Debug: Log response structure
                logger.info(f"Response candidates: {len(response.candidates)}")
                if not response.candidates:
                    break
                
                candidate = response.candidates[0]
                logger.info(f"Finish reason: {candidate.finish_reason}")
                logger.info(f"Safety ratings: {candidate.safety_ratings}")
                    
                parts = candidate.content.parts
                logger.info(f"Response parts: {len(parts)}")
                
                # Check if any part is a function call - collect ALL function calls first
                has_function_call = False
                function_results = []
                
                # Import tools once at the start
                from tools import (
                    control_home_assistant,
                    get_ha_state,
                    search_ha_entities,
                    get_person_location,
                    get_appliance_status,
                    get_weather,
                    get_travel_time,
                    google_search,
                    add_calendar_event,
                    list_calendar_events,
                    create_location_reminder,
                    play_music,
                    save_preference,
                    get_preference,
                    delete_preference,
                    get_current_time,
                    query_radarr,
                    add_to_radarr,
                    query_sonarr,
                    add_to_sonarr,
                    query_qbittorrent,
                    query_prowlarr,
                    check_vpn_status,
                    query_unifi_network,
                    query_unifi_controller,
                    analyze_camera,
                )
                
                # Map function names to actual functions
                function_map = {
                    "control_home_assistant": control_home_assistant,
                    "get_ha_state": get_ha_state,
                    "search_ha_entities": search_ha_entities,
                    "get_person_location": get_person_location,
                    "get_appliance_status": get_appliance_status,
                    "get_weather": get_weather,
                    "get_travel_time": get_travel_time,
                    "google_search": google_search,
                    "add_calendar_event": add_calendar_event,
                    "list_calendar_events": list_calendar_events,
                    "create_location_reminder": create_location_reminder,
                    "play_music": play_music,
                    "save_preference": save_preference,
                    "get_preference": get_preference,
                    "delete_preference": delete_preference,
                    "get_current_time": get_current_time,
                    "query_radarr": query_radarr,
                    "add_to_radarr": add_to_radarr,
                    "query_sonarr": query_sonarr,
                    "add_to_sonarr": add_to_sonarr,
                    "query_qbittorrent": query_qbittorrent,
                    "query_prowlarr": query_prowlarr,
                    "check_vpn_status": check_vpn_status,
                    "query_unifi_network": query_unifi_network,
                    "query_unifi_controller": query_unifi_controller,
                    "analyze_camera": analyze_camera,
                }
                
                for i, part in enumerate(parts):
                    logger.info(f"Part {i}: has function_call = {hasattr(part, 'function_call')}")
                    
                    if hasattr(part, 'function_call'):
                        logger.info(f"Part {i} function_call object: {part.function_call}")
                        logger.info(f"Part {i} function_call bool: {bool(part.function_call)}")
                    
                    if hasattr(part, 'function_call') and part.function_call:
                        has_function_call = True
                        function_call_count += 1
                        
                        # Execute the function call
                        function_name = part.function_call.name
                        function_args = dict(part.function_call.args)
                        
                        logger.info(f"Function call {function_call_count}: {function_name}({function_args})")
                        
                        if function_name in function_map:
                            try:
                                # Call the function
                                result = function_map[function_name](**function_args)
                                logger.info(f"Function result: {result}")
                                function_results.append(f"{function_name}: {result}")
                                
                            except Exception as e:
                                logger.error(f"Function execution error: {e}", exc_info=True)
                                function_results.append(f"{function_name}: Error - {str(e)}")
                
                # If we had function calls, send ALL results back together
                if has_function_call and function_results:
                    combined_results = "\n".join(function_results)
                    logger.info(f"Sending {len(function_results)} function results back to model")
                    
                    try:
                        response = self.chat.send_message(
                            f"Function results:\n{combined_results}",
                            generation_config={"temperature": 0.7, "max_output_tokens": 256}
                        )
                    except Exception as model_error:
                        # Handle malformed response errors - retry with simpler format
                        logger.warning(f"Model error on function result, retrying: {model_error}")
                        try:
                            # Reset chat and try with direct instruction
                            response = self.chat.send_message(
                                f"Based on these results, provide a natural response: {combined_results}",
                                generation_config={"temperature": 0.5, "max_output_tokens": 200}
                            )
                        except Exception as retry_error:
                            logger.error(f"Retry also failed: {retry_error}")
                            # Return a helpful response based on the function results
                            if "turn_on" in combined_results.lower() or "success" in combined_results.lower():
                                return "Done, Sir. I've executed those commands for you."
                            elif "not found" in combined_results.lower() or "error" in combined_results.lower():
                                # Try to extract the actual error message
                                if "Route not found" in combined_results:
                                    return "I apologize, Sir, but I couldn't find a route for that location. Could you provide a more specific address or postcode?"
                                elif "not configured" in combined_results.lower():
                                    return "I apologize, Sir, but that feature isn't currently configured."
                                else:
                                    return f"I encountered an issue, Sir: {combined_results[:150]}"
                            else:
                                return f"I executed the commands. Results: {combined_results[:200]}"
                    
                    continue  # Continue loop to check new response
                
                # If no function calls, we have text - exit loop
                if not has_function_call:
                    break
            
            # Get the final text response
            try:
                response_text = response.text
            except (ValueError, AttributeError) as e:
                # If still no text after max calls, log and return error
                logger.error(f"No text response after {function_call_count} function calls: {e}")
                response_text = "I apologize, Sir. I encountered an issue formulating my response."
            
            logger.info(f"Jarvis: {response_text}")
            
            # Save conversation to memory for context
            # Detect if this was an error response
            is_error = any(keyword in response_text.lower() for keyword in [
                'error', 'failed', 'could not', 'unable to', 'issue', 'problem', 
                'apolog', 'sorry', 'encountered an', 'cannot'
            ])
            self.memory.save_context(text, response_text, is_error=is_error)
            
            return response_text
        
        except Exception as e:
            # Check if this is a safety block error
            error_str = str(e)
            if "Finish reason: 2" in error_str or "ResponseValidationError" in str(type(e)):
                logger.error(f"Safety block detected: {e}")
                return "I apologize, Sir, but that request triggered a safety filter. This sometimes happens with complex multi-step queries. Try breaking it into simpler parts - for example, ask for each destination separately."
            
            logger.error(f"Vertex AI error: {e}", exc_info=True)
            return f"I encountered an error processing that, Sir. {str(e)}"
    
    def reset_conversation(self):
        """Reset conversation history (but keep memory)."""
        self.chat = self.model.start_chat()
        logger.info("Conversation history reset")
