import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


class Config:
    """Configuration manager for DeepSeek API"""

    @staticmethod
    def get_api_key() -> str:
        """Get API key from environment"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in .env file")
        return api_key

    @staticmethod
    def get_base_url() -> str:
        """Get base URL for API"""
        return os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    @staticmethod
    def get_model() -> str:
        """Get model name"""
        return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    @staticmethod
    def get_max_tokens() -> int:
        """Get max tokens for responses"""
        return int(os.getenv("MAX_TOKENS", "1000"))

    @staticmethod
    def get_temperature() -> float:
        """Get temperature for responses"""
        return float(os.getenv("TEMPERATURE", "0.7"))