"""
Multi-Agent Research System - Enhanced UI
Run with: streamlit run ui_streamlit.py
"""

import streamlit as st
import asyncio
import json
from datetime import datetime
import sys
import os
import time
import matplotlib.pyplot as plt
import pandas as pd

# Import your pipeline
from pipeline import run_research_pipeline
from rate_limiter import get_remaining_quota

# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title="Multi-Agent Research System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CUSTOM CSS - CLEAN PROFESSIONAL THEME ==========
st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1f2937;
        font-weight: 600;
    }
    
    /* Agent Cards */
    .agent-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .agent-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
        border-color: #6366f1;
        background: white;
    }
    
    .agent-icon {
        font-size: 2.5rem;
        margin-bottom: 0.75rem;
    }
    
    .agent-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 0.25rem;
    }
    
    .agent-role {
        font-size: 0.8rem;
        color: #6b7280;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    
    /* Example buttons */
    .example-btn {
        background-color: #f3f4f6;
        color: #374151;
        border: 1px solid #e5e7eb;
        border-radius: 2rem;
        padding: 0.4rem 1rem;
        font-size: 0.8rem;
        transition: all 0.2s ease;
        cursor: pointer;
        display: inline-block;
        margin: 0.25rem;
    }
    
    .example-btn:hover {
        background-color: #6366f1;
        color: white;
        border-color: #6366f1;
        transform: translateY(-2px);
    }
    
    /* Status messages */
    .status-info {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    .status-success {
        background-color: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    .status-warning {
        background-color: #fefce8;
        border-left: 4px solid #eab308;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Score display */
    .score-high {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1rem;
        border-radius: 1rem;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
    }
    
    .score-mid {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 1rem;
        border-radius: 1rem;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
    }
    
    .score-low {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 1rem;
        border-radius: 1rem;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
    }
    
    /* Report cards */
    .report-card {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    
    .finding-item {
        background: #f8fafc;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 3px solid #6366f1;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f8fafc;
    }
    
    /* Metrics */
    .metric-card {
        background: white;
        border-radius: 0.75rem;
        padding: 1rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #6b7280;
        font-size: 0.8rem;
        border-top: 1px solid #e2e8f0;
        margin-top: 2rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .agent-card {
            padding: 1rem;
        }
        .agent-icon {
            font-size: 1.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### 🤖 Agent Team")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="agent-card">
            <div class="agent-icon">🔍</div>
            <div class="agent-name">Search</div>
            <div class="agent-role">Finds 5 authoritative sources</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="agent-card">
            <div class="agent-icon">✍️</div>
            <div class="agent-name">Writer</div>
            <div class="agent-role">Generates structured report</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="agent-card">
            <div class="agent-icon">📖</div>
            <div class="agent-name">Reader</div>
            <div class="agent-role">Extracts web content</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="agent-card">
            <div class="agent-icon">🎯</div>
            <div class="agent-name">Critic</div>
            <div class="agent-role">Evaluates quality (0-10)</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Quota display
    remaining = get_remaining_quota()
    if remaining > 10:
        st.success(f"📊 API Calls Remaining: **{remaining}/18**")
    elif remaining > 5:
        st.warning(f"⚠️ API Calls Remaining: **{remaining}/18**")
    else:
        st.error(f"🔴 API Calls Remaining: **{remaining}/18**")
    
    st.divider()
    
    # Research History (mock for now)
    st.markdown("### 📜 Quick Tips")
    st.caption("💡 **For better results:**")
    st.caption("• Be specific in your topic")
    st.caption("• Add year for recent data")
    st.caption("• Compare vs for analysis")
    
    st.divider()
    
    # Example topics
    st.markdown("### 🎯 Try these:")
    example_topics = [
        "Impact of AI on healthcare jobs",
        "Renewable energy trends 2024",
        "Effects of remote work on productivity",
        "Future of electric vehicles in India",
        "Mental health in tech industry"
    ]
    
    for topic_ex in example_topics:
        if st.button(f"📌 {topic_ex[:35]}...", key=topic_ex, use_container_width=True):
            st.session_state.topic_input = topic_ex
            st.rerun()

# ========== MAIN CONTENT ==========
st.markdown("# 🔍 Multi-Agent Research System")
st.markdown("*4 specialized AI agents collaborate to research any topic - fully autonomous*")

# Topic input
topic = st.text_input(
    "**Enter your research topic:**",
    value=st.session_state.get("topic_input", ""),
    placeholder="e.g., Impact of war on stock market and Indian economy",
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
col1, col2, col3 = st.columns([1.5, 2, 1.5])
with col2:
    run_button = st.button("🚀 Start Research", use_container_width=True, disabled=not topic)

# ========== PIPELINE EXECUTION ==========
if run_button and topic:
    # Progress tracking
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    result_placeholder = st.empty()
    
    try:
        # Step 1: Search
        status_placeholder.markdown('<div class="status-info">🔍 <strong>Agent 1/4: Search</strong> - Finding authoritative sources...</div>', unsafe_allow_html=True)
        progress_bar = progress_placeholder.progress(10, text="Searching the web...")
        
        # Step 2: Read
        status_placeholder.markdown('<div class="status-info">📖 <strong>Agent 2/4: Reader</strong> - Scraping and extracting content...</div>', unsafe_allow_html=True)
        progress_bar.progress(30, text="Reading web pages...")
        
        # Step 3: Write
        status_placeholder.markdown('<div class="status-info">✍️ <strong>Agent 3/4: Writer</strong> - Generating structured report...</div>', unsafe_allow_html=True)
        progress_bar.progress(60, text="Writing report...")
        
        # Step 4: Critique
        status_placeholder.markdown('<div class="status-info">🎯 <strong>Agent 4/4: Critic</strong> - Evaluating quality...</div>', unsafe_allow_html=True)
        progress_bar.progress(80, text="Critiquing...")
        
        # Run pipeline
        with st.spinner("🤖 Agents are analyzing (10-15 seconds)..."):
            result = run_research_pipeline(topic, save_checkpoint=save_checkpoint)
        
        progress_bar.progress(100, text="Complete!")
        
        if result.get("error"):
            status_placeholder.markdown('<div class="status-warning">⚠️ Pipeline completed with warnings</div>', unsafe_allow_html=True)
            st.warning(f"Note: {result['error']}")
        else:
            status_placeholder.markdown('<div class="status-success">✅ All agents completed successfully!</div>', unsafe_allow_html=True)
        
        # Display results
        report = result.get("report")
        feedback = result.get("feedback")
        
        if report and feedback:
            # Score styling
            score = feedback.score
            if score >= 7:
                score_class = "score-high"
            elif score >= 5:
                score_class = "score-mid"
            else:
                score_class = "score-low"
            
            # Two-column layout
            col1, col2 = st.columns([1.5, 1])
            
            with col1:
                st.markdown("## 📄 Research Report")
                
                with st.expander("📖 Introduction", expanded=True):
                    st.write(report.introduction)
                
                with st.expander("🔑 Key Findings", expanded=True):
                    for i, finding in enumerate(report.key_findings, 1):
                        st.markdown(f'<div class="finding-item"><strong>{i}.</strong> {finding}</div>', unsafe_allow_html=True)
                
                with st.expander("📝 Conclusion", expanded=True):
                    st.write(report.conclusion)
                
                with st.expander("🔗 Sources", expanded=False):
                    for source in report.sources:
                        st.markdown(f"- {source}")
            
            with col2:
                st.markdown("## 🎯 Critic Feedback")
                st.markdown(f'<div class="{score_class}">{score}/10</div>', unsafe_allow_html=True)
                st.info(f"**Verdict:** {feedback.verdict}")
                
                st.markdown("**✅ Strengths**")
                for s in feedback.strengths:
                    st.success(f"• {s}")
                
                st.markdown("**⚠️ Areas to Improve**")
                for i in feedback.improvements:
                    st.warning(f"• {i}")
                
                # Stats
                st.divider()
                st.markdown("**📊 Quick Stats**")
                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("URLs Found", len(result.get("urls_found", [])))
                with metric_col2:
                    st.metric("Sources Cited", len(report.sources))
            
            # Download section
            st.divider()
            st.markdown("### 📥 Export Results")
            
            dl_col1, dl_col2, dl_col3 = st.columns(3)
            
            with dl_col1:
                report_md = f"""# {topic}

## Introduction
{report.introduction}

## Key Findings
{chr(10).join([f"{i+1}. {f}" for i, f in enumerate(report.key_findings)])}

## Conclusion
{report.conclusion}

## Sources
{chr(10).join(report.sources)}

---
*Generated by Multi-Agent Research System on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
                st.download_button("📥 Download Markdown", report_md, file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
            
            with dl_col2:
                st.download_button("📋 Download JSON", json.dumps(report.dict(), indent=2), file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            with dl_col3:
                share_url = f"https://twitter.com/intent/tweet?text=Just researched '{topic[:60]}' using AI agents! Score: {score}/10"
                st.markdown(f'<a href="{share_url}" target="_blank" style="text-decoration: none;"><button style="width:100%; background:#1DA1F2; color:white; border:none; border-radius:0.5rem; padding:0.6rem;">🐦 Share on X</button></a>', unsafe_allow_html=True)
            
            # Raw JSON option
            if show_raw_json:
                with st.expander("📋 Raw JSON Output"):
                    st.json({
                        "topic": topic,
                        "urls_found": result.get("urls_found", []),
                        "report": report.dict(),
                        "feedback": feedback.dict(),
                        "timestamp": result.get("timestamp")
                    })
        
        else:
            st.warning("⚠️ No report generated. This may be due to API quota limits. Please try again later.")
            st.info("💡 **Tip:** Gemini free tier has 20 requests/day. Try again tomorrow morning (5:30 AM IST).")
    
    except Exception as e:
        st.error(f"❌ Pipeline error: {str(e)}")
        st.info("Please check your API keys or try again later.")

elif run_button and not topic:
    st.warning("⚠️ Please enter a research topic first")

# ========== FOOTER ==========
st.divider()
st.markdown("""
<div class="footer">
    <strong>How it works:</strong> Search Agent (Tavily) → Reader Agent (Web Scraping) → Writer Agent (Gemini) → Critic Agent (Gemini)<br>
    Powered by Google Gemini 2.5 Flash, LangChain, and Tavily API
</div>
""", unsafe_allow_html=True)