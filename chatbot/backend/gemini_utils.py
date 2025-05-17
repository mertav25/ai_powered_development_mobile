import google.generativeai as genai
from django.conf import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiHelper:
    @staticmethod
    def generate_response(prompt, model_name="gemini-pro"):
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return None

    @staticmethod
    def chat_conversation(messages, model_name="gemini-pro"):
        try:
            model = genai.GenerativeModel(model_name)
            chat = model.start_chat(history=[])
            for message in messages:
                chat.send_message(message)
            return chat.last.text
        except Exception as e:
            print(f"Gemini chat error: {str(e)}")
            return None