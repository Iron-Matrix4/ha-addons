import google.generativeai as genai
import openai
import config
import tools
from google.protobuf.struct_pb2 import Struct

class Brain:
    def __init__(self):
        self.provider = config.LLM_PROVIDER
        self.history = []
        self.system_prompt = (
            "You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), "
            "Tony Stark's AI assistant. You are helpful, polite, and slightly witty. "
            "You address the user as 'Sir' (or 'Ma'am' if corrected). "
            "Keep your responses concise and suitable for voice output. "
            "Do not use markdown formatting like asterisks or hash signs in your response, "
            "as they will be read aloud. "
            "IMPORTANT - HOME ASSISTANT & TOOLS: "
            "1. VOCABULARY RULE: "
            "   - 'HEATING' = Control. Use `control_home_assistant` with `climate.*` entities. "
            "   - 'TEMPERATURE' = Information. Use `get_ha_state` with `sensor.*` entities. "
            "2. MISSING ROOM RULE: "
            "   - If the user does not specify a room for EITHER command, ASK 'Which room?'. "
            "   - Do NOT guess the room for control commands. "
            "3. WHOLE HOUSE: "
            "   - 'Whole house' = `climate.whole_house_heating`."
            "4. SPOTIFY: "
            "   - If asked to play music, use `play_music`."
            "5. COMPLEX LOGIC: "
            "   - If the user asks for a conditional action (e.g., 'If temp < 19, set to 20'), "
            "     first use `get_ha_state` to check the condition. Then, ONLY if the condition is met, "
            "     use `control_home_assistant` to perform the action. Report the check result to the user."
            "   - DECISIVENESS: If the user says 'Turn on [Name]', and you don't know the exact ID, guess the most logical one (e.g., `light.[name_with_underscores]`) and call `control_home_assistant`. DO NOT SEARCH/ASK. The system will auto-correct."
            "6. NATURAL SPEECH & SOCIAL INTERACTION:"
            "   - You are Jarvis. Be witty, helpful, and natural."
            "   - If asked to 'Say X' or 'Tell X to Y', do so naturally as if you are speaking TO that person."
            "     Example: 'Tell Arlo to go to bed' -> 'Arlo, go to bed.' (Direct address is more natural)."
            "   - If asked social questions ('How are you?', 'Hello'), reply in character."
            "7. FOLLOW-UP COMMANDS:"
            "   - If the user uses vague terms like 'it', 'the light', 'that one' without a specific name, "
            "     Call `get_last_interacted_entity()` to retrieve the context. "
            "   - Example: 'Turn on the office light' -> 'Turn that off' -> Use `get_last_interacted_entity` -> `turn_off(last_entity)`."
            "8. PROACTIVE KNOWLEDGE:"
            "   - If you don't know an answer (e.g., 'Population of Asia'), proactively use `google_search` to find it."
            "   - Be helpful/witty: Read the results and tell the user the answer directly. You don't need to ask permission to be helpful."
            "   - If the question is about the house, check Home Assistant."
        )

        if self.provider == "gemini":
            if not config.GEMINI_API_KEY:
                print("Warning: GEMINI_API_KEY not found in environment variables.")
            else:
                genai.configure(api_key=config.GEMINI_API_KEY)
                self.tool_functions = tools.get_tools()
                # Initialize model with tools
                self.model = genai.GenerativeModel(
                    'gemini-2.0-flash', 
                    tools=self.tool_functions
                )
                self.chat = self.model.start_chat(enable_automatic_function_calling=True)
        
        elif self.provider == "openai":
            if not config.OPENAI_API_KEY:
                print("Warning: OPENAI_API_KEY not found in environment variables.")
            else:
                self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
                self.history.append({"role": "system", "content": self.system_prompt})

    def process(self, text):
        """
        Processes the input text and returns the LLM's response.
        """
        if self.provider == "gemini":
            try:
                if not hasattr(self, 'chat'):
                    return "My connection to the Gemini grid is down, Sir. Please check my configuration."
                
                # Send message with automatic function calling enabled
                if not self.chat.history:
                    response = self.chat.send_message(f"{self.system_prompt}\n\nUser: {text}")
                else:
                    response = self.chat.send_message(text)
                
                return response.text
            except Exception as e:
                print(f"Gemini Error: {e}")
                return f"I encountered an error processing that, Sir. {e}"

        elif self.provider == "openai":
            # OpenAI function calling implementation would go here
            # For now, keeping it text-only as per original scope
            try:
                self.history.append({"role": "user", "content": text})
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=self.history
                )
                reply = response.choices[0].message.content
                self.history.append({"role": "assistant", "content": reply})
                return reply
            except Exception as e:
                return f"I encountered an error processing that, Sir. {e}"
        
        return "I am not connected to a brain, Sir."
