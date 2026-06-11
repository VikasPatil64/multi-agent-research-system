"""Utility functions for the multi-agent research system"""

import re
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage, HumanMessage
import tiktoken

def extract_urls_from_messages(messages: List[BaseMessage]) -> List[str]:
    """
    Extract all URLs from agent messages (including ToolMessages and AIMessages)
    """
    urls = []
    url_pattern = r'URL:\s*(https?://[^\s\n]+)'
    url_pattern_alt = r'(https?://[^\s\n]+\.(?:com|org|net|gov|edu|io|news|co|uk|us|ai|[a-z]{2})[^\s\n]*)'
    
    for msg in messages:
        if isinstance(msg, ToolMessage):
            matches = re.findall(url_pattern, msg.content)
            urls.extend(matches)
            if not matches:
                matches = re.findall(url_pattern_alt, msg.content)
                urls.extend(matches)
        elif isinstance(msg, AIMessage):
            if isinstance(msg.content, str):
                matches = re.findall(url_pattern, msg.content)
                urls.extend(matches)
            elif isinstance(msg.content, list):
                for item in msg.content:
                    if isinstance(item, dict) and 'text' in item:
                        matches = re.findall(url_pattern, item['text'])
                        urls.extend(matches)
        elif isinstance(msg, HumanMessage) and isinstance(msg.content, str):
            matches = re.findall(url_pattern, msg.content)
            urls.extend(matches)
    
    # Remove duplicates preserving order
    unique_urls = []
    for url in urls:
        if url not in unique_urls:
            unique_urls.append(url)
    
    return unique_urls

def extract_search_summary(messages: List[BaseMessage]) -> str:
    """Extract the final search summary text from agent messages"""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            if isinstance(msg.content, str):
                return msg.content
            elif isinstance(msg.content, list) and len(msg.content) > 0:
                if isinstance(msg.content[0], dict) and 'text' in msg.content[0]:
                    return msg.content[0]['text']
                return str(msg.content[0])
    return ""

def validate_topic(topic: str) -> bool:
    """Validate that the research topic is not empty or too short"""
    if not topic or not isinstance(topic, str):
        return False
    topic = topic.strip()
    if len(topic) < 3:
        return False
    return True

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens using tiktoken"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: approximate (1 token ~ 4 chars)
        return len(text) // 4

def truncate_by_tokens(text: str, max_tokens: int = 3000, model: str = "gpt-4") -> str:
    """Truncate text to fit within token limit"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return encoding.decode(tokens[:max_tokens])
    except Exception:
        # Fallback: character-based truncation
        if len(text) <= max_tokens * 4:
            return text
        return text[:max_tokens * 4] + "..."

def truncate_text(text: str, max_length: int = 4000, add_ellipsis: bool = True) -> str:
    """Truncate text to a maximum length while preserving word boundaries"""
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    
    if add_ellipsis:
        truncated += "..."
    
    return truncated

def format_research_context(search_summary: str, scraped_content: str, max_total: int = 6000) -> str:
    """Format and combine search results and scraped content for the writer"""
    search_limit = max_total // 3
    scrape_limit = max_total - search_limit
    
    search_part = f"SEARCH RESULTS:\n{truncate_text(search_summary, search_limit)}\n\n"
    scrape_part = f"SCRAPED CONTENT:\n{truncate_text(scraped_content, scrape_limit)}"
    
    return search_part + scrape_part

def log_step(step_name: str, data: Optional[Any] = None):
    """Simple logging utility for pipeline steps"""
    print("\n" + "="*60)
    print(f"🔍 Step: {step_name}")
    print("="*60)
    if data:
        print(f"📊 Data: {data[:200] if isinstance(data, str) else data}")