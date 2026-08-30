import asyncio
from dotenv import load_dotenv
load_dotenv()

from services.supabase_service import SupabaseService

async def main():
    print("🚀 Initializing SupabaseService...")
    try:
        db = SupabaseService()
        print("✅ Supabase client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        return

    # Test 1: Database Insert & Cleanup
    print("\n📝 Test 1: Testing Database Table Permissions...")
    doc_id = None
    try:
        doc_id = db.insert_document(
            paper_title="Test Connection Paper",
            paper_url="https://arxiv.org/abs/test-connection",
            pdf_path="test/path.pdf"
        )
        print(f"✅ Success! Inserted mock document. Generated ID: {doc_id}")
    except Exception as e:
        print(f"❌ Database Insertion Failed: {e}")
        print("💡 Hint: Ensure you have run the schema.sql script in your Supabase SQL editor.")

    if doc_id:
        try:
            print("🧹 Cleaning up database test record...")
            # Run direct delete query
            db.client.table("documents").delete().eq("id", doc_id).execute()
            print("✅ Database test record cleaned up successfully!")
        except Exception as e:
            print(f"⚠️ Warning: Failed to clean up test record: {e}")

    # # Test 2: Storage Bucket Upload
    # print("\n📦 Test 2: Testing Storage Bucket Upload...")
    # bucket_name = "figures" # or whatever bucket you want to test
    # path_on_bucket = "test_connection_marker.txt"
    # test_content = b"ResearchPaL Connection Test Successful!"
    
    # try:
    #     print(f"📤 Uploading test file to bucket '{bucket_name}'...")
    #     public_url = db.upload_file(
    #         bucket_name=bucket_name,
    #         path_on_bucket=path_on_bucket,
    #         file_content=test_content,
    #         content_type="text/plain"
    #     )
    #     print(f"✅ Success! File uploaded. Public URL:\n    {public_url}")
    # except Exception as e:
    #     print(f"❌ Storage Upload Failed: {e}")
    #     print("💡 Hint: Ensure your Supabase user/service-role has access permissions (RLS) to upload to the bucket.")

if __name__ == "__main__":
    asyncio.run(main())
