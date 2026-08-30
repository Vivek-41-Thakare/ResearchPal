import re
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import HTTPException

class PWCService:
    def __init__(self):
        self.arxiv_base_url = "https://export.arxiv.org/api/query"

    def _extract_github_url(self, text: str) -> Optional[str]:
        """
        Scans the abstract text for a GitHub repository link using a regex.
        """
        match = re.search(r'(https?://github\.com/[a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_/]+)', text)
        if match:
            # Clean up trailing punctuation if matched by regex
            url = match.group(0)
            if url.endswith('.') or url.endswith(','):
                url = url[:-1]
            return url
        return None

    def _parse_arxiv_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Parses arXiv's Atom XML response and formats it to match the legacy PWC schema.
        """
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'opensearch': 'http://a9.com/-/spec/opensearch/1.1/',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        try:
            root = ET.fromstring(xml_content)
        except Exception as e:
            print(f"XML Parsing Error: {e}")
            return []

        results = []
        for entry in root.findall('atom:entry', namespaces):
            # 1. Extract ID & ArXiv ID
            id_url = entry.find('atom:id', namespaces)
            id_str = id_url.text if id_url is not None else ""
            arxiv_id = id_str.split('/abs/')[-1] if '/abs/' in id_str else id_str
            
            # 2. Extract Title
            title_node = entry.find('atom:title', namespaces)
            title = title_node.text.strip().replace('\n', ' ') if title_node is not None else "Untitled"
            
            # 3. Extract Abstract (Summary)
            summary_node = entry.find('atom:summary', namespaces)
            abstract = summary_node.text.strip().replace('\n', ' ') if summary_node is not None else ""
            
            # 4. Extract Authors
            authors = []
            for author_node in entry.findall('atom:author', namespaces):
                name_node = author_node.find('atom:name', namespaces)
                if name_node is not None and name_node.text:
                    authors.append(name_node.text.strip())
            
            # 5. Format Published Date
            published_node = entry.find('atom:published', namespaces)
            published_raw = published_node.text if published_node is not None else ""
            try:
                # E.g., "2017-06-12T17:57:34Z" -> "12 June 2017"
                dt = datetime.strptime(published_raw.split('T')[0], "%Y-%m-%d")
                published_str = dt.strftime("%d %B %Y")
            except Exception:
                published_str = published_raw
            
            # 6. Extract PDF URL
            pdf_url = ""
            for link in entry.findall('atom:link', namespaces):
                rel = link.attrib.get('rel')
                title_attr = link.attrib.get('title')
                href = link.attrib.get('href')
                if rel == 'related' and title_attr == 'pdf':
                    pdf_url = href
                    break
            
            if not pdf_url:
                pdf_url = id_str.replace('/abs/', '/pdf/') + ".pdf" if '/abs/' in id_str else ""

            # 7. Extract Github URL if present in the abstract description
            github_url = self._extract_github_url(abstract)
            repo_json = None
            if github_url:
                try:
                    parts = github_url.replace("https://github.com/", "").split('/')
                    owner = parts[0] if len(parts) > 0 else ""
                    name = parts[1] if len(parts) > 1 else ""
                    repo_json = {
                        "url": github_url,
                        "owner": owner,
                        "name": name,
                        "stars": 0,
                        "framework": "PyTorch" if "pytorch" in abstract.lower() else "TensorFlow" if "tensorflow" in abstract.lower() else ""
                    }
                except Exception:
                    pass

            paper_json = {
                "id": arxiv_id,
                "arxiv_id": arxiv_id,
                "url_pdf": pdf_url,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published": published_str
            }
            
            results.append({
                "paper": paper_json,
                "repository": repo_json
            })
            
        return results

    async def get_trending_papers(self, page: int = 1, items: int = 10) -> Dict[str, Any]:
        """
        Fetches the latest computer science research papers from arXiv (acts as our trending feed).
        """
        start = (page - 1) * items
        # Query latest machine learning/AI papers
        url = f"{self.arxiv_base_url}?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CV&sortBy=submittedDate&sortOrder=descending&start={start}&max_results={items}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=15.0)
            response.raise_for_status()
            results = self._parse_arxiv_xml(response.text)
            next_page = page + 1 if len(results) >= items else None
            return {"results": results, "next_page": next_page}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching arXiv trending feed: {str(e)}")

    async def search_papers(self, query: str, page: int = 1, items: int = 10) -> Dict[str, Any]:
        """
        Searches arXiv for papers matching the user query.
        """
        start = (page - 1) * items
        # Format search terms (convert spaces to arXiv query parameters)
        terms = query.strip().split()
        formatted_terms = "+AND+".join([f"all:{term}" for term in terms]) if terms else "all:machine+learning"
        url = f"{self.arxiv_base_url}?search_query={formatted_terms}&start={start}&max_results={items}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=15.0)
            response.raise_for_status()
            results = self._parse_arxiv_xml(response.text)
            next_page = page + 1 if len(results) >= items else None
            return {"results": results, "next_page": next_page}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error searching arXiv: {str(e)}")
