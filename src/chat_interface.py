from typing import List, Dict
from .deepseek_client import DeepSeekClient
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import time

console = Console()


class ChatSession:
    """Manages a chat session with history"""

    def __init__(self, system_prompt: str = "You are a helpful assistant."):
        self.client = DeepSeekClient()
        self.messages = [{"role": "system", "content": system_prompt}]
        self.conversation_history = []

    def add_message(self, role: str, content: str):
        """Add a message to the conversation"""
        self.messages.append({"role": role, "content": content})

    def get_response(self, user_input: str) -> str:
        """Get response from DeepSeek for user input"""
        self.add_message("user", user_input)

        with console.status("[bold green]Thinking...", spinner="dots"):
            start_time = time.time()
            response = self.client.chat(self.messages)
            elapsed_time = time.time() - start_time

        self.add_message("assistant", response)
        self.conversation_history.append({
            "user": user_input,
            "assistant": response,
            "time": elapsed_time
        })

        return response

    def display_conversation(self):
        """Display the entire conversation"""
        console.print(Panel.fit("[bold cyan]Conversation History[/bold cyan]"))

        for i, exchange in enumerate(self.conversation_history, 1):
            console.print(f"\n[bold yellow]Exchange {i}:[/bold yellow]")
            console.print(f"[green]You:[/green] {exchange['user']}")
            console.print(f"[blue]Assistant:[/blue] {exchange['assistant']}")
            console.print(f"[dim]Time: {exchange['time']:.2f}s[/dim]")

    def clear_history(self):
        """Clear conversation history (keep system prompt)"""
        system_msg = self.messages[0]
        self.messages = [system_msg]
        self.conversation_history = []
        console.print("[yellow]Conversation cleared[/yellow]")


class InteractiveChat:
    """Interactive command-line chat interface"""

    def __init__(self):
        self.session = ChatSession()
        self.running = True

    def run(self):
        """Run the interactive chat"""
        console.print(Panel.fit(
            "[bold magenta]🤖 DeepSeek Chat Assistant[/bold magenta]\n"
            "[dim]Type 'quit' to exit, 'clear' to reset, 'help' for commands[/dim]"
        ))

        while self.running:
            try:
                user_input = console.input("\n[bold green]You:[/bold green] ").strip()

                if not user_input:
                    continue

                if user_input.lower() == 'quit':
                    self.running = False
                    console.print("[yellow]Goodbye! 👋[/yellow]")
                    break
                elif user_input.lower() == 'clear':
                    self.session.clear_history()
                    continue
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                elif user_input.lower() == 'history':
                    self.session.display_conversation()
                    continue

                # Get and display response
                response = self.session.get_response(user_input)

                console.print("\n[bold blue]Assistant:[/bold blue]")
                console.print(Markdown(response))

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'quit' to exit.[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def show_help(self):
        """Show available commands"""
        help_text = """
        Available Commands:
        • [bold]quit[/bold] - Exit the chat
        • [bold]clear[/bold] - Clear conversation history
        • [bold]history[/bold] - Show conversation history
        • [bold]help[/bold] - Show this help message

        Just type normally to chat with the assistant!
        """
        console.print(Panel.fit(help_text, title="Help"))
