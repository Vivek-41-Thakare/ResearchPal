import asyncio
from services.pwc_service import PWCService

async def main():
    print("🚀 Initializing PWCService (HTTP Client Mode)...")
    pwc = PWCService()
    
    print("📈 Fetching top 3 trending papers from PWC Flask microservice...")
    try:
        data = await pwc.get_trending_papers(page=1, items=3)
        results = data.get("results", [])
        print(f"✅ Success! Retrieved {len(results)} papers:")
        for idx, res in enumerate(results, 1):
            paper = res.get("paper", {})
            repo = res.get("repository", {})
            print(f"\n[{idx}] Title: {paper.get('title')}")
            print(f"    PDF URL: {paper.get('url_pdf')}")
            if repo:
                print(f"    Code Repo: {repo.get('url')} (Stars: {repo.get('stars')})")
            else:
                print("    Code Repo: None")
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        print("\n💡 NOTE: Please make sure your PWC Flask server is running at http://localhost:8080 before testing.")

if __name__ == "__main__":
    asyncio.run(main())
