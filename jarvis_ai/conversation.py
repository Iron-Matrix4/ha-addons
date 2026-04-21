"""
Conversation brain for Jarvis using Modern Google GenAI (Vertex AI mode) with function calling and persistent memory.
"""
import logging
import os
import config_helper as config
from memory import Memory
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class JarvisConversation:
    """
    Jarvis conversation agent powered by Modern Google GenAI (Vertex AI mode).
    Integrates with persistent memory for preferences and context.
    """
    
    def __init__(self, memory: Memory):
        """
        Initialize Jarvis conversation brain.
        
        Args:
            memory: Memory instance for persistent storage
        """
        self.memory = memory
        
        # Initialize Modern Google GenAI Client
        credentials_path = "/data/gcp-credentials.json"
        if os.path.exists(credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            logger.info(f"Using GCP credentials from {credentials_path}")
        else:
            logger.warning(f"GCP credentials not found at {credentials_path}, attempting default credentials")
        
        self.client = genai.Client(
            vertexai=True,
            project=config.GCP_PROJECT_ID,
            location="us-central1"
        )
        
        # Get configured model (defaults to gemini-2.5-flash)
        self.model_name = config.GEMINI_MODEL
        
        # Import tools format for new SDK
        from vertex_tools import jarvis_tool_list
       
        # Initialize chat
        self.chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                tools=jarvis_tool_list,
                temperature=0.7,
                max_output_tokens=1024
            )
        )
        
        logger.info(f"Jarvis conversation brain initialized with Modern SDK: {self.model_name}")
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
- Example: If function returns "23 °C", say "23" or "23 degrees" based on preference
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
- Always use `query_unifi_controller()` for UniFi network information if configured (WAN IP, DHCP, clients, networks)
- You can use network NAMES instead of subnets: "next IP in IoT" or "stats for Main-Network"
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
        """
        try:
            # Manual memory command detection (temporary workaround)
            text_lower = text.lower()
            
            # Handle "remember [location name] is [address]" / "save [location] as [address]"
            if "remember" in text_lower or "save" in text_lower or "set" in text_lower:
                for pattern in [" is ", " as ", " to "]:
                    if pattern in text:
                        parts = text.split(pattern, 1)
                        prefix = parts[0].lower()
                        address = parts[1].strip().rstrip('.')
                        is_location_command = (
                            "location" in prefix or 
                            "address" in prefix or 
                            "home" in prefix or
                            any(keyword in address.lower() for keyword in ["street", "road", "avenue", "drive", "lane", "way", " st ", " rd ", " ave "]) or
                            (len(address) > 15 and any(char.isdigit() for char in address))
                        )
                        
                        if not is_location_command:
                            continue
                        
                        location_name = None
                        if "remember" in prefix:
                            location_name = prefix.replace("remember", "").replace("my", "").strip()
                        elif "save" in prefix:
                            location_name = prefix.replace("save", "").replace("my", "").strip()
                        elif "set" in prefix:
                            location_name = prefix.replace("set", "").replace("my", "").strip()
                        
                        if location_name:
                            if "home" in location_name or "location" in location_name:
                                pref_key = "home_location"
                                display_name = "your home"
                            else:
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
            
            # Build message
            message = text
            if len(self.chat._curated_history) == 0:
                system_prompt = self._build_system_prompt()
                message = f"{system_prompt}\n\nUser: {text}"
                logger.info("First message with system prompt")
            else:
                logger.info(f"User: {text}")

            # Send initial message
            response = self.chat.send_message(message)
            
            # Import tools
            from tools import (
                control_home_assistant, get_ha_state, search_ha_entities,
                get_person_location, get_appliance_status, get_weather,
                get_travel_time, google_search, add_calendar_event,
                list_calendar_events, create_location_reminder, play_music,
                save_preference, get_preference, delete_preference,
                get_current_time, query_radarr, add_to_radarr,
                query_sonarr, add_to_sonarr, query_qbittorrent,
                query_prowlarr, check_vpn_status, query_unifi_network,
                query_unifi_controller, analyze_camera,
            )
            
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

            # Function calling loop
            max_calls = 5
            calls = 0
            while calls < max_calls:
                last_candidate = response.candidates[0]
                has_fc = any(p.function_call for p in last_candidate.content.parts)
                
                if not has_fc:
                    break
                    
                calls += 1
                function_calls = [p.function_call for p in last_candidate.content.parts if p.function_call]
                tool_responses = []
                
                for fc in function_calls:
                    logger.info(f"Function call: {fc.name}({fc.args})")
                    if fc.name in function_map:
                        try:
                            result = function_map[fc.name](**dict(fc.args))
                            logger.info(f"Result: {result}")
                            tool_responses.append(
                                types.Part.from_function_response(
                                    name=fc.name,
                                    response={'result': result}
                                )
                            )
                        except Exception as e:
                            logger.error(f"Function {fc.name} error: {e}")
                            tool_responses.append(
                                types.Part.from_function_response(
                                    name=fc.name,
                                    response={'error': str(e)}
                                )
                            )
                
                # Send results back
                response = self.chat.send_message(tool_responses)

            response_text = response.text
            logger.info(f"Jarvis: {response_text}")
            
            # Save conversation
            is_error = any(kw in response_text.lower() for kw in ['error', 'failed', 'could not', 'unable to', 'issue', 'problem', 'apolog', 'sorry', 'cannot'])
            self.memory.save_context(text, response_text, is_error=is_error)
            
            return response_text
        
        except Exception as e:
            logger.error(f"Brain error: {e}", exc_info=True)
            return f"I encountered an error processing that, Sir. {str(e)}"
    
    def reset_conversation(self):
        """Reset conversation history (but keep memory)."""
        self.chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                tools=self.chat.config.tools,
                temperature=0.7,
                max_output_tokens=1024
            )
        )
        logger.info("Conversation history reset")
