# # agents/executor.py
from tools.web_scraper import WebScraper
from tools.selenium_tool import SeleniumTool
from tools.scraping_strategy import ScrapingStrategyRouter
from tools.memory_tool import MemoryTool
from llm.groq_client import GroqClient
from tools.content_extractor import extract_headlines, fetch_articles
from tools.content_extractor import extract_headlines
from tools.llm_preprocessor import prepare_llm_text
from tools.llm_extractor import extract_headlines_with_llm

class ExecutorAgent:
    def __init__(self):
        self.web = WebScraper()
        self.selenium = SeleniumTool()
        self.router = ScrapingStrategyRouter(self.web, self.selenium)
        self.memory = MemoryTool()
        self.llm = GroqClient()


    

    def execute(self, step: str):
        step_lower = step.lower()
        MIN_HEADLINES = 3

        if "fetch" in step_lower or "scrape" in step_lower:
            url = step.split()[-1]
            html = self.router.fetch(url)
            # self.memory.store(data)
            self.memory.store({"type": "html", "data": html})

            return html


        if "extract headlines" in step_lower:
            item = self.memory.retrieve_latest()

            if item is None:
                raise RuntimeError("No data in memory")

            if item["type"] == "html":
                html = item["data"]
            else:
                # Already processed or non-HTML → send to LLM path
                text = item["data"]
                headlines = self.llm.extract_headlines(text)
                self.memory.store({"type": "headlines", "data": headlines})
                return headlines
        
            # html = self.memory.retrieve_latest()

            # # 1️⃣ deterministic attempt
            # headlines = extract_headlines(html)

            # if len(headlines) >= MIN_HEADLINES:
            #     self.memory.store(headlines)
            #     return headlines

            # 2️⃣ fallback to LLM
            print("[Executor] Falling back to LLM-based extraction")

            llm_text = prepare_llm_text(html)
            headlines = extract_headlines_with_llm(
                llm_text,
                self.llm
            )

            self.memory.store({
                    "type": "headlines",
                    "data": headlines
                })

            return headlines

        
        
        if "summarize" in step_lower:

            item = self.memory.retrieve_latest()

            if item["type"] == "headlines":
                headlines = item["data"]

                if not headlines:
                    raise RuntimeError("No headlines to summarize")

                text = "\n".join(str(h) for h in headlines)

            else:
                text = prepare_llm_text(item["data"])

            summary = self.llm.ask(
        f"Summarize the following headlines into two sentences:\n{text}"
    )

            self.memory.store({
                "type": "summary",
                "data": summary
            })


            return summary
        
            # text = self.memory.retrieve_latest()
            # return self.llm.ask(f"Summarize:\n{text}")
        

        # --- FETCH STEP ---
        # if step_lower.startswith("fetch"):
        #     url = step.split(" ", 1)[1]
        #     # Phase 1: cheap fetch
        #     html = self.web.fetch(url)

        #     # Decide strategy based on content
        #     strategy = self.router.decide(html)

        #     if strategy == "selenium":
        #         print("[Executor] Escalating to Selenium for:", url)
        #         html = self.selenium.fetch(url)
        #     else:
        #         print("[Executor] Static HTML sufficient for:", url)

        #     self.memory.store(html)
        #     return html

        # --- SUMMARIZE ---
        # if "summarize" in step_lower:
        #     text = self.memory.retrieve_latest()
        #     return self.llm.ask(
        #         f"Summarize the following content:\n\n{text}"
        #     )

        # --- STORE ---
        if "store" in step_lower:
            # self.memory.store(step)
            self.memory.store({
                    "type": "step",
                    "data": step
                })      
            return "Stored in memory"
        

        # elif "parse html" in step_lower:
        #     html = self.memory.retrieve_latest()
        #     return html   # parsing is implicit for now

        # elif "extract all headlines" in step_lower:
        #     html = self.memory.retrieve_latest()
        #     headlines = extract_headlines(html)
        #     self.memory.store(headlines)
        #     return headlines

        # elif "extract article content" in step_lower:
        #     headlines = self.memory.retrieve_latest()
        #     articles = fetch_articles(headlines)
        #     self.memory.store(articles)
        #     return articles

        return f"Executed: {step}"





