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
            location="us-central1"
        )
        
        # Get configured model (defaults to gemini-2.5-flash)
        model_name = config.GEMINI_MODEL
        
        # Import Vertex AI tools
        from vertex_tools import jarvis_tool
       
        # Initialize with tools
        self.model = GenerativeModel(
            model_name,
            tools=[jarvis_tool]
        )
        
        # Start chat
        self.chat = self.model.start_chat()
        
        logger.info(f"Jarvis conversation brain initialized with Vertex AI {model_name}")
        logger.info(f"GCP Project: {config.GCP_PROJECT_ID}")
        logger.info("Function calling tools enabled: HA control, weather, search")
    
    def _build_system_prompt(self) -> str:
        """Build dynamic system prompt including user preferences from memory."""
        
        base_prompt = """You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), Tony Stark's AI assistant.

PERSONA:
- Helpful, polite, and slightly witty
- Address user as 'Sir' (or 'Ma'am' if corrected)
- Keep responses concise and suitable for voice output
- DO NOT use markdown formatting (asterisks, hash signs, etc.) - it will be read aloud

USER PREFERENCES:
- **CRITICAL**: Always check and respect user preferences listed below
- If user has preference "skip_unit_suffix" or similar, DO NOT include units in your response
  Example: If function returns "23 °C", say "23" or "23 degrees" based on preference
- If user prefers Celsius/Fahrenheit, convert temperatures accordingly
- User preferences override default formatting - follow them strictly

HOME ASSISTANT CONTROL:
- **IMPORTANT**: If you're not 100% certain of the exact entity_id, use search_ha_entities() FIRST
- Example: For "office light", search first to see all office lights, then pick the right one
- Use control_home_assistant() to control devices
- Use get_ha_state() to query device states  
- For "turn on office light" try entity_id like "light.office" or "switch.office_light"
- Many lights are actually switches - check both domains!

CAMERA ANALYSIS:
- When user asks about a camera ("what's in the garden"), always pick the HIGHEST SCORING camera automatically
- DO NOT ask which camera to use - just use the best match from search results
- When you get the analyze_camera result, describe what you see naturally
- DO NOT say "The Garden Camera HD shows..." or mention the entity name
- Just describe the scene: "I see a backyard with..."

MULTI-COMMAND CONTEXT:
- When user gives multiple commands in one request, infer room context from earlier commands
- Example: "Turn on the office light and set the heating to 22" - apply "office" to both (climate.office)
- Example: "Turn on office light and living room heating" - use the specified rooms for each
- If a room is mentioned early in the request but not repeated, carry it forward
- Only apply this inference when no explicit room is given for the later command

LOCATIONS & TRAVEL:
- Users can save locations with custom names: "Remember work is 123 Main St"
- Save as "[name]_location" preference (e.g., "work_location", "gym_location", "mom_location")
- When calculating travel time, these saved names can be used: "How long to work?" or "Time to gym from home?"
- get_travel_time() will automatically resolve saved location names

PROACTIVE KNOWLEDGE:
- Use get_weather() for weather questions
- **IMPORTANT**: You have extensive built-in knowledge - use it for general questions!
- **For Home Assistant queries**: Use search_ha_entities() when asked to find devices, entities, buttons, switches, sensors, etc.
- ONLY use google_search() when:
  * Asked explicitly to search the web ("search for...", "google...")
  * Question requires current/real-time web information (news, events, stock prices)
  * You genuinely don't know and it's not common knowledge
- For general knowledge (health, science, history, etc.), answer directly without searching
- Be helpful and find answers!

DEVICE CONTROL PATTERNS:
- **"Restart X"** commands (e.g., "restart qbittorrent", "restart VPN"):
  1. Use search_ha_entities() to find button entities containing "restart" + keyword
  2. Press the most relevant button found using control_home_assistant()
  3. Don't ask permission - just do it
- "Turn on/off X" → Use control_home_assistant() to control entities/buttons
- "Find X buttons" → Use search_ha_entities()
- HASS Agent commands appear as button entities - search and press them automatically

UNIFI NETWORK QUERIES:
        **UniFi Network Queries:**
        - Always use `query_unifi_controller()` for UniFi network information if configured (WAN IP, DHCP, clients, networks)
        - You can use network NAMES instead of subnets: \"next IP in IoT\" or \"stats for Main-Network\"  
        - Do NOT fall back to `query_unifi_network()` (which uses Home Assistant sensors) if the direct UniFi API is configured
        
        **General Knowledge vs Search:**
"""
        
        # Load user preferences from memory
        prefs = self.memory.get_all_preferences()
        
        if prefs:
            logger.info(f"Loading {len(prefs)} preferences into system prompt: {list(prefs.keys())}")
            pref_text = "\n\nUSER PREFERENCES (from memory):\n"
            for key, value in prefs.items():
                pref_text += f"- {key}: {value}\n"
            base_prompt += pref_text
        else:
            logger.info("No preferences found in memory")
        
        # Load recent conversation context (exclude errors!)
        recent_context = self.memory.get_recent_context(limit=3, include_errors=False)
        if recent_context:
            context_text = "\n\nRECENT CONTEXT:\n"
            for ctx in recent_context:
                context_text += f"User: {ctx['user']}\n"
                context_text += f"You: {ctx['assistant']}\n"
            base_prompt += context_text
        
        return base_prompt
    
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
            
            # Build system prompt with current memory/preferences
            system_prompt = self._build_system_prompt()
            
            # Send message
            if not self.chat.history:
                # First message includes system prompt
                full_message = f"{system_prompt}\n\nUser: {text}"
                logger.info(f"First message with system prompt")
            else:
                # Subsequent messages don't need system prompt repeated
                full_message = text
                logger.info(f"User: {text}")
            
            response = self.chat.send_message(
                full_message,
                generation_config={"temperature": 0.7, "max_output_tokens": 1024}
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
                            generation_config={"temperature": 0.7, "max_output_tokens": 1024}
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
