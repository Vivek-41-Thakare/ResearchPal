import os
import time
import requests
import dotenv
from services.supabase_service import SupabaseService

dotenv.load_dotenv()

BASE_URL = "http://127.0.0.1:8000"

def run_test():
    test_url = "https://arxiv.org/abs/2108.00001"
    print(f"🔗 Target ArXiv Link: {test_url}")
    
    # Ingest
    print(f"\n🚀 Step 1: Requesting ingestion/parsing...")
    headers = {
        "Content-Type": "application/json",
        "X-Gemini-API-Key": os.getenv("GEMINI_API_KEY") or os.getenv("gemini_api_key") or "",
        "X-Jina-API-Key": os.getenv("JINA_API_KEY") or os.getenv("jina_api_key") or ""
    }
    payload = {
        "url": test_url,
        "filename": "arxiv_2108.00001_final.pdf"
    }
    
    parse_res = requests.post(f"{BASE_URL}/api/parse_url", json=payload, headers=headers)
    if parse_res.status_code != 200:
        print(f"❌ Ingestion request failed: {parse_res.text}")
        return
        
    parse_data = parse_res.json()
    saved_filename = parse_data["filename"]
    print(f"✅ Ingestion queued! Filename: {saved_filename}")
    
    # Poll document ID & metadata
    print(f"\n⏳ Step 2: Polling database for document registration...")
    db = SupabaseService()
    
    doc_id = None
    doc_row = None
    for attempt in range(15):
        docs_res = requests.get(f"{BASE_URL}/api/documents")
        if docs_res.status_code == 200:
            docs = docs_res.json()
            for doc in docs:
                if doc["paper_url"] == test_url:  # Match on the source URL now!
                    doc_id = doc["id"]
                    doc_row = doc
                    break
        if doc_id:
            break
        print("Waiting for document row registration...")
        time.sleep(2)
        
    if not doc_id:
        print("❌ Timeout waiting for document registration. (Make sure paper_url matches source URL)")
        return
        
    print(f"🎉 Document Registered!")
    print(f"   Stored ID: {doc_row['id']}")
    print(f"   Stored Title: '{doc_row['paper_title']}'")
    print(f"   Stored URL: '{doc_row['paper_url']}'")
    
    # Now poll the chunk count
    chunks_count = 0
    start_time = time.time()
    while chunks_count == 0:
        elapsed = time.time() - start_time
        if elapsed > 45:
            print("❌ Timeout waiting for chunk generation.")
            return
            
        chunks_res = db.client.table("document_chunks").select("id").eq("document_id", doc_id).execute()
        chunks_count = len(chunks_res.data)
        print(f"   [Polling] Chunks count: {chunks_count} (Elapsed: {int(elapsed)}s)...")
        if chunks_count == 0:
            time.sleep(2)
            
    print(f"🎉 Indexing complete! Total chunks: {chunks_count}")
    
    # Chat with the paper
    print(f"\n💬 Step 3: Chatting with the document `{doc_id}`...")
    chat_payload = {
        "query": "What construction is presented in this note? Be very brief.",
        "document_id": doc_id,
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
