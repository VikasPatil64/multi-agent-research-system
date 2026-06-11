from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import streamlit as st  
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Optional, List, Dict, Any
import time
from rate_limiter import rate_limited
from pydantic import BaseModel, Field
from typing import List
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv(override=True)

# ========== PYDANTIC MODELS FOR STRUCTURED OUTPUT ==========

class ResearchReport(BaseModel):
    """Structured research report model"""
    introduction: str = Field(description="Overview of the topic and why it matters")
    key_findings: List[str] = Field(description="At least 3 major findings with evidence", min_items=3)
    conclusion: str = Field(description="Summary of findings and implications")
    sources: List[str] = Field(description="URLs referenced in the report")

class CriticFeedback(BaseModel):
    """Structured critic feedback model"""
    score: float = Field(ge=0, le=10, description="Quality score out of 10")
    strengths: List[str] = Field(description="Specific strengths of the report")
    improvements: List[str] = Field(description="Specific areas needing improvement")
    verdict: str = Field(description="One-line summary verdict")

# Create parsers for structured output
report_parser = PydanticOutputParser(pydantic_object=ResearchReport)
critic_parser = PydanticOutputParser(pydantic_object=CriticFeedback)

# ========== LLM INITIALIZATION WITH RATE LIMITING ==========

@rate_limited  # ✅ Applied rate limiter
def get_llm_with_retry():
    """Initialize Gemini with retry logic and error handling"""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # For Streamlit Cloud deployment - TRY SECRETS IF ENV VAR NOT FOUND
    if not api_key:
        try:
            api_key = st.secrets.get("GOOGLE_API_KEY")
            print("Using API key from Streamlit secrets")
        except:
            pass
    
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables or Streamlit secrets")
    
    print("KEY FOUND:", bool(api_key))
    if api_key:
        print("KEY PREFIX:", api_key[:15])
    
    # Simple retry without backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0,
                google_api_key=api_key,
                request_timeout=30,
                max_retries=2
            )
            return llm
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"Retry {attempt + 1}/{max_retries} after error: {e}")
            time.sleep(2)
    
    return None
llm = get_llm_with_retry()
print("Gemini Connected!")

# ========== AGENT BUILDERS ==========

def build_search_agent():
    """Agent that searches the web using Tavily API"""
    return create_agent(
        model=llm, 
        tools=[web_search],
        system_prompt="""You are a web search specialist. 
        When searching for information:
        1. Use the web_search tool to find recent, authoritative information
        2. Extract and remember all URLs from search results
        3. Summarize key findings from each source
        4. Always include source URLs in your response"""
    )

def build_reader_agent():
    """Agent that scrapes and reads web page content"""
    return create_agent(
        model=llm, 
        tools=[scrape_url],
        system_prompt="""You are a web content reader. When given URLs:
        1. ALWAYS use the scrape_url tool to get content from each URL
        2. Extract key facts, dates, numbers, statistics, and direct quotes
        3. NEVER say you cannot scrape - just use the tool
        4. If a URL fails, report what was found and continue with others
        5. Format your response with clear source attribution
        6. Be thorough - extract detailed information, not just summaries"""
    )

# ========== WRITER CHAIN WITH STRUCTURED OUTPUT ==========

writer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert research writer. Write clear, structured and insightful reports based on the information provided.
            
            {format_instructions}
            
            Always cite sources by including URLs in the text and in the sources section.
            Be factual, detailed, and professional."""
        ),
        (
            "human",
            """Write a detailed research report on the topic below.

            Topic: {topic}
            
            Research Gathered:
            {research}
            
            IMPORTANT: Your response must be valid JSON matching the format instructions above."""
        ),
    ]
).partial(format_instructions=report_parser.get_format_instructions())

writer_chain = writer_prompt | llm | report_parser

# ========== CRITIC CHAIN WITH STRUCTURED OUTPUT ==========

critic_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """You are a sharp and constructive research critic. Be honest and specific.
         
         {format_instructions}
         
         Evaluate reports based on:
         - Factual accuracy and evidence
         - Source quality and attribution
         - Depth of analysis
         - Structural clarity
         - Completeness of coverage"""),
        ("human", """Review the research report below and evaluate it strictly.

        Report:
        {report}
        
        IMPORTANT: Your response must be valid JSON matching the format instructions above.""")
    ]
).partial(format_instructions=critic_parser.get_format_instructions())

critic_chain = critic_prompt | llm | critic_parser