import asyncio
import httpx
from dotenv import load_dotenv
load_dotenv()

from services.parse_service import ParseService

async def main():
    print("🚀 Downloading a sample PDF from arXiv (Attention Is All You Need)...")
    pdf_url = "https://arxiv.org/pdf/1706.03762v7"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(pdf_url)
            pdf_bytes = resp.content
        print(f"📥 Downloaded {len(pdf_bytes) / 1024:.2f} KB of PDF.")
    except Exception as e:
        print(f"❌ Failed to download PDF: {e}")
        return

    print("🔍 Initializing ParseService...")
    try:
        parser = ParseService()
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    print("⚙️ Running parse_pdf (this starts PyMuPDF + Adobe Extract API)...")
    try:
        text, figures, tables = await parser.parse_pdf(pdf_bytes, "attention.pdf")
        print("✅ Success!")
        print(f"\n📝 Extracted Text Preview (First 500 chars):\n{text[:500]}...")
        
        print(f"\n🖼️ Extracted Figures count: {len(figures)}")
        for fig in figures[:3]:
            print(f"  - {fig['filename']} ({len(fig['content'])} bytes)")
            
        print(f"\n📊 Extracted Tables count: {len(tables)}")
        for table in tables[:3]:
            print(f"  - {table['filename']} (Preview first 100 chars):")
            print(f"    {table['content'][:100].strip()}...")
    except Exception as e:
        print(f"❌ Error during parsing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
