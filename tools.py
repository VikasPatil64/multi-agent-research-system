from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
import time

load_dotenv(override=True)

# Initialize Tavily client
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in environment variables")

tavily = TavilyClient(api_key=TAVILY_API_KEY)

# Simple retry function (no decorator for Python 3.14 compatibility)
def simple_retry(func, max_attempts=3, delay=1):
    """Simple retry wrapper without external dependencies"""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise e
            print(f"Retry {attempt + 1}/{max_attempts} after error: {str(e)[:100]}")
            time.sleep(delay * (attempt + 1))
    return None

@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic. Returns Titles, URLs and snippets."""
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
        result_text += "\n\n📌 IMPORTANT: The URLs listed above are available for deeper scraping. Use scrape_url() on these URLs to get detailed content."
        return result_text
        
    except Exception as e:
        return f"Search failed for '{query}': {str(e)}"

@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        return f"❌ Invalid URL: {url} - must start with http:// or https://"
    
    try:
        # Make request with proper headers
        resp = requests.get(
            url, 
            timeout=10, 
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5"
            }
        )
        resp.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Remove unwanted elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
        
        # Try to find main content area
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
        
        # Clean whitespace
        text = ' '.join(text.split())
        
        # Limit to reasonable length (5000 chars)
        max_chars = 5000
        result = f"✅ Successfully scraped: {url}\n"
        result += f"📄 Content length: {len(text)} characters\n\n"
        
        if len(text) > max_chars:
            result += text[:max_chars]
            result += f"\n\n[Content truncated from {len(text)} to {max_chars} characters]"
        else:
            result += text
        
        return result
    
    except requests.Timeout:
        return f"⏰ Timeout scraping {url} - server took too long to respond"
    except requests.HTTPError as e:
        return f"❌ HTTP error scraping {url}: {str(e)}"
    except requests.ConnectionError:
        return f"🔌 Connection error scraping {url} - could not reach the server"
    except Exception as e:
        return f"⚠️ Unexpected error scraping {url}: {str(e)}"

if __name__ == "__main__":
    print("Testing web_search...")
    result = web_search.invoke("What is the recent news about AI?")
    print(result[:500])
    print("\n" + "="*50 + "\n")
    
    print("Testing scrape_url...")
    result = scrape_url.invoke("https://www.example.com")
    print(result[:500])