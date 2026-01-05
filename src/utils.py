import json
from datetime import datetime
from typing import Dict, List
import os


def save_conversation(conversation: List[Dict], filename: str = None) -> str:
    """Save conversation to JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(conversation, f, indent=2, ensure_ascii=False)

    return filename


def load_conversation(filename: str) -> List[Dict]:
    """Load conversation from JSON file"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return []


def format_tokens(tokens: int) -> str:
    """Format token count for display"""
    if tokens >= 1000:
        return f"{tokens / 1000:.1f}k tokens"
    return f"{tokens} tokens"


def validate_api_key(api_key: str) -> bool:
    """Basic validation of API key format"""
    return api_key.startswith('sk-') and len(api_key) > 10