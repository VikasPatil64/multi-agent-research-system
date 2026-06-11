"""
Multi-Agent Research System - Streamlit UI
Run with: streamlit run ui_streamlit.py
"""

import streamlit as st
import asyncio
import json
from datetime import datetime
import sys
import os

# Import your pipeline
from pipeline import run_research_pipeline
from rate_limiter import get_remaining_quota

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Research System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        background-color: #ff4b4b;
        color: white;
        font-size: 1.2rem;
    }
    .report-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .score-high {
        color: #00cc00;
        font-size: 2rem;
        font-weight: bold;
    }
    .score-mid {
        color: #ffaa00;
        font-size: 2rem;
        font-weight: bold;
    }
    .score-low {
        color: #ff4444;
        font-size: 2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=80)
    st.title("🤖 Agent Team")
    st.markdown("""
    | Agent | Role |
    |-------|------|
    | 🔍 **Search** | Finds 5 authoritative sources |
    | 📖 **Reader** | Scrapes and extracts content |
    | ✍️ **Writer** | Generates structured report |
    | 🎯 **Critic** | Evaluates quality (0-10) |
    """)
    
    st.divider()
    
    # Quota display
    remaining = get_remaining_quota()
    st.metric("📊 Daily API Calls Remaining", f"{remaining}/18")
    
    if remaining < 3:
        st.warning("⚠️ Low quota! Results may be limited.")
    
    st.divider()
    
    # Example topics
    st.subheader("💡 Try these topics:")
    example_topics = [
        "Impact of AI on job market",
        "Renewable energy trends 2024",
        "Effects of remote work on productivity",
        "Future of electric vehicles",
        "Mental health in tech industry"
    ]
    for topic in example_topics:
        if st.button(f"📌 {topic[:40]}...", key=topic):
            st.session_state.topic_input = topic
            st.rerun()

# Main content
st.title("🔍 Multi-Agent Research System")
st.caption("4 specialized AI agents collaborate to research any topic - fully autonomous")

# Topic input
topic = st.text_input(
    "**Enter your research topic:**",
    value=st.session_state.get("topic_input", ""),
    placeholder="e.g., Impact of war on stock markets",
    help="Be specific for better results"
)

# Advanced options
with st.expander("⚙️ Advanced Options"):
    col1, col2 = st.columns(2)
    with col1:
        save_checkpoint = st.checkbox("Save checkpoint file", value=True)
    with col2:
        show_raw_json = st.checkbox("Show raw JSON output", value=False)

# Run button
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    run_button = st.button("🚀 Start Research", use_container_width=True, disabled=not topic)

# Progress indicators
if run_button and topic:
    # Create placeholders for real-time updates
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    result_placeholder = st.empty()
    
    # Progress bar
    progress_bar = progress_placeholder.progress(0, text="Initializing agents...")
    
    try:
        # Step 1: Search
        status_placeholder.info("🔍 **Agent 1/4: Search** - Finding authoritative sources...")
        progress_bar.progress(10, text="Searching the web...")
        
        # Step 2: Read
        status_placeholder.info("📖 **Agent 2/4: Reader** - Scraping and extracting content...")
        progress_bar.progress(30, text="Reading web pages...")
        
        # Step 3: Write
        status_placeholder.info("✍️ **Agent 3/4: Writer** - Generating structured report...")
        progress_bar.progress(60, text="Writing report...")
        
        # Step 4: Critique
        status_placeholder.info("🎯 **Agent 4/4: Critic** - Evaluating quality...")
        progress_bar.progress(80, text="Critiquing...")
        
        # Run the actual pipeline
        with st.spinner("🤖 Agents are working (this takes 10-15 seconds)..."):
            result = run_research_pipeline(topic, save_checkpoint=save_checkpoint)
        
        progress_bar.progress(100, text="Complete!")
        status_placeholder.success("✅ All agents completed successfully!")
        
        # Display results
        if result.get("error"):
            st.error(f"❌ Error: {result['error']}")
        else:
            # Extract results
            report = result.get("report")
            feedback = result.get("feedback")
            
            if report and feedback:
                # Score color
                score = feedback.score
                if score >= 7:
                    score_class = "score-high"
                elif score >= 4:
                    score_class = "score-mid"
                else:
                    score_class = "score-low"
                
                # Two-column layout for results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📄 Research Report")
                    st.markdown(f"**Topic:** {topic}")
                    
                    with st.expander("📖 Introduction", expanded=True):
                        st.write(report.introduction)
                    
                    with st.expander("🔑 Key Findings", expanded=True):
                        for i, finding in enumerate(report.key_findings, 1):
                            st.markdown(f"**{i}.** {finding}")
                    
                    with st.expander("📝 Conclusion", expanded=True):
                        st.write(report.conclusion)
                    
                    with st.expander("🔗 Sources", expanded=False):
                        for source in report.sources:
                            st.markdown(f"- [{source}]({source})")
                
                with col2:
                    st.markdown("### 🎯 Critic Feedback")
                    
                    # Score display
                    st.markdown(f'<p class="{score_class}">{score}/10</p>', unsafe_allow_html=True)
                    
                    # Verdict
                    st.info(f"**Verdict:** {feedback.verdict}")
                    
                    # Strengths
                    st.markdown("**✅ Strengths**")
                    for s in feedback.strengths:
                        st.success(f"• {s}")
                    
                    # Improvements
                    st.markdown("**⚠️ Areas to Improve**")
                    for i in feedback.improvements:
                        st.warning(f"• {i}")
                    
                    # Statistics
                    st.divider()
                    st.markdown("**📊 Statistics**")
                    st.metric("URLs Found", len(result.get("urls_found", [])))
                    st.metric("Sources Cited", len(report.sources))
                    st.metric("Content Scraped", f"{len(result.get('scraped_content', '')):,} chars")
                
                # Raw JSON option
                if show_raw_json:
                    with st.expander("📋 Raw JSON Output"):
                        st.json({
                            "topic": topic,
                            "urls_found": result.get("urls_found", []),
                            "report": report.dict() if report else None,
                            "feedback": feedback.dict() if feedback else None,
                            "timestamp": result.get("timestamp")
                        })
                
                # Download buttons
                st.divider()
                col_dl1, col_dl2, col_dl3 = st.columns(3)
                
                with col_dl1:
                    report_text = f"# {topic}\n\n{report.introduction}\n\n## Key Findings\n" + "\n".join([f"{i+1}. {f}" for i, f in enumerate(report.key_findings)]) + f"\n\n## Conclusion\n{report.conclusion}\n\n## Sources\n" + "\n".join(report.sources)
                    st.download_button("📥 Download Report (TXT)", report_text, file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                
                with col_dl2:
                    st.download_button("📥 Download Report (JSON)", json.dumps(result.get("report_dict", {}), indent=2), file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                
                with col_dl3:
                    st.link_button("🔗 View Checkpoint", "file:///" + os.path.abspath(".") if save_checkpoint else "#", disabled=not save_checkpoint)
                
            else:
                st.warning("⚠️ Pipeline completed but no report was generated. Check quota or try again.")
                
    except Exception as e:
        st.error(f"❌ Pipeline failed: {str(e)}")
        st.info("💡 Tip: You may have hit API quota. Try again tomorrow or check your .env file.")

elif run_button and not topic:
    st.warning("⚠️ Please enter a research topic first")

# Footer
st.divider()
st.caption("""
**How it works:** Search Agent (Tavily) → Reader Agent (Web Scraping) → Writer Agent (Gemini) → Critic Agent (Gemini)  
*Powered by Google Gemini 2.5 Flash, LangChain, and Tavily API*
""")