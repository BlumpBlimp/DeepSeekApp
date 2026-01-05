"""Basic chat example"""
from src.deepseek_client import DeepSeekClient


def main():
    client = DeepSeekClient()

    # Simple query
    response = client.single_message("Hello! How are you?")
    print(f"Response: {response}")

    # With system prompt
    response = client.single_message(
        "Write a short poem about Python",
        system_prompt="You are a creative poet."
    )
    print(f"\nPoem: {response}")


if __name__ == "__main__":
    main()