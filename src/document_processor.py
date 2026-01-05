import os
import PyPDF2
import docx
import markdown
from typing import List, Dict
import chromadb
from sentence_transformers import SentenceTransformer
import hashlib


class DocumentProcessor:
    """Process study documents for ingestion"""

    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.create_collection(name="study_documents")

    def load_document(self, filepath: str) -> str:
        """Load document based on file type"""
        ext = os.path.splitext(filepath)[1].lower()

        if ext == '.pdf':
            return self._read_pdf(filepath)
        elif ext == '.docx':
            return self._read_docx(filepath)
        elif ext == '.txt':
            return self._read_txt(filepath)
        elif ext == '.md':
            return self._read_markdown(filepath)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _read_pdf(self, filepath: str) -> str:
        """Read PDF file"""
        text = ""
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

    def _read_docx(self, filepath: str) -> str:
        """Read DOCX file"""
        doc = docx.Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])

    def _read_txt(self, filepath: str) -> str:
        """Read text file"""
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()

    def _read_markdown(self, filepath: str) -> str:
        """Read markdown file"""
        with open(filepath, 'r', encoding='utf-8') as file:
            md_content = file.read()
            return markdown.markdown(md_content)

    def chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into manageable chunks"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0

        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1

            if current_size >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def index_document(self, filepath: str, metadata: Dict = None):
        """Index document for semantic search"""
        text = self.load_document(filepath)
        chunks = self.chunk_text(text)

        documents = []
        embeddings = []
        metadatas = []
        ids = []

        for i, chunk in enumerate(chunks):
            doc_id = hashlib.md5(f"{filepath}_{i}".encode()).hexdigest()
            embedding = self.model.encode(chunk).tolist()

            documents.append(chunk)
            embeddings.append(embedding)
            metadatas.append({
                "filepath": filepath,
                "chunk_index": i,
                "total_chunks": len(chunks),
                **(metadata or {})
            })
            ids.append(doc_id)

        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        return len(chunks)

    def search_documents(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search documents semantically"""
        query_embedding = self.model.encode(query).tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return [
            {
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            }
            for i in range(len(results["documents"][0]))
        ]