# Agentic Web Intelligence Platform

A production-grade agentic AI system for dynamic web scraping, content extraction, summarization, and automation across static and JavaScript-rendered websites.

## Features
- Planner–Executor–Critic agent architecture
- Dynamic scraping strategy (static HTML vs JS-rendered)
- Deterministic extraction with LLM fallback
- Typed SQLite-backed agent memory
- Schema-validated LLM outputs
- Local-first, zero-cloud execution
- Automation via change detection and scheduling

## Tech Stack
- Python
- Groq LLM SDK (LLaMA family)
- BeautifulSoup, Requests
- Selenium (JS-rendered sites)
- SQLite
- Pydantic

## Example Use Case
```text
Input:
URL: https://timesofindia.indiatimes.com/india
Task: Extract top 10 headlines and summarize in two sentences

Output:
Clean headlines + concise summary
