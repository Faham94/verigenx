"""
SpecMind: Semantic Chunker
Splits specification text into semantically coherent chunks
"""
import re
from typing import List, Dict

class Chunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_document(self, text: str, metadata: Dict = None) -> List[Dict]:
        if metadata is None:
            metadata = {}
        
        sections = re.split(r'\n(?=#{1,3}\s|Section\s+\d+\.\d+|\d+\.\s+[A-Z])', text)
        
        chunks = []
        for i, section in enumerate(sections):
            if not section.strip():
                continue
            
            section_words = section.split()
            if len(section_words) > self.chunk_size * 1.5:
                sub_chunks = self._split_long_section(section)
                for j, sub in enumerate(sub_chunks):
                    chunks.append({
                        "text": sub,
                        "chunk_index": f"{i}_{j}",
                        "section": f"Section {i+1}",
                        "metadata": metadata
                    })
            else:
                chunks.append({
                    "text": section,
                    "chunk_index": str(i),
                    "section": f"Section {i+1}",
                    "metadata": metadata
                })
        
        return chunks
    
    def _split_long_section(self, text: str) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_text = " ".join(words[i:i + self.chunk_size])
            if chunk_text.strip():
                chunks.append(chunk_text)
        return chunks
