from typing import List, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings

class EmbeddingsService:
    @staticmethod
    def get_embeddings(
        texts: List[str], 
        api_keys: dict, 
        provider: str = "google"
    ) -> List[List[float]]:
        """
        Generates embeddings for a list of texts dynamically using the user's provided API key.
        """
        if provider == "google":
            if "gemini" not in api_keys:
                raise ValueError("Google Gemini API key is missing from request headers.")
            
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                output_dimensionality=768,
                google_api_key=api_keys["gemini"]
            )
            return embeddings.embed_documents(texts)
            
        elif provider == "openai":
            if "openai" not in api_keys:
                raise ValueError("OpenAI API key is missing from request headers.")
                
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small", 
                openai_api_key=api_keys["openai"]
            )
            return embeddings.embed_documents(texts)
            
        elif provider == "jina":
            if "jina" not in api_keys or not api_keys["jina"]:
                raise ValueError("Jina AI API key is missing.")
            
            import requests
            task = "retrieval.passage" if len(texts) > 1 else "retrieval.query"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_keys['jina']}"
            }
            data = {
                "model": "jina-embeddings-v3",
                "task": task,
                "dimensions": 768,
                "embedding_type": "float",
                "input": texts
            }
            response = requests.post("https://api.jina.ai/v1/embeddings", json=data, headers=headers)
            if response.status_code != 200:
                raise ValueError(f"Jina AI Embeddings API call failed ({response.status_code}): {response.text}")
            
            res_json = response.json()
            return [item["embedding"] for item in res_json["data"]]
            
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
