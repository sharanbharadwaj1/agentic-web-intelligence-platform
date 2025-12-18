# llm/gemini_client.py
import time
import json
import traceback
import google.generativeai as genai
from config.settings import settings

# configure once (safe to call multiple times)
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except Exception:
    # ignore; some genai versions may not need configure or use env vars
    pass

class GeminiClient:
    def __init__(self, model_name: str = None):
        # default model name from settings (e.g. "gemini-2.0-flash")
        self.model_name = model_name or getattr(settings, "MODEL_NAME", None) or "gemini-2.0-flash"
        self.max_retries = 2
        self.retry_delay = 0.5

    def _call_variants(self, prompt: str, gen_kwargs: dict | None = None):
        """
        Try a series of common invocation variants on google.generativeai.
        Return the raw response object when successful.
        """
        gen_kwargs = gen_kwargs or {}
        attempts = []

        # Candidate call wrappers: each returns (ok:bool, response_or_error)
        def try_generate_text():
            try:
                # Some SDKs expose genai.generate_text(model=..., prompt=...)
                if hasattr(genai, "generate_text"):
                    return True, genai.generate_text(model=self.model_name, prompt=prompt, **gen_kwargs)
                # older variants: genai.generate_text(prompt=..., model=...)
                # but above covers typical shapes
            except Exception as e:
                return False, e
            return False, "not-available"

        def try_generate():
            try:
                # Some installations expose genai.generate(model=..., prompt=...)
                if hasattr(genai, "generate"):
                    return True, genai.generate(model=self.model_name, prompt=prompt, **gen_kwargs)
            except Exception as e:
                return False, e
            return False, "not-available"

        def try_text_create():
            try:
                # genai.TextGeneration.create(...)
                if hasattr(genai, "TextGeneration") and hasattr(genai.TextGeneration, "create"):
                    return True, genai.TextGeneration.create(model=self.model_name, prompt=prompt, **gen_kwargs)
            except Exception as e:
                return False, e
            return False, "not-available"

        def try_generations_create():
            try:
                # genai.generations.create(...)
                if hasattr(genai, "generations") and hasattr(genai.generations, "create"):
                    return True, genai.generations.create(model=self.model_name, input=prompt, **gen_kwargs)
            except Exception as e:
                return False, e
            return False, "not-available"

        def try_model_object():
            try:
                # genai.Model(...) or genai.GenerativeModel(...)
                if hasattr(genai, "Model"):
                    m = genai.Model(self.model_name)
                    if hasattr(m, "generate_text"):
                        return True, m.generate_text(prompt)
                    if hasattr(m, "generate"):
                        return True, m.generate(prompt)
                if hasattr(genai, "GenerativeModel"):
                    m = genai.GenerativeModel(self.model_name)
                    if hasattr(m, "generate_content"):
                        return True, m.generate_content(prompt)
            except Exception as e:
                return False, e
            return False, "not-available"

        # Order of attempts - covers most SDK variants
        candidates = [try_generate_text, try_text_create, try_generations_create, try_model_object, try_generate]

        for fn in candidates:
            ok, resp = fn()
            attempts.append((fn.__name__, ok, resp))
            if ok:
                return True, resp, attempts

        # none succeeded
        return False, attempts, attempts

    def _extract_text(self, resp):
        """
        Try common response shapes and extract a best-effort text string.
        """
        try:
            # direct str
            if resp is None:
                return ""
            # If it's already a string
            if isinstance(resp, str):
                return resp

            # Some responses have `.text`
            if hasattr(resp, "text"):
                try:
                    return resp.text
                except Exception:
                    pass

            # Some responses are mapping-like
            try:
                # dict-like with candidates/content
                if isinstance(resp, dict):
                    # common pattern: {"candidates": [{"content": "..."}, ...]}
                    if "candidates" in resp and isinstance(resp["candidates"], (list, tuple)) and resp["candidates"]:
                        c0 = resp["candidates"][0]
                        if isinstance(c0, dict) and ("content" in c0 or "text" in c0):
                            return str(c0.get("content") or c0.get("text") or "")
                    # some APIs use 'output' or 'content' fields
                    if "output" in resp:
                        out = resp["output"]
                        if isinstance(out, str):
                            return out
                        if isinstance(out, dict) and "content" in out:
                            return str(out["content"])
                    if "content" in resp:
                        return str(resp["content"])
                # object with 'candidates' attribute
                if hasattr(resp, "candidates"):
                    try:
                        cand = resp.candidates
                        # iterable of candidates
                        first = cand[0]
                        if hasattr(first, "content"):
                            return first.content
                        if isinstance(first, dict) and "content" in first:
                            return first["content"]
                    except Exception:
                        pass

                # some SDKs return nested 'results' with 'output' or 'content'
                if hasattr(resp, "results"):
                    try:
                        res0 = resp.results[0]
                        if hasattr(res0, "output"):
                            out = getattr(res0, "output")
                            if isinstance(out, str):
                                return out
                            # check blocks / content
                            if isinstance(out, (list, tuple)) and out:
                                first = out[0]
                                if hasattr(first, "text"):
                                    return first.text
                                if isinstance(first, dict) and "text" in first:
                                    return first["text"]
                    except Exception:
                        pass

                # fallback: try to convert to JSON string
                try:
                    return json.dumps(resp)
                except Exception:
                    return str(resp)
            except Exception:
                return str(resp)
        except Exception:
            return str(resp)

    def _safe_generate_once(self, prompt: str, gen_kwargs: dict | None = None):
        ok, resp, attempts = self._call_variants(prompt, gen_kwargs)
        if not ok:
            # resp contains attempts info
            # build helpful error message
            msg = "No supported genai invocation succeeded. Attempts:\n"
            for name, success, result in attempts:
                msg += f"- {name}: {'ok' if success else 'failed'}; resp={repr(result)}\n"
            raise RuntimeError(msg)
        # extract text
        text = self._extract_text(resp)
        return text, resp

    def _safe_generate(self, prompt: str, gen_kwargs: dict | None = None, retries: int | None = None):
        retries = self.max_retries if retries is None else retries
        last_exc = None
        for attempt in range(retries + 1):
            try:
                text, raw = self._safe_generate_once(prompt, gen_kwargs)
                # success
                return {"ok": True, "text": text, "raw": raw, "error": None}
            except Exception as e:
                last_exc = e
                time.sleep(self.retry_delay)
                continue
        # failed after retries
        return {"ok": False, "text": "", "raw": None, "error": str(last_exc)}

    def ask(self, prompt: str) -> str:
        """
        Simple text completion. Returns string (possibly an error string).
        """
        out = self._safe_generate(prompt)
        if not out["ok"]:
            return f"[Gemini Error] {out['error']}"
        return out["text"]

    def structured(self, prompt: str, schema: dict | None = None, max_retries: int = 1):
        """
        Try to obtain JSON-like output. Returns raw text (may be JSON or plain text).
        Caller should parse JSON if desired.
        """
        wrapped = prompt
        if schema:
            wrapped = prompt.strip() + "\n\nReturn ONLY valid JSON matching the requested schema. No extra explanation."
        out = self._safe_generate(wrapped, retries=max_retries)
        if not out["ok"]:
            raise RuntimeError(f"Gemini structured failed: {out['error']}")
        return out["text"]
