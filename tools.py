from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
import time

load_dotenv(override=True)

# Try to get API key from multiple sources
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# For Streamlit Cloud deployment
if not TAVILY_API_KEY:
    try:
        import streamlit as st
        TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
    except:
        pass

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in environment variables or streamlit secrets")

tavily = TavilyClient(api_key=TAVILY_API_KEY)

@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic."""
    try:
        results = tavily.search(query=query, max_results=5)
        out = []
        
        for idx, r in enumerate(results.get('results', []), 1):
            out.append(
                f"{idx}. Title: {r.get('title', 'N/A')}\n"
                f"   URL: {r.get('url', 'N/A')}\n"
                f"   Snippet: {r.get('content', 'N/A')[:300]}\n"
            )
        
        if not out:
            return f"No results found for query: '{query}'"
        
        result_text = "\n---\n".join(out)
        result_text += "\n\n📌 IMPORTANT: The URLs listed above are available for deeper scraping."
        return result_text
        
    except Exception as e:
        return f"Search failed for '{query}': {str(e)}"

@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL."""
    if not url.startswith(('http://', 'https://')):
        return f"❌ Invalid URL: {url}"
    
    try:
        resp = requests.get(
            url, 
            timeout=10, 
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
        
        main_content = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', class_='content') or
            soup.find('body')
        )
        
        if main_content:
            text = main_content.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)
        
        text = ' '.join(text.split())
        
        max_chars = 5000
        result = f"✅ Successfully scraped: {url}\n"
        result += f"📄 Content length: {len(text)} characters\n\n"
        
        if len(text) > max_chars:
            result += text[:max_chars]
            result += f"\n\n[Content truncated]"
        else:
            result += text
        
        return result
    
    except requests.Timeout:
        return f"⏰ Timeout scraping {url}"
    except requests.HTTPError as e:
        return f"❌ HTTP error: {str(e)}"
    except Exception as e:
        return f"⚠️ Error: {str(e)}"