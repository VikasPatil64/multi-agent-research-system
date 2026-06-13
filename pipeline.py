from agents import (
    build_search_agent, 
    build_reader_agent, 
    writer_chain, 
    critic_chain, 
    ResearchReport, 
    CriticFeedback,
    report_parser,      
    llm                 
)
from utils import (
    extract_urls_from_messages, 
    extract_search_summary, 
    validate_topic,
    format_research_context,
    log_step
)
from rate_limiter import check_quota, get_remaining_quota, limiter
from typing import Dict, Any, List
import json
from datetime import datetime
import sys
import time
import asyncio
import aiohttp
from bs4 import BeautifulSoup


# ========== ASYNC SCRAPING FOR PARALLEL PROCESSING ==========

async def scrape_url_async(session, url: str, idx: int) -> tuple:
    """Scrape a single URL asynchronously"""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')
            
            # Remove unwanted elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                tag.decompose()
            
            # Find main content
            main_content = (
                soup.find('main') or 
                soup.find('article') or 
                soup.find('div', class_='content') or
                soup.find('body')
            )
            
            if main_content:
                content = main_content.get_text(separator=" ", strip=True)
            else:
                content = soup.get_text(separator=" ", strip=True)
            
            # Clean whitespace
            content = ' '.join(content.split())
            
            # Truncate to 5000 chars
            if len(content) > 5000:
                content = content[:5000] + "..."
            
            return idx, url, True, content
    except Exception as e:
        return idx, url, False, str(e)

async def scrape_parallel(urls: List[str], max_urls: int = 2) -> List[tuple]:
    """Scrape multiple URLs in parallel"""
    urls_to_scrape = urls[:max_urls]
    async with aiohttp.ClientSession() as session:
        tasks = [scrape_url_async(session, url, i) for i, url in enumerate(urls_to_scrape, 1)]
        return await asyncio.gather(*tasks)

# ========== HELPER FUNCTIONS ==========

# ========== HELPER FUNCTIONS ==========

def wait_with_backoff(attempt, base_delay=2):
    """Wait with exponential backoff to avoid rate limits"""
    delay = base_delay * (attempt + 1)
    print(f"⏳ Rate limit protection: Waiting {delay} seconds...")
    time.sleep(delay)

