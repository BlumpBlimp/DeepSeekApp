#!/usr/bin/env python3
"""
ADVANCED STUDY ASSISTANT - With persistent analysis
"""
import os
import sys
import json
import PyPDF2
import docx
import shutil
from datetime import datetime
from typing import Dict, List
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AdvancedStudyAssistant:
    """Study assistant with persistent analysis"""

    def __init__(self):
        # Initialize DeepSeek client
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("❌ Error: DEEPSEEK_API_KEY not found in .env file")
            sys.exit(1)

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        # Setup directories
        self.base_dir = "advanced_study_data"
        self.documents_dir = os.path.join(self.base_dir, "documents")
        self.analysis_dir = os.path.join(self.base_dir, "analysis")
        self.config_file = os.path.join(self.base_dir, "config.json")

        for dir_path in [self.base_dir, self.documents_dir, self.analysis_dir]:
            os.makedirs(dir_path, exist_ok=True)

        # Load or create configuration
        self.config = self.load_config()

        # Load existing data
        self.documents = self.load_documents()
        self.analyses = self.load_analyses()

        print("🔬 Advanced Study Assistant initialized")
        if self.documents:
            print(f"📚 Found {len(self.documents)} previously uploaded documents")
        if self.analyses:
            print(f"📊 Found {len(self.analyses)} previously analyzed documents")

    def load_config(self) -> Dict:
        """Load or create configuration"""
        default_config = {
            "temperature": 0.3,
            "max_tokens": 1500,
            "top_p": 0.95,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.0,
            "model": "deepseek-chat",
            "analysis_depth": "standard"  # quick/standard/deep
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                pass

        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def load_documents(self) -> Dict:
        """Load documents from storage"""
        documents = {}
        supported_extensions = ['.pdf', '.docx', '.txt', '.md', '.rtf']

        for filename in os.listdir(self.documents_dir):
            filepath = os.path.join(self.documents_dir, filename)
            ext = os.path.splitext(filename)[1].lower()

            if ext in supported_extensions and os.path.isfile(filepath):
                try:
                    stat = os.stat(filepath)
                    documents[filename] = {
                        "path": filepath,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                except Exception as e:
                    print(f"⚠️  Error loading {filename}: {e}")

        return documents

    def load_analyses(self) -> Dict:
        """Load previously saved analyses"""
        analyses = {}

        for filename in os.listdir(self.analysis_dir):
            if filename.endswith('_analysis.json'):
                doc_name = filename.replace('_analysis.json', '')
                filepath = os.path.join(self.analysis_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        analyses[doc_name] = json.load(f)
                except:
                    pass

        return analyses

    def save_analysis(self, filename: str, analysis: Dict):
        """Save analysis to file"""
        analysis_file = os.path.join(self.analysis_dir, f"{filename}_analysis.json")
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        self.analyses[filename] = analysis

    def analyze_documents(self):
        """Analyze uploaded documents"""
        if not self.documents:
            print("\n❌ No documents to analyze. Please upload documents first.")
            return

        print("\n" + "=" * 60)
        print("🔬 ANALYZE DOCUMENTS")
        print("=" * 60)

        # Check which documents need analysis
        unanalyzed = []
        for filename in self.documents:
            if filename not in self.analyses:
                unanalyzed.append(filename)

        if not unanalyzed:
            print("\n✅ All documents are already analyzed")
            print("\nOptions:")
            print("1. Re-analyze all documents")
            print("2. Re-analyze specific documents")
            print("3. Back to menu")

            choice = input("\nSelect option (1-3): ").strip()

            if choice == '1':
                unanalyzed = list(self.documents.keys())
            elif choice == '2':
                self._reanalyze_specific()
                return
            else:
                return

        print(f"\n📊 Found {len(unanalyzed)} documents to analyze")

        # Select analysis depth
        print("\n📈 Analysis Depth:")
        print("1. Quick (fast, basic summary)")
        print("2. Standard (recommended, detailed)")
        print("3. Deep (slow, comprehensive)")

        depth_choice = input("\nSelect depth (1-3): ").strip()
        depths = {"1": "quick", "2": "standard", "3": "deep"}
        depth = depths.get(depth_choice, "standard")

        print(f"\n🔍 Starting {depth} analysis...")

        analyzed_count = 0
        for i, filename in enumerate(unanalyzed, 1):
            print(f"\n📝 Analyzing {i}/{len(unanalyzed)}: {filename}")

            try:
                analysis = self._analyze_single_document(filename, depth)
                self.save_analysis(filename, analysis)
                analyzed_count += 1
                print(f"  ✅ Analysis saved")

            except Exception as e:
                print(f"  ❌ Analysis failed: {e}")

        print(f"\n🎉 Analysis complete!")
        print(f"  • Successfully analyzed: {analyzed_count} documents")
        print(f"  • Total analyzed documents: {len(self.analyses)}")

    def _reanalyze_specific(self):
        """Re-analyze specific documents"""
        print("\n📄 Select documents to re-analyze:")

        for i, filename in enumerate(self.documents.keys(), 1):
            has_analysis = "✅" if filename in self.analyses else "❌"
            print(f"  {i}. {filename} {has_analysis}")

        try:
            selections = input("\nEnter document numbers (comma-separated): ").strip()
            if not selections:
                return

            doc_list = list(self.documents.keys())
            indices = [int(idx.strip()) - 1 for idx in selections.split(',')]

            print("\n🔍 Starting re-analysis...")

            for idx in indices:
                if 0 <= idx < len(doc_list):
                    filename = doc_list[idx]
                    print(f"\n📝 Re-analyzing: {filename}")

                    try:
                        analysis = self._analyze_single_document(filename, "standard")
                        self.save_analysis(filename, analysis)
                        print(f"  ✅ Re-analysis complete")
                    except Exception as e:
                        print(f"  ❌ Error: {e}")

        except:
            print("❌ Invalid input")

    def _analyze_single_document(self, filename: str, depth: str) -> Dict:
        """Analyze a single document"""
        filepath = self.documents[filename]["path"]
        content = self._read_file_content(filepath, max_chars=10000 if depth == "quick" else 20000)

        if not content:
            return {
                "error": "Could not read file content",
                "analyzed_at": datetime.now().isoformat()
            }

        # Adjust analysis based on depth
        if depth == "quick":
            prompt = f"""QUICK ANALYSIS of study document for exam preparation.

DOCUMENT: {filename}
CONTENT PREVIEW: {content[:2000]}

Provide a brief analysis with:
1. Main topic/subject
2. 3-5 key concepts
3. Estimated difficulty (Beginner/Intermediate/Advanced)
4. Exam relevance (High/Medium/Low)

Format as JSON.
"""
            max_tokens = 500
        elif depth == "deep":
            prompt = f"""DEEP ANALYSIS of study document for advanced exam preparation.

DOCUMENT: {filename}
CONTENT: {content[:15000]}

Provide comprehensive analysis with:
1. Subject and sub-topics
2. 5-10 key concepts with explanations
3. Complexity level and why
4. Exam question types this could generate
5. Prerequisite knowledge needed
6. Connections to other topics
7. Study priority (1-10)
8. Common student difficulties
9. Recommended study approach
10. Key formulas/theorems to memorize

Format as JSON.
"""
            max_tokens = 2000
        else:  # standard
            prompt = f"""ANALYSIS of study document for exam preparation.

DOCUMENT: {filename}
CONTENT: {content[:10000]}

Provide analysis with:
1. Main subject
2. Key concepts (5-8)
3. Difficulty level
4. Exam relevance and why
5. Potential exam questions
6. Study priority (1-10)
7. Summary (3-4 sentences)

Format as JSON.
"""
            max_tokens = 1000

        response = self.client.chat.completions.create(
            model=self.config["model"],
            messages=[
                {"role": "system",
                 "content": "You are an expert exam preparation analyst. Analyze study materials accurately."},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            temperature=0.2,  # Low temp for consistent analysis
            max_tokens=max_tokens,
            top_p=0.9
        )

        analysis_text = response.choices[0].message.content

        # Extract JSON from response
        try:
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = analysis_text[start_idx:end_idx]
                analysis = json.loads(json_str)
            else:
                analysis = {"analysis": analysis_text}
        except:
            analysis = {"analysis": analysis_text}

        # Add metadata
        analysis["filename"] = filename
        analysis["analyzed_at"] = datetime.now().isoformat()
        analysis["analysis_depth"] = depth
        analysis["content_preview"] = content[:500] + "..." if len(content) > 500 else content

        return analysis

    def upload_folder(self):
        """Upload entire folder of study materials"""
        print("\n" + "=" * 60)
        print("📂 UPLOAD STUDY FOLDER")
        print("=" * 60)

        folder_path = input("\nEnter full path to folder: ").strip()

        if not folder_path or not os.path.isdir(folder_path):
            print("❌ Invalid folder path")
            return

        print(f"\n🔍 Scanning folder...")

        supported_extensions = ['.pdf', '.docx', '.txt', '.md', '.rtf']
        files_found = []

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in supported_extensions:
                    files_found.append(os.path.join(root, file))

        if not files_found:
            print("❌ No supported files found")
            return

        print(f"\n✅ Found {len(files_found)} files")

        confirm = input(f"\nUpload all {len(files_found)} files? (y/n): ").lower()
        if confirm != 'y':
            return

        print("\n📤 Uploading...")

        uploaded = 0
        for filepath in files_found:
            try:
                filename = os.path.basename(filepath)
                dest_path = os.path.join(self.documents_dir, filename)

                # Handle duplicates
                counter = 1
                while os.path.exists(dest_path):
                    name, ext = os.path.splitext(filename)
                    dest_path = os.path.join(self.documents_dir, f"{name}_{counter}{ext}")
                    counter += 1

                shutil.copy2(filepath, dest_path)

                stat = os.stat(dest_path)
                self.documents[os.path.basename(dest_path)] = {
                    "path": dest_path,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                }

                uploaded += 1
                print(f"  ✅ {filename}")

            except Exception as e:
                print(f"  ❌ Error: {e}")

        print(f"\n🎉 Uploaded {uploaded} files")

        # Ask if user wants to analyze immediately
        if uploaded > 0:
            analyze_now = input("\nAnalyze newly uploaded documents now? (y/n): ").lower()
            if analyze_now == 'y':
                self.analyze_documents()

    def upload_single_document(self):
        """Upload a single document"""
        print("\n" + "=" * 60)
        print("📄 UPLOAD SINGLE DOCUMENT")
        print("=" * 60)

        filepath = input("\nEnter full path to document: ").strip()

        if not filepath or not os.path.exists(filepath):
            print("❌ File not found")
            return

        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()

        supported_extensions = ['.pdf', '.docx', '.txt', '.md', '.rtf']
        if ext not in supported_extensions:
            print(f"❌ Unsupported file type")
            return

        # Handle duplicates
        if filename in self.documents:
            overwrite = input(f"'{filename}' already exists. Overwrite? (y/n): ").lower()
            if overwrite != 'y':
                print("❌ Cancelled")
                return

        dest_path = os.path.join(self.documents_dir, filename)
        try:
            shutil.copy2(filepath, dest_path)

            stat = os.stat(dest_path)
            self.documents[filename] = {
                "path": dest_path,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            }

            print(f"✅ Uploaded: {filename}")

            # Ask for analysis
            analyze_now = input("\nAnalyze this document now? (y/n): ").lower()
            if analyze_now == 'y':
                print(f"\n🔍 Analyzing {filename}...")
                analysis = self._analyze_single_document(filename, "standard")
                self.save_analysis(filename, analysis)
                print(f"✅ Analysis saved")

        except Exception as e:
            print(f"❌ Error: {e}")

    def adjust_parameters(self):
        """Adjust AI parameters"""
        print("\n" + "=" * 60)
        print("⚙️  ADJUST PARAMETERS")
        print("=" * 60)

        while True:
            print(f"\nCurrent parameters:")
            for i, (key, value) in enumerate(self.config.items(), 1):
                print(f"{i}. {key}: {value}")
            print(f"{len(self.config) + 1}. Save and return")

            try:
                choice = input(f"\nSelect parameter (1-{len(self.config) + 1}): ").strip()

                if choice == str(len(self.config) + 1):
                    self.save_config()
                    print("✅ Parameters saved")
                    break

                idx = int(choice) - 1
                if 0 <= idx < len(self.config):
                    key = list(self.config.keys())[idx]
                    current = self.config[key]

                    if key in ["temperature", "top_p", "frequency_penalty", "presence_penalty"]:
                        value = float(input(f"Enter {key} (current: {current}): ").strip() or str(current))
                        if key == "temperature":
                            value = max(0.0, min(2.0, value))
                        elif key in ["top_p"]:
                            value = max(0.0, min(1.0, value))
                        else:
                            value = max(-2.0, min(2.0, value))
                    elif key == "max_tokens":
                        value = int(input(f"Enter {key} (current: {current}): ").strip() or str(current))
                        value = max(1, min(4096, value))
                    else:
                        value = input(f"Enter {key} (current: {current}): ").strip() or current

                    self.config[key] = value
                    print(f"✅ {key} set to: {value}")

            except:
                print("❌ Invalid input")

    def chat_about_material(self):
        """Chat about study material with analysis context"""
        if not self.documents:
            print("\n❌ No documents uploaded")
            return

        print("\n" + "=" * 60)
        print("💬 CHAT WITH ANALYSIS")
        print("=" * 60)

        # Use analysis if available, otherwise just content
        context_parts = []

        for filename in self.documents:
            if filename in self.analyses:
                analysis = self.analyses[filename]
                context_parts.append(f"""
📄 {filename} - ANALYSIS:
Subject: {analysis.get('subject', 'Unknown')}
Key Concepts: {', '.join(analysis.get('key_concepts', ['Unknown'])[:3])}
Difficulty: {analysis.get('difficulty_level', 'Unknown')}
Exam Relevance: {analysis.get('exam_relevance', 'Unknown')}
Summary: {analysis.get('summary', analysis.get('analysis', 'No summary'))[:200]}...
""")
            else:
                content = self._read_file_content(self.documents[filename]["path"], 1000)
                context_parts.append(f"""
📄 {filename} - CONTENT PREVIEW:
{content[:500]}...
""")

        context = "\n".join(context_parts)

        print(f"\n📚 Loaded {len(self.documents)} documents")
        if self.analyses:
            print(f"📊 Using {len(self.analyses)} analyses for context")
        print("\n💡 Ask questions about your study material")
        print("Type 'back' to return\n")

        while True:
            question = input("❓ Your question: ").strip()
            if question.lower() == 'back':
                break

            if not question:
                continue

            prompt = f"""Based on these analyzed study materials:

{context}

QUESTION: {question}

Provide a helpful, accurate answer using the analysis when possible.
"""

            try:
                print("\n🤔 Thinking...", end="", flush=True)

                response = self.client.chat.completions.create(
                    model=self.config["model"],
                    messages=[
                        {"role": "system",
                         "content": "You are a knowledgeable study assistant. Use the provided analyses to give accurate answers."},
                        {"role": "user", "content": prompt}
                    ],
                    stream=False,
                    temperature=self.config["temperature"],
                    max_tokens=self.config["max_tokens"],
                    top_p=self.config["top_p"],
                    frequency_penalty=self.config["frequency_penalty"],
                    presence_penalty=self.config["presence_penalty"]
                )

                answer = response.choices[0].message.content
                print(f"\n💡 {answer}\n")

            except Exception as e:
                print(f"\n❌ Error: {e}")

    def view_analyses(self):
        """View document analyses"""
        if not self.analyses:
            print("\n❌ No analyses available. Analyze documents first.")
            return

        print("\n" + "=" * 60)
        print("📊 DOCUMENT ANALYSES")
        print("=" * 60)

        print(f"\nFound {len(self.analyses)} analyses:")

        for i, (filename, analysis) in enumerate(self.analyses.items(), 1):
            print(f"\n{i}. 📄 {filename}")
            print(f"   Subject: {analysis.get('subject', 'Unknown')}")
            print(f"   Analyzed: {analysis.get('analyzed_at', 'Unknown').split('T')[0]}")
            print(f"   Depth: {analysis.get('analysis_depth', 'Unknown')}")

        print("\nOptions:")
        print("1. View detailed analysis")
        print("2. Back to menu")

        choice = input("\nSelect option (1-2): ").strip()

        if choice == '1':
            try:
                idx = int(input(f"Enter analysis number (1-{len(self.analyses)}): ").strip()) - 1
                if 0 <= idx < len(self.analyses):
                    filename = list(self.analyses.keys())[idx]
                    analysis = self.analyses[filename]

                    print(f"\n" + "=" * 60)
                    print(f"📊 ANALYSIS: {filename}")
                    print("=" * 60)

                    for key, value in analysis.items():
                        if key not in ["filename", "content_preview"]:
                            print(f"\n🔹 {key.upper().replace('_', ' ')}:")
                            if isinstance(value, list):
                                for item in value[:10]:
                                    print(f"   • {item}")
                            else:
                                print(f"   {value}")

                    print("\n" + "=" * 60)
            except:
                print("❌ Invalid selection")

    def _read_file_content(self, filepath: str, max_chars: int = 5000) -> str:
        """Read file content"""
        ext = os.path.splitext(filepath)[1].lower()

        try:
            if ext == '.pdf':
                text = ""
                with open(filepath, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages[:3]:
                        text += page.extract_text() + "\n"
                return text[:max_chars]
            elif ext == '.docx':
                doc = docx.Document(filepath)
                text = "\n".join([para.text for para in doc.paragraphs[:50]])
                return text[:max_chars]
            else:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(max_chars)
        except:
            return ""

    def run(self):
        """Main interactive loop"""
        print("\n" + "=" * 60)
        print("🧠 STUDY ASSISTANT - With Persistent Analysis")
        print("=" * 60)
        print("• Documents & analyses saved between sessions")
        print("• Upload folders or single files")
        print("• Deep document analysis")
        print()

        while True:
            print("\n📋 MAIN MENU:")
            print("1. 💬 Chat about study material (with analysis)")
            print("2. 🔬 Analyze documents")
            print("3. 📂 Upload folder of documents")
            print("4. 📄 Upload single document")
            print("5. 📊 View document analyses")
            print("6. ⚙️  Adjust AI parameters")
            print("7. 🏁 Exit")

            choice = input("\nSelect option (1-7): ").strip()

            if choice == '1':
                self.chat_about_material()
            elif choice == '2':
                self.analyze_documents()
            elif choice == '3':
                self.upload_folder()
            elif choice == '4':
                self.upload_single_document()
            elif choice == '5':
                self.view_analyses()
            elif choice == '6':
                self.adjust_parameters()
            elif choice == '7':
                print("\n👋 Goodbye! All data is saved.")
                break
            else:
                print("❌ Invalid choice")


def main():
    """Main entry point"""
    print("🚀 Starting Study Assistant...")

    try:
        import PyPDF2
        import docx
    except ImportError:
        print("❌ Install: pip install pypdf2 python-docx")
        return

    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ DEEPSEEK_API_KEY not found in .env")
        return

    try:
        assistant = AdvancedStudyAssistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\n\n👋 Session ended.")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()