# import re
# import time
# import json
# from pathlib import Path
# from typing import Any, List, Optional

# from tools.web_scraper import WebScraper
# from tools.selenium_tool import SeleniumTool
# from tools.api_caller import APICaller
# from tools.file_manager import FileManager
# from tools.memory_tool import MemoryTool

# # optional Groq client; memory_tool imports GroqClient internally if available
# try:
#     from llm.groq_client import GroqClient
# except Exception:
#     GroqClient = None

# WORK_DIR = Path("work")
# WORK_DIR.mkdir(parents=True, exist_ok=True)

# class ExecutorAgent:
#     """
#     ExecutorAgent: receives a single step string and executes it.
#     The step may contain a URL placeholder {url} — the caller should replace it before calling.
#     """

#     def __init__(self):
#         self.scraper = WebScraper()
#         self.selenium = SeleniumTool()
#         self.api = APICaller()
#         self.files = FileManager()
#         self.memory = MemoryTool()
#         self.llm = None
#         if GroqClient:
#             try:
#                 self.llm = GroqClient()
#             except Exception:
#                 self.llm = None

#         # transient cache for last scraped data (and persisted to work/last_hn.json by scraper helpers)
#         self._last_headlines: Optional[List[str]] = None

#     # --------------------
#     # Utilities
#     # --------------------
#     def _save_last(self, key: str, data: Any):
#         path = WORK_DIR / f"last_{key}.json"
#         try:
#             with open(path, "w", encoding="utf-8") as f:
#                 json.dump({"ts": time.time(), "data": data}, f, ensure_ascii=False, indent=2)
#         except Exception:
#             pass

#     def _load_last(self, key: str):
#         path = WORK_DIR / f"last_{key}.json"
#         try:
#             with open(path, "r", encoding="utf-8") as f:
#                 j = json.load(f)
#                 return j.get("data")
#         except Exception:
#             return None

#     def _local_summarize(self, items: List[str]) -> str:
#         if not items:
#             return "No content to summarize."
#         top = items[:8]
#         joined = "; ".join(top)
#         short = top[0] if top else ""
#         return f"{joined}\n\nIn short: {short} and {len(items)-1 if len(items)>1 else 0} other headlines."

#     # --------------------
#     # Hacker News helpers (stable)
#     # --------------------
#     def scrape_hackernews_api(self, limit: int = 10) -> List[str]:
#         try:
#             import requests
#             top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
#             r = requests.get(top_url, timeout=8)
#             r.raise_for_status()
#             ids = r.json() or []
#             titles = []
#             for idx in ids[:limit]:
#                 try:
#                     item_url = f"https://hacker-news.firebaseio.com/v0/item/{idx}.json"
#                     ir = requests.get(item_url, timeout=6)
#                     ir.raise_for_status()
#                     item = ir.json()
#                     if item and "title" in item:
#                         titles.append(item["title"])
#                 except Exception:
#                     continue
#             self._save_last("hn", titles)
#             return titles
#         except Exception:
#             # fallback to static scraping using WebScraper
#             try:
#                 titles = self.scraper.scrape_hackernews()
#                 self._save_last("hn", titles)
#                 return titles
#             except Exception:
#                 return []

#     # --------------------
#     # Core execute interface
#     # --------------------
#     def execute(self, step: str) -> Any:
#         """
#         Execute a single planner step and return a structured result (list/dict/string).
#         """
#         if not isinstance(step, str):
#             return {"error": "invalid_step"}

#         s = step.strip().lower()

#         # --- Hacker News specific ---
#         if "hacker news" in s or ("news.ycombinator" in s) or ("top headlines" in s and "hacker" in s):
#             # Use stable HN API scraper
#             titles = self.scrape_hackernews_api(limit=10)
#             if titles:
#                 # store in memory as newline-joined string
#                 self.memory.store("\n".join(titles))
#                 return titles
#             return []

