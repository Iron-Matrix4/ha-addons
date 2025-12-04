import google.generativeai as genai
import openai
import config

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
            "as they will be read aloud."
        )

        if self.provider == "gemini":
            if not config.GEMINI_API_KEY:
                print("Warning: GEMINI_API_KEY not found in environment variables.")
            else:
                genai.configure(api_key=config.GEMINI_API_KEY)
                # Using gemini-2.0-flash as it is available and fast
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                self.chat = self.model.start_chat(history=[])
        
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
                
                # Gemini doesn't support system prompts in the same way as OpenAI in the basic API,
                # but we can prepend it or use the system instruction if available in the specific model version.
                # For simplicity, we'll just send the message. 
                # To enforce the persona, we can prepend the instruction to the first message 
                # or rely on the chat history if we pre-seed it.
                
                # A simple workaround for the persona in a running chat:
                if not self.chat.history:
                    response = self.chat.send_message(f"{self.system_prompt}\n\nUser: {text}")
                else:
                    response = self.chat.send_message(text)
                return response.text
            except Exception as e:
                return f"I encountered an error processing that, Sir. {e}"

        elif self.provider == "openai":
            try:
                self.history.append({"role": "user", "content": text})
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo", # or gpt-4
                    messages=self.history
                )
                reply = response.choices[0].message.content
                self.history.append({"role": "assistant", "content": reply})
                return reply
            except Exception as e:
                return f"I encountered an error processing that, Sir. {e}"
        
        return "I am not connected to a brain, Sir."