def retry_on_quota(func, max_retries=2):
    """Retry function with exponential backoff on quota errors ONLY.
    Non-quota errors fail immediately with clear debug info."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_msg = str(e)
            
            # Check if it's a quota error (429)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                wait_time = 2 ** attempt * 5  # 5s, 10s
                print(f"⚠️ QUOTA ERROR: {error_msg[:150]}")
                print(f"⚠️ Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                # Non-quota error - fail immediately with clear message
                print(f"❌ NON-QUOTA ERROR: {type(e).__name__}")
                print(f"   Message: {error_msg[:300]}")
                raise e  # Don't retry, just fail
    
    raise Exception(f"Failed after {max_retries} retries due to quota errors")

def safe_api_call(func, call_name="API call", max_retries=2):
    """Wrapper for API calls with better error messages"""
    for attempt in range(max_retries):
        try:
            print(f"📞 Making {call_name}...")
            result = func()
            print(f"✅ {call_name} successful")
            return result
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                wait_time = 2 ** attempt * 5
                print(f"⚠️ Quota exceeded on {call_name}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ {call_name} failed: {type(e).__name__}: {error_msg[:200]}")
                raise e
    raise Exception(f"Failed {call_name} after {max_retries} attempts")
# ========== MAIN PIPELINE ==========

def run_research_pipeline(topic: str, save_checkpoint: bool = True) -> Dict[str, Any]:
    """
    Run the complete research pipeline: search -> scrape -> write -> critique
    """
    
    # Check quota before starting
    if not check_quota():
        print(f"\n❌ Daily quota exhausted. {get_remaining_quota()} calls remaining today.")
        print("⏰ Please try again tomorrow or upgrade your plan.")
        return {"error": "Quota exhausted", "topic": topic}
    
    # Initialize state
    state = {
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "urls_found": [],
        "search_summary": "",
        "scraped_content": "",
        "report": None,
        "report_dict": {},
        "feedback": None,
        "feedback_dict": {},
        "errors": []
    }
    
    # Validate topic
    if not validate_topic(topic):
        raise ValueError(f"Invalid topic: '{topic}'. Topic must be at least 3 characters long.")
    
    print(f"\n{'='*60}")
    print(f"🚀 Starting Research Pipeline for: {topic}")
    print(f"{'='*60}\n")
    
    try:
        # ========== STEP 1: SEARCH AGENT ==========
        log_step("1/4 - Search Agent: Finding information")
        
        def do_search():
            search_agent = build_search_agent()
            return search_agent.invoke({
                "messages": [("user", f"Find recent, reliable and detailed information about: {topic}. Include at least 5 sources with URLs.")]
            })
        
        search_result = retry_on_quota(do_search)
        
        # Extract URLs and summary from the messages
        all_messages = search_result.get("messages", [])
        state["urls_found"] = extract_urls_from_messages(all_messages)
        state["search_summary"] = extract_search_summary(all_messages)
        
        print(f"✅ Found {len(state['urls_found'])} unique URLs")
        for i, url in enumerate(state["urls_found"][:3], 1):
            print(f"   {i}. {url[:80]}...")
        
        if not state["urls_found"]:
            state["errors"].append("No URLs found in search results")
            print("⚠️ Warning: No URLs extracted from search results")
        
        # Wait between stages
        wait_with_backoff(0, 1)
        
        # ========== STEP 2: READER AGENT (PARALLEL) ==========
        log_step("2/4 - Reader Agent: Scraping web content (parallel)")
        
        if state["urls_found"]:
            print(f"📖 Scraping {min(2, len(state['urls_found']))} URLs in parallel...")
            
            # Run parallel scraping
            scraped_results = asyncio.run(scrape_parallel(state["urls_found"], max_urls=2))
            
            scraped_pieces = []
            for idx, url, success, content in scraped_results:
                if success:
                    scraped_pieces.append(f"## Source {idx}: {url}\n\n{content}")
                    print(f"   ✅ Scraped URL {idx}: {url[:60]}... ({len(content)} chars)")
                else:
                    print(f"   ❌ Failed URL {idx}: {url[:60]}... - {content[:100]}")
                    state["errors"].append(f"Scraping failed for {url}: {content}")
            
            if scraped_pieces:
                state["scraped_content"] = "\n\n---\n\n".join(scraped_pieces)
                print(f"\n✅ Successfully scraped {len(scraped_pieces)} source(s) in parallel")
            else:
                state["scraped_content"] = "No content could be scraped from the found URLs."
                print(f"\n⚠️ No content successfully scraped")
        else:
            state["scraped_content"] = "No URLs were found to scrape."
            print("⚠️ Skipping scraping - no URLs available")
        
        # Wait between stages
        wait_with_backoff(1, 1)
        
        # ========== STEP 3: WRITER CHAIN ==========
        log_step("3/4 - Writer Chain: Generating research report")
        
        # Check quota before writer
        if not check_quota():
            raise Exception("Quota exhausted before writer stage")
        
        # Combine and format research context
        research_context = format_research_context(
            state["search_summary"],
            state["scraped_content"],
            max_total=6000
        )
        
        print("📝 Generating report...")
    
        def do_write():
            return writer_chain.invoke({
                "topic": topic,
                "research": research_context
            })
        
        report_obj = safe_api_call(do_write, call_name="Writer Chain")
        
        # Store both the object and a serializable dict
        state["report"] = report_obj
        state["report_dict"] = report_obj.model_dump()
        
        print(f"✅ Report generated")
        print(f"   - Introduction: {len(report_obj.introduction)} chars")
        print(f"   - Key findings: {len(report_obj.key_findings)} points")
        print(f"   - Sources: {len(report_obj.sources)} URLs")
        
        # Display report preview
        print("\n" + "="*60)
        print("📄 REPORT PREVIEW:")
        print("="*60)
        print(report_obj.introduction[:200] + "...\n")
        
        # Wait between stages
        wait_with_backoff(2, 1)
        
        # ========== STEP 4: CRITIC CHAIN ==========
        log_step("4/4 - Critic Chain: Evaluating report quality")
        
        # Check quota before critic
        if not check_quota():
            raise Exception("Quota exhausted before critic stage")
        
        print("🔍 Critiquing report...")
        def do_critic():
            # Convert report to string for critic
            report_text = f"# {topic}\n\n{report_obj.introduction}\n\n"
            report_text += "\n".join([f"## Finding {i+1}: {f}" for i, f in enumerate(report_obj.key_findings)])
            report_text += f"\n\n## Conclusion\n{report_obj.conclusion}"
            report_text += f"\n\n## Sources\n{chr(10).join(report_obj.sources)}"
            
            return critic_chain.invoke({"report": report_text[:4000]})
        
        feedback_obj = safe_api_call(do_critic, call_name="Critic Chain")
        
        state["feedback"] = feedback_obj
        state["feedback_dict"] = feedback_obj.model_dump()
        
        print(f"✅ Critique generated")
        print(f"   - Score: {feedback_obj.score}/10")
        print(f"   - Verdict: {feedback_obj.verdict}")
        
        # Display critique preview
        print("\n" + "="*60)
        print("📊 CRITIQUE PREVIEW:")
        print("="*60)
        print(f"Score: {feedback_obj.score}/10")
        print(f"Verdict: {feedback_obj.verdict}\n")
        
        
        # ========== REVISION LOOP (NO format_instructions) ==========
        max_revisions = 2
        revision_count = 0
        current_report = report_obj
        current_feedback = feedback_obj

        while current_feedback.score < 7.0 and revision_count < max_revisions:
            revision_count += 1
            print(f"\n🔄 REVISION {revision_count}/{max_revisions}: Score {current_feedback.score}/10 < 7, improving...")
            
            # Simple prompt - NO format_instructions to avoid nested braces
            revision_text = f"""The original report scored {current_feedback.score}/10. 
