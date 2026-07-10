"""
Document Ingestion for SpecMind
Supports TXT, PDF, and DOCX files
"""
import os
from pathlib import Path

class DocumentIngestor:
    def ingest(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = Path(file_path).suffix.lower()
        
        if ext == '.txt':
            return self._ingest_txt(file_path)
        elif ext == '.pdf':
            return self._ingest_pdf(file_path)
        elif ext == '.docx':
            return self._ingest_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _ingest_txt(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return {"text": text, "file_type": "txt", "metadata": {"title": os.path.basename(file_path)}}
    
    def _ingest_pdf(self, file_path):
        try:
            import fitz
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return {"text": text, "file_type": "pdf", "metadata": {"title": os.path.basename(file_path), "pages": len(doc)}}
        except ImportError:
            print("PyMuPDF not installed. Install with: pip install PyMuPDF")
            raise
    
    def _ingest_docx(self, file_path):
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            return {"text": text, "file_type": "docx", "metadata": {"title": os.path.basename(file_path)}}
        except ImportError:
            print("python-docx not installed. Install with: pip install python-docx")
            raise