#         # --- Fetch a URL (explicit fetch) ---
#         if s.startswith("fetch ") or "fetch the webpage at " in s or re.search(r'https?://', step):
#             # try to extract URL
#             url = self._extract_url(step)
#             if url:
#                 # prefer requests first
#                 try:
#                     html = self.scraper.fetch(url)
#                     parsed = self.scraper.parse(html) if hasattr(self.scraper, "parse") else html
#                     # store parsed if list-like
#                     if isinstance(parsed, list) and parsed:
#                         self._save_last("generic", parsed)
#                         self.memory.store("\n".join([str(x) for x in parsed]))
#                         return parsed
#                     # persist raw html if parser not available
#                     self._save_last("raw_html", html)
#                     return html
#                 except Exception:
#                     # fallback to selenium
#                     try:
#                         html_s = self.selenium.scrape_dynamic(url)
#                         parsed = self.scraper.parse(html_s) if hasattr(self.scraper, "parse") else html_s
#                         if isinstance(parsed, list) and parsed:
#                             self._save_last("generic", parsed)
#                             self.memory.store("\n".join([str(x) for x in parsed]))
#                             return parsed
#                         self._save_last("raw_html", html_s)
#                         return html_s
#                     except Exception as e:
#                         return {"error": f"fetch_failed: {e}"}
#             else:
#                 return {"error": "no_url_found"}

#         # --- Parse / Extract headlines from last fetch ---
#         if "parse" in s or "extract" in s or "headline" in s:
#             # prefer persisted last_generic or last_raw
#             parsed = self._load_last("generic")
#             if parsed:
#                 # ensure memory updated
#                 try:
#                     if isinstance(parsed, list):
#                         self.memory.store("\n".join([str(x) for x in parsed]))
#                     else:
#                         self.memory.store(str(parsed))
#                 except Exception:
#                     pass
#                 return parsed
#             # fallback: attempt HN scrape
#             hn = self._load_last("hn")
#             if hn:
#                 self.memory.store("\n".join(hn))
#                 return hn
#             # final fallback: try scraping HN
#             return self.scrape_hackernews_api(10)

#         # --- Store into memory (explicit) ---
#         if "store" in s and "memory" in s:
#             # if step contains a URL or explicit payload, try to pull it
#             payload = None
#             # if last_generic exists use it
#             last = self._load_last("generic") or self._load_last("hn")
#             if last:
#                 payload = last
#             if payload:
#                 try:
#                     if isinstance(payload, list):
#                         text = "\n".join([str(x) for x in payload])
#                     else:
#                         text = str(payload)
#                     self.memory.store(text)
#                     return "Memory stored."
#                 except Exception as e:
#                     return {"error": f"memory_store_failed: {e}"}
#             return "Memory stored (empty)."

#         # --- Summarize ---
#         if "summarize" in s or "final report" in s or "two-sentence" in s or "two sentence" in s:
#             # retrieve latest memory
#             rows = self.memory.retrieve_latest(limit=1)
#             text = ""
#             if rows:
#                 text = rows[0][0] if isinstance(rows[0], (list, tuple)) else str(rows[0])
#             # fallback to cached lists
#             if not text:
#                 cached = self._load_last("generic") or self._load_last("hn")
#                 if isinstance(cached, list):
#                     text = "\n".join([str(x) for x in cached])
#                 elif cached:
#                     text = str(cached)
#             # try LLM summarizer
#             if self.llm:
#                 try:
#                     prompt = f"Summarize the following content into a concise 2-sentence report:\n\n{text}"
#                     res = self.llm.ask(prompt)
#                     if res and not str(res).startswith("[Groq Error]"):
#                         # store summary
#                         try:
#                             self.memory.store(res)
#                         except Exception:
#                             pass
#                         return res
#                 except Exception:
#                     pass
                
#             # local fallback
#             if text:
#                 summary = self._local_summarize(text.splitlines())
#                 try:
#                     self.memory.store(summary)
#                 except Exception:
#                     pass
#                 return summary
#             return "No content to summarize."

#         # --- Format / Return report ---
#         if "format" in s or "return" in s or "final" in s:
#             # assemble report from memory & cached lists
#             rows = self.memory.retrieve_latest(limit=5)
#             texts = [r[0] for r in rows] if rows else []
#             report = {
#                 "summary": texts[0] if texts else "",
#                 "headlines": self._load_last("hn") or self._load_last("generic") or []
#             }
#             return report

#         # --- Default fallback: echo ---
#         return f"Executed: {step}"

#     def _extract_url(self, text: str) -> Optional[str]:
#         m = re.search(r'(https?://[^\s,;]+)', text)
#         return m.group(0) if m else None
