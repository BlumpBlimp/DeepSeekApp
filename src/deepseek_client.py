from openai import OpenAI
from typing import List, Dict, Optional
from .config import Config


class DeepSeekClient:
    """Client for interacting with DeepSeek API"""

    def __init__(self):
        self.client = OpenAI(
            api_key=Config.get_api_key(),
            base_url=Config.get_base_url()
        )
        self.model = Config.get_model()
        self.max_tokens = Config.get_max_tokens()
        self.temperature = Config.get_temperature()

    def chat(self, messages: List[Dict], stream: bool = False) -> str:
        """Send chat messages to DeepSeek"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=stream
            )

            if stream:
                return self._handle_stream_response(response)
            else:
                return response.choices[0].message.content

        except Exception as e:
            return f"Error: {e}"

    def _handle_stream_response(self, response):
        """Handle streaming responses"""
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                print(content, end="", flush=True)
        return full_response

    def single_message(self, message: str, system_prompt: Optional[str] = None) -> str:
        """Send a single message with optional system prompt"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": message})

        return self.chat(messages)