Critic verdict: {current_feedback.verdict}

Weaknesses to fix:
{chr(10).join(['- ' + i for i in current_feedback.improvements])}

Original report:
Introduction: {current_report.introduction}
Key Findings: {chr(10).join(current_report.key_findings)}
Conclusion: {current_report.conclusion}

Rewrite and IMPROVE this report. Address each weakness. 
Return a valid JSON with: introduction, key_findings (array of 3 strings), conclusion, sources (array of strings)."""
            
            from langchain_core.prompts import ChatPromptTemplate
            simple_revision_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert research writer. Improve the report based on feedback. Return ONLY valid JSON."),
                ("human", revision_text)
            ])
            simple_revision_chain = simple_revision_prompt | llm | report_parser
            
            print("📝 Revising report...")
            
            try:
                revised_report = simple_revision_chain.invoke({})
                print(f"✅ Revision {revision_count} complete")
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"❌ Revision failed: {e}")
                break
            
            # Re-critique
            print("🎯 Re-evaluating...")
            revised_report_text = f"# {topic}\n\n{revised_report.introduction}\n\n"
            revised_report_text += "\n".join([f"## Finding {i+1}: {f}" for i, f in enumerate(revised_report.key_findings)])
            revised_report_text += f"\n\n## Conclusion\n{revised_report.conclusion}"
            revised_report_text += f"\n\n## Sources\n{chr(10).join(revised_report.sources)}"
            
            try:
                revised_feedback = critic_chain.invoke({"report": revised_report_text[:4000]})
                print(f"📊 Score: {current_feedback.score}/10 → {revised_feedback.score}/10")
                current_report = revised_report
                current_feedback = revised_feedback
            except Exception as e:
                print(f"❌ Re-critique failed: {e}")
                break

        final_report = current_report
        final_feedback = current_feedback

        state["report"] = final_report
        state["report_dict"] = final_report.model_dump()
        state["feedback"] = final_feedback
        state["feedback_dict"] = final_feedback.model_dump()                
        if save_checkpoint:
            checkpoint_file = f"research_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                serializable_state = {
                    "topic": state["topic"],
                    "timestamp": state["timestamp"],
                    "urls_found": state["urls_found"],
                    "search_summary": state["search_summary"][:1000],
                    "scraped_content": state["scraped_content"][:1000],
                    "report": state["report_dict"],
                    "feedback": state["feedback_dict"],
                    "errors": state["errors"]
                }
                json.dump(serializable_state, f, indent=2, ensure_ascii=False)
            print(f"💾 Checkpoint saved to: {checkpoint_file}")
        
        # ========== SUMMARY ==========
        print("\n" + "="*60)
        print("🎉 PIPELINE COMPLETE!")
        print("="*60)
        print(f"📊 Statistics:")
        print(f"   - URLs found: {len(state['urls_found'])}")
        print(f"   - Content scraped: {len(state['scraped_content'])} chars")
        print(f"   - Report score: {final_feedback.score}/10")
        print(f"   - Report sources: {len(final_report.sources)}")
        if state["errors"]:
            print(f"   - Errors encountered: {len(state['errors'])}")
        
        return state
        
    except Exception as e:
        error_msg = f"Pipeline failed with exception: {str(e)}"
        print(f"\n❌ {error_msg}")
        state["errors"].append(error_msg)
        
        # Save error checkpoint
        if save_checkpoint:
            error_file = f"research_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "topic": topic,
                    "timestamp": state["timestamp"],
                    "error": str(e),
                    "errors": state["errors"]
                }, f, indent=2, ensure_ascii=False)
            print(f"💾 Error checkpoint saved to: {error_file}")
        
        return state

def display_final_report(state: Dict[str, Any]):
    """Display the complete research results in a formatted way"""
    print("\n" + "="*80)
    print("📋 FINAL RESEARCH REPORT")
    print("="*80)
    
    if state.get("report"):
        report = state["report"]
        print(f"\n# {state['topic']}\n")
        print(f"## Introduction\n{report.introduction}\n")
        print(f"## Key Findings")
        for i, finding in enumerate(report.key_findings, 1):
            print(f"\n### {i}. {finding}")
        print(f"\n## Conclusion\n{report.conclusion}\n")
        print(f"## Sources")
        for source in report.sources:
            print(f"- {source}")
    
    print("\n" + "="*80)
    print("🔍 CRITIC FEEDBACK")
    print("="*80)
    
    if state.get("feedback"):
        feedback = state["feedback"]
        print(f"\n**Score:** {feedback.score}/10")
        print(f"\n**Verdict:** {feedback.verdict}")
        print(f"\n**Strengths:**")
        for s in feedback.strengths:
            print(f"  ✓ {s}")
        print(f"\n**Areas to Improve:**")
        for i in feedback.improvements:
            print(f"  ✗ {i}")
    
    if state.get("errors"):
        print("\n" + "="*80)
        print("⚠️ ERRORS ENCOUNTERED")
        print("="*80)
        for error in state["errors"]:
            print(f"  • {error}")

if __name__ == "__main__":
    # Get topic from user input
    topic = input("\n🔍 Enter a research topic: ").strip()
    
    if not topic:
        print("❌ No topic entered. Exiting.")
        sys.exit(1)
    
    # Run the pipeline
    result = run_research_pipeline(topic, save_checkpoint=True)
    
    # Ask if user wants to see full results
    if not result.get("error"):
        print("\n" + "="*60)
        show_full = input("📖 Show full report and critique? (y/n): ").strip().lower()
        
        if show_full == 'y':
            display_final_report(result)
    
    print("\n✅ Research complete! Check the checkpoint JSON file for full results.")