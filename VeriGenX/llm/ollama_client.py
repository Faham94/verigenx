"""
Ollama Client for VeriGenX
Handles all LLM interactions with local Ollama models
"""
import requests
import time
import json
from typing import Optional, List, Dict, Any
from VeriGenX.config import OLLAMA_BASE_URL, DEEPSEEK_MODEL, EMBEDDING_MODEL

class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.available_models = []
        self._check_connection()
    
    def _check_connection(self):
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.available_models = [m["name"] for m in data.get("models", [])]
                print(f"Ollama connected. Models: {self.available_models}")
            else:
                print("Warning: Ollama not responding")
        except Exception as e:
            print(f"Warning: Cannot connect to Ollama: {e}")
    
    def generate(self, prompt: str, model: str = DEEPSEEK_MODEL,
                 temperature: float = 0.3, max_tokens: int = 4096) -> str:
        if model not in self.available_models:
            model = self.available_models[0] if self.available_models else DEEPSEEK_MODEL
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens}
        }
        
        try:
            start = time.time()
            response = self.session.post(f"{self.base_url}/api/generate", json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            print(f"Generated in {time.time()-start:.2f}s")
            return result.get("response", "")
        except Exception as e:
            print(f"Generation failed: {e}")
            return ""
    
    def embed(self, text: str) -> List[float]:
        try:
            response = self.session.post(
                f"{self.base_url}/api/embeddings",
                json={"model": EMBEDDING_MODEL, "prompt": text},
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("embedding", [])
        except Exception as e:
            print(f"Embedding failed: {e}")
            return []
    
    def is_available(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

_client = None

def get_ollama_client() -> OllamaClient:
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client
