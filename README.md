# 🔍 Multi-Agent Research System

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://multi-agent-research-system-qdoyjgqgemonvxswd6ejwh.streamlit.app)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-green.svg)](https://www.langchain.com/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange.svg)](https://deepmind.google/technologies/gemini/)

> **4 specialized AI agents collaborate to research any topic - fully autonomous**

## 🎯 Live Demo

**Try it yourself:** [multi-agent-research-system.streamlit.app](https://multi-agent-research-system-qdoyjgqgemonvxswd6ejwh.streamlit.app)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USER INPUT: "impact of war on stock market"      │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 1: SEARCH AGENT                                              │
│  • Uses Tavily API to search the web                                │
│  • Returns 5 authoritative sources with titles, URLs & snippets     │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 2: READER AGENT                                              │
│  • Extracts URLs from search results                                │
│  • Scrapes top 2 URLs in parallel (async)                          │
│  • Cleans HTML and extracts main content                           │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 3: WRITER AGENT                                              │
│  • Gemini 2.5 Flash generates structured report                     │
│  • Output: Introduction + Key Findings + Conclusion + Sources       │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AGENT 4: CRITIC AGENT                                              │
│  • Evaluates report quality                                         │
│  • Returns: Score (0-10) + Strengths + Improvements + Verdict       │
└─────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FINAL OUTPUT: Report + Score + Critique          │
└─────────────────────────────────────────────────────────────────────┘
```

## 🤖 Agents Overview

| Agent | Role | Tools Used |
|-------|------|------------|
| 🔍 **Search** | Finds authoritative sources | Tavily API |
| 📖 **Reader** | Scrapes and extracts content | requests, BeautifulSoup |
| ✍️ **Writer** | Generates structured reports | Gemini 2.5 Flash |
| 🎯 **Critic** | Evaluates quality (0-10) | Gemini 2.5 Flash |

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Agent Orchestration** | LangChain |
| **LLM** | Google Gemini 2.5 Flash |
| **Web Search** | Tavily API |
| **Web Scraping** | requests + BeautifulSoup |
| **UI** | Streamlit |
| **Structured Output** | Pydantic |
| **Async Processing** | aiohttp |
| **Deployment** | Streamlit Cloud |

## 📊 Features

- ✅ **Multi-Agent Collaboration** - 4 specialized agents work together
- ✅ **Tool Calling** - Agents use web search and scraping tools
- ✅ **Self-Critique** - Agent evaluates its own output with 0-10 scoring
- ✅ **Parallel Processing** - Async scraping (2x faster)
- ✅ **Rate Limiting** - Prevents API quota exhaustion
- ✅ **Structured Output** - Pydantic models for reliable parsing
- ✅ **Checkpoint System** - Saves progress for debugging
- ✅ **Beautiful UI** - Professional dashboard with real-time updates
- ✅ **Export Options** - Download reports as Markdown or JSON

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [Tavily API Key](https://tavily.com/) (free tier available)
- [Google AI Studio API Key](https://aistudio.google.com/) (free tier: 20 requests/day)

### Installation

```bash
# Clone the repository
git clone https://github.com/VikasPatil64/multi-agent-research-system.git
cd multi-agent-research-system

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API keys
echo "GOOGLE_API_KEY=your_key_here" > .env
echo "TAVILY_API_KEY=your_key_here" >> .env

# Run the app
streamlit run ui_streamlit.py
```

## 📁 Project Structure

```
multi-agent-research-system/
├── agents.py              # Agent definitions (Search, Reader, Writer, Critic)
├── pipeline.py            # Orchestration logic
├── tools.py               # Web search & scraping tools
├── utils.py               # Helper functions (URL extraction, formatting)
├── rate_limiter.py        # API quota management
├── ui_streamlit.py        # Streamlit frontend
├── requirements.txt       # Dependencies
└── .env                   # API keys (gitignored)
```

## 📈 Sample Output

### Report Preview
```
# Research Report: Impact of AI on Job Market

## Introduction
Artificial Intelligence is transforming the job market at an unprecedented pace...

## Key Findings
1. AI is creating new job categories with 450% growth since 2020
2. Routine cognitive tasks face 70-80% automation potential
3. Companies investing in AI training see 40% higher retention

## Conclusion
AI will reshape rather than eliminate jobs through proactive adaptation...
```

### Critic Feedback
```
Score: 8.2/10
Verdict: Excellent analysis with concrete data points

Strengths:
✓ Strong data backing
✓ Balanced perspective
✓ Current statistics

Areas to Improve:
⚠️ Add regional variations
⚠️ Include industry-specific examples
```

## 🔄 How It Works

1. **User inputs** a research topic
2. **Search Agent** finds 5 authoritative sources via Tavily
3. **Reader Agent** scrapes top 2 URLs in parallel
4. **Writer Agent** generates structured report using Gemini
5. **Critic Agent** evaluates report quality (0-10 score)
6. **User receives** report + critique + download options

## ⚡ Performance

| Metric | Value |
|--------|-------|
| Search time | ~2 seconds |
| Scrape time (parallel) | ~2-3 seconds |
| Report generation | ~3-4 seconds |
| Critique | ~2 seconds |
| **Total** | **~10-12 seconds** |

## 🚧 Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| API rate limits | Custom rate limiter with daily quota tracking |
| URL extraction | Regex patterns to parse agent responses |
| Scraping latency | Async parallel HTTP requests |
| Token limits | Dynamic truncation with tiktoken |
| Structured output | Pydantic models for reliable parsing |

## 🎯 Future Improvements

- [ ] Add Redis caching for repeated queries
- [ ] Implement RAG for source-grounded responses
- [ ] Add support for PDF/document uploads
- [ ] Fine-tune critic for domain-specific evaluation
- [ ] Add user feedback loop for continuous improvement
- [ ] Deploy as Docker container with API endpoints

## 📄 License

MIT License - feel free to use, modify, and distribute!

## 🙏 Acknowledgments

- [LangChain](https://www.langchain.com/) for agent orchestration
- [Google Gemini](https://deepmind.google/technologies/gemini/) for LLM capabilities
- [Tavily](https://tavily.com/) for search API
- [Streamlit](https://streamlit.io/) for beautiful UI

## 📞 Connect

**Vikas Patil**

[![GitHub](https://img.shields.io/badge/GitHub-VikasPatil64-181717?style=flat&logo=github)](https://github.com/VikasPatil64)

---

⭐ If you found this project helpful, please give it a star on GitHub!
