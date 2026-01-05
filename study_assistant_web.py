#!/usr/bin/env python3
"""
STUDY ASSISTANT WEB INTERFACE - Beautiful GUI
"""
import streamlit as st
import os
import json

try:
    import PyPDF2
except ImportError:
    import pypdf as PyPDF2
import docx
import shutil
from datetime import datetime
from typing import Dict
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize session state
if 'documents' not in st.session_state:
    st.session_state.documents = {}
if 'analyses' not in st.session_state:
    st.session_state.analyses = {}
if 'config' not in st.session_state:
    st.session_state.config = {
        "temperature": 0.3,
        "max_tokens": 1500,
        "top_p": 0.95,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.0,
        "model": "deepseek-chat"
    }


class WebStudyAssistant:
    def __init__(self):
        # Check Streamlit secrets first, then environment variable
        if hasattr(st, 'secrets') and 'DEEPSEEK_API_KEY' in st.secrets:
            api_key = st.secrets['DEEPSEEK_API_KEY']
        else:
            api_key = os.getenv("DEEPSEEK_API_KEY")

        if not api_key:
            st.error("❌ DEEPSEEK_API_KEY not found")
            st.info("""
            **How to fix:**
            1. **Streamlit Cloud:** Go to App Settings → Secrets → Add DEEPSEEK_API_KEY
            2. **Local:** Create `.env` file with DEEPSEEK_API_KEY=your_key
            """)
            st.stop()

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            default_headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

        self.base_dir = "advanced_study_data"
        self.documents_dir = os.path.join(self.base_dir, "documents")
        self.analysis_dir = os.path.join(self.base_dir, "analysis")

        for dir_path in [self.base_dir, self.documents_dir, self.analysis_dir]:
            os.makedirs(dir_path, exist_ok=True)

        self.load_data()

    def load_data(self):
        """Load documents and analyses"""
        # Load documents
        supported_extensions = ['.pdf', '.docx', '.txt', '.md', '.rtf']
        for filename in os.listdir(self.documents_dir):
            ext = os.path.splitext(filename)[1].lower()
            if ext in supported_extensions:
                filepath = os.path.join(self.documents_dir, filename)
                stat = os.stat(filepath)
                st.session_state.documents[filename] = {
                    "path": filepath,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                }

        # Load analyses
        for filename in os.listdir(self.analysis_dir):
            if filename.endswith('_analysis.json'):
                doc_name = filename.replace('_analysis.json', '')
                filepath = os.path.join(self.analysis_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        st.session_state.analyses[doc_name] = json.load(f)
                except:
                    pass

    def save_analysis(self, filename: str, analysis: Dict):
        """Save analysis to file"""
        analysis_file = os.path.join(self.analysis_dir, f"{filename}_analysis.json")
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        st.session_state.analyses[filename] = analysis

    def read_file_content(self, filepath: str, max_chars: int = 5000) -> str:
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
                return "\n".join([para.text for para in doc.paragraphs[:50]])[:max_chars]
            else:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(max_chars)
        except:
            return ""

    def analyze_document(self, filename: str, progress_bar=None):
        """Analyze a single document"""
        filepath = st.session_state.documents[filename]["path"]
        content = self.read_file_content(filepath, 10000)

        if not content:
            return {"error": "Could not read file"}

        prompt = f"""ANALYSIS of study document for exam preparation.

DOCUMENT: {filename}
CONTENT: {content[:8000]}

Provide analysis with:
1. Main subject
2. Key concepts (5-8)
3. Difficulty level (Beginner/Intermediate/Advanced)
4. Exam relevance (High/Medium/Low) and why
5. Potential exam questions
6. Study priority (1-10)
7. Summary (3-4 sentences)

Format as JSON.
"""

        try:
            if progress_bar:
                progress_bar.progress(50)

            response = self.client.chat.completions.create(
                model=st.session_state.config["model"],
                messages=[
                    {"role": "system", "content": "You are an expert exam preparation analyst."},
                    {"role": "user", "content": prompt}
                ],
                stream=False,
                temperature=0.2,
                max_tokens=1000
            )

            if progress_bar:
                progress_bar.progress(80)

            analysis_text = response.choices[0].message.content

            # Extract JSON
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

            analysis["filename"] = filename
            analysis["analyzed_at"] = datetime.now().isoformat()

            self.save_analysis(filename, analysis)

            if progress_bar:
                progress_bar.progress(100)

            return analysis

        except Exception as e:
            return {"error": str(e)}


def main():
    # Page config
    st.set_page_config(
        page_title="Study Assistant",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3B82F6;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #D1FAE5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10B981;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #DBEAFE;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3B82F6;
        margin: 1rem 0;
    }
    .document-card {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #6B7280;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-header">🧠 Advanced Study Assistant</h1>', unsafe_allow_html=True)

    # Initialize assistant
    assistant = WebStudyAssistant()

    # Sidebar for navigation
    with st.sidebar:
        st.markdown("### 📋 Navigation")
        page = st.radio(
            "Go to:",
            ["🏠 Dashboard", "📂 Upload Documents", "🔬 Analyze", "💬 Chat", "⚙️ Settings"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### 📊 Statistics")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", len(st.session_state.documents))
        with col2:
            st.metric("Analyses", len(st.session_state.analyses))

        if st.session_state.documents:
            st.markdown("---")
            st.markdown("### 📄 Documents")
            for filename in list(st.session_state.documents.keys())[:5]:
                st.caption(f"• {filename}")

    # Dashboard Page
    if page == "🏠 Dashboard":
        st.markdown('<h2 class="sub-header">📊 Dashboard</h2>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📚 Documents", len(st.session_state.documents))
        with col2:
            st.metric("🔬 Analyses", len(st.session_state.analyses))
        with col3:
            analyzed_pct = (len(st.session_state.analyses) / max(len(st.session_state.documents), 1)) * 100
            st.metric("📈 Analyzed", f"{analyzed_pct:.0f}%")

        # Quick Actions
        st.markdown('<h3 class="sub-header">⚡ Quick Actions</h3>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📤 Upload Documents", use_container_width=True):
                st.switch_page("📂 Upload Documents")
        with col2:
            if st.button("🔬 Analyze All", use_container_width=True):
                st.switch_page("🔬 Analyze")
        with col3:
            if st.button("💬 Start Chat", use_container_width=True, disabled=not st.session_state.documents):
                st.switch_page("💬 Chat")

        # Recent Documents
        if st.session_state.documents:
            st.markdown('<h3 class="sub-header">📄 Recent Documents</h3>', unsafe_allow_html=True)

            for i, (filename, doc_info) in enumerate(list(st.session_state.documents.items())[:3]):
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{filename}**")
                        st.caption(f"Size: {doc_info['size']:,} bytes")
                    with col2:
                        analyzed = "✅" if filename in st.session_state.analyses else "❌"
                        st.write(f"Analyzed: {analyzed}")
                    st.divider()

        # Recent Analyses
        if st.session_state.analyses:
            st.markdown('<h3 class="sub-header">📊 Recent Analyses</h3>', unsafe_allow_html=True)

            for i, (filename, analysis) in enumerate(list(st.session_state.analyses.items())[:3]):
                with st.expander(f"🔬 {filename}"):
                    if "subject" in analysis:
                        st.write(f"**Subject:** {analysis['subject']}")
                    if "key_concepts" in analysis:
                        st.write("**Key Concepts:**")
                        for concept in analysis['key_concepts'][:3]:
                            st.write(f"• {concept}")
                    if "exam_relevance" in analysis:
                        st.write(f"**Exam Relevance:** {analysis['exam_relevance']}")

    # Upload Documents Page
    elif page == "📂 Upload Documents":
        st.markdown('<h2 class="sub-header">📂 Upload Documents</h2>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["📁 Upload Folder", "📄 Upload Single File"])

        with tab1:
            st.markdown("### Upload Entire Folder")
            st.info("Upload all PDF, DOCX, TXT, MD, RTF files from a folder")

            folder_path = st.text_input("Folder path:", placeholder="/Users/name/Documents/StudyMaterials/")

            if st.button("📤 Scan and Upload Folder", type="primary"):
                if folder_path and os.path.isdir(folder_path):
                    with st.spinner("🔍 Scanning folder..."):
                        supported_extensions = ['.pdf', '.docx', '.txt', '.md', '.rtf']
                        files_found = []

                        for root, dirs, files in os.walk(folder_path):
                            for file in files:
                                ext = os.path.splitext(file)[1].lower()
                                if ext in supported_extensions:
                                    files_found.append(os.path.join(root, file))

                        if files_found:
                            st.success(f"✅ Found {len(files_found)} files")

                            progress_bar = st.progress(0)
                            uploaded = 0

                            for i, filepath in enumerate(files_found):
                                try:
                                    filename = os.path.basename(filepath)
                                    dest_path = os.path.join(assistant.documents_dir, filename)

                                    # Handle duplicates
                                    counter = 1
                                    while os.path.exists(dest_path):
                                        name, ext = os.path.splitext(filename)
                                        dest_path = os.path.join(assistant.documents_dir, f"{name}_{counter}{ext}")
                                        counter += 1

                                    shutil.copy2(filepath, dest_path)
                                    stat = os.stat(dest_path)
                                    st.session_state.documents[os.path.basename(dest_path)] = {
                                        "path": dest_path,
                                        "size": stat.st_size,
                                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                                    }
                                    uploaded += 1

                                except Exception as e:
                                    st.error(f"❌ Error with {os.path.basename(filepath)}: {e}")

                                progress_bar.progress((i + 1) / len(files_found))

                            st.success(f"🎉 Successfully uploaded {uploaded} files")
                            st.rerun()
                        else:
                            st.warning("⚠️ No supported files found in folder")
                else:
                    st.error("❌ Please enter a valid folder path")

        with tab2:
            st.markdown("### Upload Single File")
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['pdf', 'docx', '.txt', '.md', '.rtf'],
                label_visibility="collapsed"
            )

            if uploaded_file is not None:
                # Display file info
                st.info(f"**File:** {uploaded_file.name} | **Size:** {uploaded_file.size:,} bytes")

                if st.button("💾 Save File", type="primary"):
                    dest_path = os.path.join(assistant.documents_dir, uploaded_file.name)

                    # Handle duplicates
                    counter = 1
                    while os.path.exists(dest_path):
                        name, ext = os.path.splitext(uploaded_file.name)
                        dest_path = os.path.join(assistant.documents_dir, f"{name}_{counter}{ext}")
                        counter += 1

                    # Save file
                    with open(dest_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    stat = os.stat(dest_path)
                    st.session_state.documents[os.path.basename(dest_path)] = {
                        "path": dest_path,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                    }

                    st.success(f"✅ File saved as: {os.path.basename(dest_path)}")
                    st.rerun()

        # Show uploaded files
        if st.session_state.documents:
            st.markdown("---")
            st.markdown("### 📚 Uploaded Files")

            for filename, doc_info in st.session_state.documents.items():
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{filename}**")
                    with col2:
                        st.write(f"{doc_info['size']:,} bytes")
                    with col3:
                        analyzed = "✅ Analyzed" if filename in st.session_state.analyses else "❌ Not analyzed"
                        st.write(analyzed)
                    st.divider()

    # Analyze Page
    elif page == "🔬 Analyze":
        st.markdown('<h2 class="sub-header">🔬 Analyze Documents</h2>', unsafe_allow_html=True)

        if not st.session_state.documents:
            st.warning("📭 No documents uploaded yet. Please upload documents first.")
            st.page_link("📂 Upload Documents", label="Go to Upload Page")
        else:
            # Find unanalyzed documents
            unanalyzed = [f for f in st.session_state.documents if f not in st.session_state.analyses]
            analyzed = [f for f in st.session_state.documents if f in st.session_state.analyses]

            col1, col2 = st.columns(2)
            with col1:
                st.metric("📝 To Analyze", len(unanalyzed))
            with col2:
                st.metric("✅ Analyzed", len(analyzed))

            if unanalyzed:
                st.markdown("### 📋 Documents Needing Analysis")

                selected_files = st.multiselect(
                    "Select documents to analyze:",
                    options=unanalyzed,
                    default=unanalyzed[:3] if len(unanalyzed) > 3 else unanalyzed
                )

                if selected_files and st.button("🚀 Start Analysis", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for i, filename in enumerate(selected_files):
                        status_text.text(f"Analyzing: {filename} ({i + 1}/{len(selected_files)})")

                        result = assistant.analyze_document(filename, progress_bar)

                        if "error" in result:
                            st.error(f"❌ Error analyzing {filename}: {result['error']}")
                        else:
                            st.success(f"✅ Analyzed: {filename}")

                        progress_bar.progress((i + 1) / len(selected_files))

                    status_text.text("✅ Analysis complete!")
                    st.rerun()

            # Show existing analyses
            if analyzed:
                st.markdown("---")
                st.markdown("### 📊 Existing Analyses")

                for filename in analyzed:
                    with st.expander(f"🔬 {filename}", expanded=False):
                        analysis = st.session_state.analyses[filename]

                        col1, col2 = st.columns(2)
                        with col1:
                            if "subject" in analysis:
                                st.info(f"**Subject:** {analysis['subject']}")
                            if "difficulty_level" in analysis:
                                st.info(f"**Difficulty:** {analysis['difficulty_level']}")
                        with col2:
                            if "exam_relevance" in analysis:
                                relevance_color = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
                                color = relevance_color.get(analysis['exam_relevance'], "⚪")
                                st.info(f"**Exam Relevance:** {color} {analysis['exam_relevance']}")
                            if "study_priority" in analysis:
                                st.info(f"**Priority:** {analysis['study_priority']}/10")

                        if "key_concepts" in analysis:
                            st.markdown("**Key Concepts:**")
                            cols = st.columns(3)
                            for i, concept in enumerate(analysis['key_concepts'][:6]):
                                with cols[i % 3]:
                                    st.markdown(f"• {concept}")

                        if st.button(f"🗑️ Delete Analysis", key=f"delete_{filename}", type="secondary"):
                            analysis_file = os.path.join(assistant.analysis_dir, f"{filename}_analysis.json")
                            if os.path.exists(analysis_file):
                                os.remove(analysis_file)
                            del st.session_state.analyses[filename]
                            st.rerun()

    # Chat Page
    elif page == "💬 Chat":
        st.markdown('<h2 class="sub-header">💬 Chat with Study Assistant</h2>', unsafe_allow_html=True)

        if not st.session_state.documents:
            st.warning("📭 No documents uploaded. Please upload documents first.")
            st.page_link("📂 Upload Documents", label="Go to Upload Page")
        else:
            # Chat interface
            st.info(f"💡 Ask questions about your {len(st.session_state.documents)} documents")

            # Initialize chat history
            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Display chat messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Chat input
            if prompt := st.chat_input("Ask about your study materials..."):
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Prepare context from analyses
                context_parts = []
                for filename in st.session_state.documents:
                    if filename in st.session_state.analyses:
                        analysis = st.session_state.analyses[filename]
                        # FIXED: Added str() conversion to handle None values before slicing
                        summary_content = str(analysis.get('summary', analysis.get('analysis', 'No summary')))[:200]

                        context_parts.append(f"""
📄 {filename}:
Subject: {analysis.get('subject', 'Unknown')}
Key Concepts: {', '.join(analysis.get('key_concepts', ['Unknown'])[:3])}
Difficulty: {analysis.get('difficulty_level', 'Unknown')}
Summary: {summary_content}...
""")
                    else:
                        content = assistant.read_file_content(st.session_state.documents[filename]["path"], 1000)
                        context_parts.append(f"""
📄 {filename}:
Content Preview: {content[:500]}...
""")

                context = "\n".join(context_parts)

                # Generate response
                with st.chat_message("assistant"):
                    with st.spinner("🤔 Thinking..."):
                        try:
                            response = assistant.client.chat.completions.create(
                                model=st.session_state.config["model"],
                                messages=[
                                    {"role": "system",
                                     "content": "You are a helpful study assistant. Use the provided document analyses to give accurate, detailed answers."},
                                    *[{"role": m["role"], "content": m["content"]} for m in
                                      st.session_state.messages[-6:]],
                                    {"role": "user",
                                     "content": f"Study Materials Context:\n{context}\n\nQuestion: {prompt}"}
                                ],
                                stream=False,
                                temperature=st.session_state.config["temperature"],
                                max_tokens=st.session_state.config["max_tokens"],
                                top_p=st.session_state.config["top_p"],
                                frequency_penalty=st.session_state.config["frequency_penalty"],
                                presence_penalty=st.session_state.config["presence_penalty"]
                            )

                            answer = response.choices[0].message.content
                            st.markdown(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})

                        except Exception as e:
                            st.error(f"❌ Error: {e}")

            # Clear chat button
            if st.session_state.messages:
                if st.button("🗑️ Clear Chat History", type="secondary"):
                    st.session_state.messages = []
                    st.rerun()

    # Settings Page
    elif page == "⚙️ Settings":
        st.markdown('<h2 class="sub-header">⚙️ Settings</h2>', unsafe_allow_html=True)

        st.markdown("### 🤖 AI Parameters")

        col1, col2 = st.columns(2)

        with col1:
            st.session_state.config["temperature"] = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=st.session_state.config["temperature"],
                help="Higher = more creative, Lower = more focused"
            )

            st.session_state.config["max_tokens"] = st.slider(
                "Max Tokens",
                min_value=100,
                max_value=4000,
                value=st.session_state.config["max_tokens"],
                step=100,
                help="Maximum response length"
            )

        with col2:
            st.session_state.config["top_p"] = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.config["top_p"],
                help="Controls diversity of responses"
            )

            st.session_state.config["frequency_penalty"] = st.slider(
                "Frequency Penalty",
                min_value=-2.0,
                max_value=2.0,
                value=st.session_state.config["frequency_penalty"],
                help="Reduce repetition (-2 to 2)"
            )

            st.session_state.config["presence_penalty"] = st.slider(
                "Presence Penalty",
                min_value=-2.0,
                max_value=2.0,
                value=st.session_state.config["presence_penalty"],
                help="Encourage new topics (-2 to 2)"
            )

        if st.button("💾 Save Settings", type="primary"):
            # Save to file
            config_file = os.path.join(assistant.base_dir, "config.json")
            with open(config_file, 'w') as f:
                json.dump(st.session_state.config, f, indent=2)
            st.success("✅ Settings saved!")

        st.markdown("---")
        st.markdown("### 🗑️ Data Management")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Clear All Analyses", type="secondary"):
                for filename in list(st.session_state.analyses.keys()):
                    analysis_file = os.path.join(assistant.analysis_dir, f"{filename}_analysis.json")
                    if os.path.exists(analysis_file):
                        os.remove(analysis_file)
                st.session_state.analyses = {}
                st.success("✅ All analyses cleared")
                st.rerun()

        with col2:
            if st.button("🗑️ Clear All Documents", type="secondary"):
                for filename in list(st.session_state.documents.keys()):
                    filepath = os.path.join(assistant.documents_dir, filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                st.session_state.documents = {}
                st.session_state.analyses = {}
                st.success("✅ All documents cleared")
                st.rerun()


if __name__ == "__main__":
    main()