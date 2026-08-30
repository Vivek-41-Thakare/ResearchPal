import os
from typing import List, Dict, Any, Optional, Union
from supabase import create_client, Client

class SupabaseService:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set.")
        self.client: Client = create_client(self.url, self.key)

    def insert_document(self, paper_title: str, paper_url: str, pdf_path: Optional[str] = None) -> str:
        """
        Inserts a new document record and returns its UUID.
        """
        data = {
            "paper_title": paper_title,
            "paper_url": paper_url,
            "pdf_path": pdf_path
        }
        response = self.client.table("documents").insert(data).execute()
        if not response.data:
            raise Exception("Failed to insert document into Supabase.")
        return response.data[0]["id"]

    def insert_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Batch inserts document chunks into the database.
        """
        response = self.client.table("document_chunks").insert(chunks).execute()
        return response.data

    def similarity_search(self, document_ids: Union[str, List[str]], query_embedding: List[float], match_count: int = 10) -> List[Dict[str, Any]]:
        """
        Performs a semantic similarity vector search on document chunks across one or multiple document IDs.
        """
        if isinstance(document_ids, str):
            if "," in document_ids:
                document_ids = [d.strip() for d in document_ids.split(",") if d.strip()]
            else:
                document_ids = [document_ids.strip()] if document_ids.strip() else []
        else:
            document_ids = [str(d).strip() for d in document_ids if str(d).strip()]
            
        # Format the list of UUIDs into standard PostgreSQL array literal format: '{uuid1,uuid2}'
        # If the list is empty, pass None so the RPC matches all documents.
        pg_array = f"{{{','.join(document_ids)}}}" if document_ids else None

        params = {
            "query_embedding": query_embedding,
            "match_threshold": 0.05, # similarity threshold optimized for Jina AI / asymmetric search
            "match_count": match_count,
            "filter_document_ids": pg_array
        }
        response = self.client.rpc("match_chunks_v2", params).execute()
        return response.data or []

    def hybrid_search(self, document_ids: Union[str, List[str]], query_text: str, query_embedding: List[float], match_count: int = 10) -> List[Dict[str, Any]]:
        """
        Performs a hybrid search combining vector similarity search and keyword search across one or multiple documents,
        merging them using Reciprocal Rank Fusion (RRF).
        """
        if isinstance(document_ids, str):
            if "," in document_ids:
                document_ids = [d.strip() for d in document_ids.split(",") if d.strip()]
            else:
                document_ids = [document_ids.strip()] if document_ids.strip() else []
        else:
            document_ids = [str(d).strip() for d in document_ids if str(d).strip()]

        # 1. Vector similarity search (fetch 2x match_count candidates)
        vector_results = self.similarity_search(document_ids, query_embedding, match_count=match_count * 2)
        
        # 2. Keyword/Full-Text Search
        keywords = [w.strip() for w in query_text.split() if len(w.strip()) > 2]
        keyword_results = []
        if keywords:
            try:
                # Query all chunk contents for these documents
                db_res = self.client.table("document_chunks").select("id, document_id, content, page_number, chunk_type, image_path").in_("document_id", document_ids).execute()
                all_chunks = db_res.data or []
                
                # Simple keyword match frequency score
                scored_chunks = []
                for chunk in all_chunks:
                    score = 0
                    content_lower = chunk.get("content", "").lower()
                    for kw in keywords:
                        if kw.lower() in content_lower:
                            score += content_lower.count(kw.lower())
                    if score > 0:
                        scored_chunks.append((chunk, score))
                
                # Sort by frequency descending and take top candidates
                scored_chunks.sort(key=lambda x: x[1], reverse=True)
                keyword_results = [item[0] for item in scored_chunks[:match_count * 2]]
            except Exception as e:
                print(f"⚠️ Keyword search failed: {str(e)}")
                
        # 3. Merge results using Reciprocal Rank Fusion (RRF)
        # RRF Score = 1 / (60 + Rank_vector) + 1 / (60 + Rank_keyword)
        rrf_scores = {}
        chunk_map = {}
        
        for rank, chunk in enumerate(vector_results):
            cid = chunk["id"]
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (60.0 + rank + 1))
            
        for rank, chunk in enumerate(keyword_results):
            cid = chunk["id"]
            chunk_map[cid] = chunk
            if "similarity" not in chunk:
                chunk["similarity"] = 0.5 # default matching score placeholder
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (60.0 + rank + 1))
            
        # Sort chunks based on RRF scores
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        merged_results = []
        for cid in sorted_ids[:match_count]:
            merged_results.append(chunk_map[cid])
            
        return merged_results

    def upload_file(self, bucket_name: str, path_on_bucket: str, file_content: bytes, content_type: str = "application/pdf") -> str:
        """
        Uploads a file (PDF or extracted figures) to Supabase Storage and returns its public URL.
        """
        # Ensure bucket exists
        try:
            self.client.storage.create_bucket(bucket_name)
        except Exception:
            pass # Bucket already exists or error handled
        
        self.client.storage.from_(bucket_name).upload(
            path=path_on_bucket,
            file=file_content,
            file_options={"content-type": content_type, "x-upsert": "true"}
        )
        
        # Get public url
        url_res = self.client.storage.from_(bucket_name).get_public_url(path_on_bucket)
        return url_res

    def get_or_create_session(self, document_id: Union[str, List[str]]) -> str:
        """
        Retrieves the active chat session ID for a document, or creates one if it doesn't exist.
        Supports single UUIDs and list/comma-separated UUIDs for multi-document synthesis.
        """
        if isinstance(document_id, list):
            document_id = ",".join([str(d).strip() for d in document_id if str(d).strip()])
            
        is_multi = "," in document_id or not document_id
        
        try:
            if is_multi:
                # For multi-document, query where document_id is null
                response = self.client.table("chat_sessions").select("id").is_("document_id", "null").order("created_at", desc=True).limit(1).execute()
                if response.data:
                    return response.data[0]["id"]
                
                data = {
                    "document_id": None,
                    "title": "Library Synthesis Chat"
                }
                res = self.client.table("chat_sessions").insert(data).execute()
                if not res.data:
                    raise Exception("Failed to create multi-document chat session.")
                return res.data[0]["id"]
            else:
                # Standard single-document session lookup
                response = self.client.table("chat_sessions").select("id").eq("document_id", document_id).order("created_at", desc=True).limit(1).execute()
                if response.data:
                    return response.data[0]["id"]
                    
                # Create new session if none exists
                doc_res = self.client.table("documents").select("paper_title").eq("id", document_id).execute()
                title = "Chat Session"
                if doc_res.data:
                    title = f"Chat: {doc_res.data[0]['paper_title']}"
                    
                data = {
                    "document_id": document_id,
                    "title": title[:100]
                }
                res = self.client.table("chat_sessions").insert(data).execute()
                if not res.data:
                    raise Exception("Failed to create chat session.")
                return res.data[0]["id"]
        except Exception as e:
            print(f"⚠️ Warning: chat_sessions table query failed: {e}. Ephemeral fallback active.")
            raise e

    def get_chat_history(self, document_id: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """
        Fetches all chat messages for a given document's session.
        """
        try:
            session_id = self.get_or_create_session(document_id)
            response = self.client.table("chat_messages").select("role", "content", "created_at").eq("session_id", session_id).order("created_at").execute()
            return response.data or []
        except Exception as e:
            print(f"⚠️ Error fetching chat history: {e}")
            return []

    def add_chat_message(self, document_id: Union[str, List[str]], role: str, content: str):
        """
        Appends a message to the active chat session of a document.
        """
        try:
            session_id = self.get_or_create_session(document_id)
            data = {
                "session_id": session_id,
                "role": role,
                "content": content
            }
            self.client.table("chat_messages").insert(data).execute()
        except Exception as e:
            print(f"⚠️ Error saving chat message: {e}")

    def delete_chat_history(self, document_id: Union[str, List[str]]):
        """
        Deletes the chat session and all cascading message records for a document.
        """
        if isinstance(document_id, list):
            document_id = ",".join([str(d).strip() for d in document_id if str(d).strip()])
            
        is_multi = "," in document_id or not document_id
        try:
            if is_multi:
                self.client.table("chat_sessions").delete().is_("document_id", "null").execute()
            else:
                self.client.table("chat_sessions").delete().eq("document_id", document_id).execute()
        except Exception as e:
            print(f"⚠️ Error deleting chat history: {e}")

