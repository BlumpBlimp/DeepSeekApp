#!/usr/bin/env python3
"""
DeepSeek Chat - Main Entry Point
"""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now import your modules
from chat_interface import InteractiveChat
from deepseek_client import DeepSeekClient
from utils import save_conversation
import argparse
from rich.console import Console

console = Console()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="DeepSeek Chat Assistant")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Start interactive chat")
    parser.add_argument("--query", "-q", type=str,
                        help="Send a single query")
    parser.add_argument("--save", "-s", action="store_true",
                        help="Save conversation to file")

    args = parser.parse_args()

    if args.query:
        # Single query mode
        client = DeepSeekClient()
        response = client.single_message(args.query)
        console.print(f"\n[bold]Query:[/bold] {args.query}")
        console.print(f"[bold]Response:[/bold]\n{response}")

    elif args.interactive or not sys.stdin.isatty():
        # Interactive mode (default)
        chat = InteractiveChat()
        chat.run()

        if args.save and chat.session.conversation_history:
            filename = save_conversation(chat.session.conversation_history)
            console.print(f"[green]Conversation saved to {filename}[/green]")
    else:
        # No arguments, show help
        from rich.panel import Panel
        console.print(Panel.fit(
            "[bold cyan]DeepSeek Chat Assistant[/bold cyan]\n\n"
            "Usage:\n"
            "• [bold]python main.py -i[/bold] for interactive chat\n"
            "• [bold]python main.py -q \"Your question\"[/bold] for single query\n"
            "• [bold]python main.py --help[/bold] for more options"
        ))


if __name__ == "__main__":
    main()