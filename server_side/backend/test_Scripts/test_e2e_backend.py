import os
import time
import requests
import dotenv
from services.supabase_service import SupabaseService

dotenv.load_dotenv()

BASE_URL = "http://127.0.0.1:8000"

def run_test():
    # 1. Fetch trending papers
    print("📈 Step 1: Fetching trending papers from `/api/papers/trending`...")
    res = requests.get(f"{BASE_URL}/api/papers/trending?page=1&items=3")
    if res.status_code != 200:
        print(f"❌ Failed to fetch papers: {res.text}")
        return
    
    data = res.json()
    results = data.get("results", [])
    if not results:
        print("❌ No trending papers returned.")
        return
        
    paper_info = results[0].get("paper", {})
    title = paper_info.get("title")
    pdf_url = paper_info.get("url_pdf")
    
    # Use abstract URL format to test arXiv URL auto-rewriting
    test_url = pdf_url
    if "arxiv.org/pdf/" in pdf_url:
        test_url = pdf_url.replace("arxiv.org/pdf/", "arxiv.org/abs/")
        
    print(f"✅ Found paper: '{title}'")
    print(f"🔗 ArXiv Abstract Link (Testing rewrite): {test_url}")
    
    # 2. Ingest the paper
    print(f"\n🚀 Step 2: Requesting ingestion/parsing for '{title}'...")
    headers = {
        "Content-Type": "application/json",
        "X-Gemini-API-Key": os.getenv("GEMINI_API_KEY") or os.getenv("gemini_api_key") or "",
        "X-Jina-API-Key": os.getenv("JINA_API_KEY") or os.getenv("jina_api_key") or ""
    }
    payload = {
        "url": test_url,
        "filename": "document.pdf"
    }
    
    parse_res = requests.post(f"{BASE_URL}/api/parse_url", json=payload, headers=headers)
    if parse_res.status_code != 200:
        print(f"❌ Ingestion request failed: {parse_res.text}")
        return
        
    parse_data = parse_res.json()
    saved_filename = parse_data["filename"]
    print(f"✅ Ingestion queued! Filename: {saved_filename}")
    
    # 3. Poll document ID & chunk count
    print(f"\n⏳ Step 3: Polling Supabase for '{saved_filename}' to complete indexing...")
    db = SupabaseService()
    
    doc_id = None
    # Wait for the document row to be inserted first
    for attempt in range(15):
        docs_res = requests.get(f"{BASE_URL}/api/documents")
        if docs_res.status_code == 200:
            docs = docs_res.json()
            for doc in docs:
                if doc["paper_url"] == saved_filename:
                    doc_id = doc["id"]
                    break
        if doc_id:
            break
        print("Waiting for document row registration...")
        time.sleep(2)
        
    if not doc_id:
        print("❌ Timeout waiting for document registration.")
        return
        
    print(f"✅ Document registered with ID: {doc_id}")
    
    # Now poll the chunk count
    chunks_count = 0
    start_time = time.time()
    while chunks_count == 0:
        elapsed = time.time() - start_time
        if elapsed > 120:  # 2 minutes timeout
            print("❌ Timeout waiting for chunk generation.")
            return
            
        chunks_res = db.client.table("document_chunks").select("id").eq("document_id", doc_id).execute()
        chunks_count = len(chunks_res.data)
        print(f"   [Polling] Chunks count: {chunks_count} (Elapsed: {int(elapsed)}s)...")
        if chunks_count == 0:
            time.sleep(5)
            
    print(f"🎉 Indexing complete! Total chunks created: {chunks_count}")
    
    # 4. Chat with the paper
    print(f"\n💬 Step 4: Chatting with the document `{doc_id}`...")
    chat_payload = {
        "query": "What is the main contribution or core theme of this paper? Keep it under 2 sentences.",
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
