from typing import List, Dict, Optional
import os
import json
from datetime import datetime
from .document_processor import DocumentProcessor
from .quiz_generator import QuizGenerator
from .verifier import LLMVerifier
from .deepseek_client import DeepSeekClient
from .progress_tracker import ProgressTracker
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class StudyAssistant:
    """Main study assistant combining all features"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.documents_dir = os.path.join(data_dir, "documents")
        self.quizzes_dir = os.path.join(data_dir, "quizzes")
        self.progress_dir = os.path.join(data_dir, "progress")

        # Create directories
        os.makedirs(self.documents_dir, exist_ok=True)
        os.makedirs(self.quizzes_dir, exist_ok=True)
        os.makedirs(self.progress_dir, exist_ok=True)

        # Initialize components
        self.doc_processor = DocumentProcessor()
        self.quiz_gen = QuizGenerator()
        self.verifier = LLMVerifier()
        self.deepseek = DeepSeekClient()
        self.progress_tracker = ProgressTracker(self.progress_dir)

    def load_study_materials(self):
        """Load all study materials from documents directory"""
        console.print(Panel.fit("[bold cyan]📚 Loading Study Materials[/bold cyan]"))

        materials = []
        for filename in os.listdir(self.documents_dir):
            filepath = os.path.join(self.documents_dir, filename)
            if filename.endswith(('.pdf', '.docx', '.txt', '.md')):
                try:
                    console.print(f"  📄 Loading: {filename}")
                    chunks = self.doc_processor.index_document(filepath, {
                        "filename": filename,
                        "loaded_date": datetime.now().isoformat()
                    })
                    materials.append({
                        "filename": filename,
                        "chunks": chunks,
                        "path": filepath
                    })
                except Exception as e:
                    console.print(f"  ❌ Error loading {filename}: {e}")

        console.print(f"\n✅ Loaded {len(materials)} study materials")
        return materials

    def generate_study_plan(self, topics: List[str], hours_per_day: int = 2,
                            days: int = 7) -> Dict:
        """Generate a personalized study plan"""
        console.print(Panel.fit("[bold green]📅 Generating Study Plan[/bold green]"))

        prompt = f"""
        Create a study plan with these topics: {', '.join(topics)}
        Available time: {hours_per_day} hours per day for {days} days
        Total hours: {hours_per_day * days}

        Include:
        1. Daily schedule
        2. Topic breakdown
        3. Study techniques
        4. Review sessions
        5. Practice exercises
        6. Rest breaks

        Format as a structured study plan.
        """

        response = self.deepseek.single_message(
            prompt,
            system_prompt="You are an expert study planner and educational consultant."
        )

        plan = {
            "topics": topics,
            "total_days": days,
            "hours_per_day": hours_per_day,
            "total_hours": hours_per_day * days,
            "generated_date": datetime.now().isoformat(),
            "plan": response,
            "daily_schedule": self._parse_daily_schedule(response)
        }

        # Save plan
        plan_file = os.path.join(self.progress_dir, f"study_plan_{datetime.now().strftime('%Y%m%d')}.json")
        with open(plan_file, 'w') as f:
            json.dump(plan, f, indent=2)

        console.print(f"✅ Study plan saved to: {plan_file}")
        return plan

    def _parse_daily_schedule(self, plan_text: str) -> List[Dict]:
        """Extract daily schedule from plan text"""
        # Simplified parsing - in practice, use more sophisticated NLP
        days = []
        lines = plan_text.split('\n')

        current_day = {}
        for line in lines:
            line = line.strip()
            if 'day' in line.lower() and any(str(i) in line for i in range(1, 8)):
                if current_day:
                    days.append(current_day)
                current_day = {"title": line, "activities": []}
            elif line and current_day and len(line) > 10:
                current_day["activities"].append(line)

        if current_day:
            days.append(current_day)

        return days

    def start_study_session(self, topic: Optional[str] = None):
        """Start an interactive study session"""
        console.clear()
        console.print(Panel.fit(
            "[bold magenta]🎓 DEEPSEEK STUDY ASSISTANT[/bold magenta]\n"
            "[dim]Your AI-powered study companion[/dim]"
        ))

        while True:
            console.print("\n[bold cyan]Study Menu:[/bold cyan]")
            console.print("  1. 📚 Review study materials")
            console.print("  2. ❓ Take a quiz")
            console.print("  3. 🔍 Search documents")
            console.print("  4. ✅ Verify LLM responses")
            console.print("  5. 📊 View progress")
            console.print("  6. 🗂️  Manage documents")
            console.print("  7. 🏁 Exit")

            choice = console.input("\n[bold green]Select option (1-7):[/bold green] ").strip()

            if choice == '1':
                self._review_materials(topic)
            elif choice == '2':
                self._take_quiz(topic)
            elif choice == '3':
                self._search_documents()
            elif choice == '4':
                self._verify_llm_responses()
            elif choice == '5':
                self._view_progress()
            elif choice == '6':
                self._manage_documents()
            elif choice == '7':
                console.print("[yellow]Goodbye! Happy studying! 👋[/yellow]")
                break
            else:
                console.print("[red]Invalid choice. Please try again.[/red]")

    def _review_materials(self, topic: Optional[str]):
        """Review study materials on a specific topic"""
        if topic:
            console.print(f"\n[bold]Reviewing topic: {topic}[/bold]")
            results = self.doc_processor.search_documents(topic, n_results=3)
        else:
            topic = console.input("\n[bold]Enter topic to review: [/bold]").strip()
            results = self.doc_processor.search_documents(topic, n_results=5)

        if not results:
            console.print("[yellow]No relevant materials found.[/yellow]")
            return

        console.print(f"\n📖 Found {len(results)} relevant sections:")
        for i, result in enumerate(results, 1):
            console.print(f"\n{i}. {result['document'][:200]}...")
            console.print(f"   [dim]Source: {result['metadata']['filepath']}[/dim]")

        # Ask if user wants to generate questions
        if console.input("\nGenerate questions on this material? (y/n): ").lower() == 'y':
            context = "\n".join([r['document'] for r in results[:2]])
            questions = self.quiz_gen.generate_questions(context, count=3)
            self._take_generated_quiz(questions)

    def _take_quiz(self, topic: Optional[str]):
        """Take a quiz on a topic"""
        if topic:
            console.print(f"\n[bold]Generating quiz on: {topic}[/bold]")
            results = self.doc_processor.search_documents(topic, n_results=2)
            if results:
                context = "\n".join([r['document'] for r in results])
                questions = self.quiz_gen.generate_questions(context, count=5)
                self._take_generated_quiz(questions)
            else:
                console.print("[yellow]No materials found for this topic.[/yellow]")
        else:
            # Use pre-generated quizzes
            quiz_files = [f for f in os.listdir(self.quizzes_dir) if f.endswith('.json')]
            if quiz_files:
                console.print("\n[bold]Available quizzes:[/bold]")
                for i, f in enumerate(quiz_files, 1):
                    console.print(f"  {i}. {f}")

                choice = console.input("\nSelect quiz number: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(quiz_files):
                    quiz_file = os.path.join(self.quizzes_dir, quiz_files[int(choice) - 1])
                    with open(quiz_file, 'r') as f:
                        questions = json.load(f)
                    self._take_generated_quiz(questions)
            else:
                console.print("[yellow]No quizzes found. Generate one first![/yellow]")

    def _take_generated_quiz(self, questions: List[Dict]):
        """Take a generated quiz"""
        score, total, results = self.quiz_gen.conduct_quiz(questions)

        console.print(f"\n{'=' * 60}")
        console.print(f"📊 Quiz Results: {score}/{total} ({score / total * 100:.1f}%)")
        console.print(f"{'=' * 60}")

        # Save results
        result_data = {
            "date": datetime.now().isoformat(),
            "score": score,
            "total": total,
            "percentage": score / total * 100,
            "results": results
        }

        result_file = os.path.join(self.progress_dir, f"quiz_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)

        # Update progress
        self.progress_tracker.update_quiz_results(result_data)

        console.print(f"\n✅ Results saved to: {result_file}")

    def _search_documents(self):
        """Search through study documents"""
        query = console.input("\n[bold]Enter search query: [/bold]").strip()
        if not query:
            return

        results = self.doc_processor.search_documents(query, n_results=10)

        console.print(f"\n🔍 Search results for '{query}':")
        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", width=5)
        table.add_column("Content", width=80)
        table.add_column("Source", width=20)

        for i, result in enumerate(results, 1):
            content = result['document']
            if len(content) > 100:
                content = content[:97] + "..."
            table.add_row(
                str(i),
                content,
                os.path.basename(result['metadata']['filepath'])
            )

        console.print(table)

    def _verify_llm_responses(self):
        """Verify LLM responses"""
        console.print(Panel.fit("[bold yellow]🔍 LLM Response Verifier[/bold yellow]"))

        query = console.input("\n[bold]Enter the original query: [/bold]").strip()
        response = console.input("\n[bold]Enter the response to verify: [/bold]").strip()

        if not query or not response:
            console.print("[red]Both query and response are required.[/red]")
            return

        console.print("\n[dim]Verifying response...[/dim]")

        # In production, use asyncio
        verification = asyncio.run(self.verifier.verify_response(query, response))

        console.print(f"\n✅ Verification complete!")
        console.print(f"Agreement ratio: {verification['agreement_ratio']:.2%}")
        console.print(f"Verified: {'✅' if verification['verified'] else '❌'}")

        console.print("\n[bold]Feedback from models:[/bold]")
        for feedback in verification['feedback']:
            console.print(f"  • {feedback}")

    def _view_progress(self):
        """View study progress"""
        progress = self.progress_tracker.get_progress_summary()

        console.print(Panel.fit("[bold green]📊 Study Progress Report[/bold green]"))

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="dim")
        table.add_column("Value")

        table.add_row("Study Sessions", str(progress.get('total_sessions', 0)))
        table.add_row("Quizzes Taken", str(progress.get('total_quizzes', 0)))
        table.add_row("Average Quiz Score", f"{progress.get('average_score', 0):.1f}%")
        table.add_row("Total Study Time", f"{progress.get('total_study_hours', 0):.1f} hours")
        table.add_row("Documents Loaded", str(progress.get('documents_loaded', 0)))

        console.print(table)

        # Show recent activity
        recent = progress.get('recent_activity', [])
        if recent:
            console.print("\n[bold]Recent Activity:[/bold]")
            for activity in recent[:5]:
                console.print(f"  • {activity}")

    def _manage_documents(self):
        """Manage study documents"""
        console.print(Panel.fit("[bold blue]🗂️ Document Management[/bold blue]"))

        files = os.listdir(self.documents_dir)
        console.print(f"\nDocuments in '{self.documents_dir}':")

        if not files:
            console.print("[yellow]No documents found.[/yellow]")
        else:
            for i, f in enumerate(files, 1):
                size = os.path.getsize(os.path.join(self.documents_dir, f)) / 1024
                console.print(f"  {i}. {f} ({size:.1f} KB)")

        console.print("\nOptions:")
        console.print("  1. Add new document")
        console.print("  2. Remove document")
        console.print("  3. Back to main menu")

        choice = console.input("\nSelect option: ").strip()

        if choice == '1':
            filepath = console.input("Enter path to document: ").strip()
            if os.path.exists(filepath):
                import shutil
                shutil.copy(filepath, os.path.join(self.documents_dir, os.path.basename(filepath)))
                console.print("[green]Document added successfully![/green]")
            else:
                console.print("[red]File not found.[/red]")
        elif choice == '2':
            if files:
                doc_num = console.input("Enter document number to remove: ").strip()
                if doc_num.isdigit() and 1 <= int(doc_num) <= len(files):
                    os.remove(os.path.join(self.documents_dir, files[int(doc_num) - 1]))
                    console.print("[green]Document removed successfully![/green]")