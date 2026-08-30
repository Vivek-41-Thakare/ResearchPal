import os
import requests
import dotenv

dotenv.load_dotenv()

BASE_URL = "http://127.0.0.1:8000"
# Use the document ID we just successfully indexed
DOC_ID = "d9f64188-140b-4374-868a-0ee629dd888c"

def run_test():
    headers = {
        "Content-Type": "application/json",
        "X-Gemini-API-Key": os.getenv("GEMINI_API_KEY") or os.getenv("gemini_api_key") or "",
        "X-Jina-API-Key": os.getenv("JINA_API_KEY") or os.getenv("jina_api_key") or ""
    }
    
    print(f"💬 Chatting with existing document `{DOC_ID}`...")
    chat_payload = {
        "query": "What is the main topic of this brief note? Be brief.",
        "document_id": DOC_ID,
        "chat_history": []
    }
    
    chat_res = requests.post(f"{BASE_URL}/api/chat", json=chat_payload, headers=headers, stream=True)
    if chat_res.status_code != 200:
        print(f"❌ Chat request failed: {chat_res.text}")
        return
        
    print("🤖 Agent Streamed Response:\n")
    for chunk in chat_res.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            print(chunk, end="", flush=True)
    print("\n\n✅ End of response.")

if __name__ == "__main__":
    run_test()
