HEADLINE_EXTRACTION_PROMPT = """
You are a strict information extraction system.

From the text below:
- Extract AT MOST 10 headlines ONLY
- Each headline must be a single sentence
- Do NOT include duplicates
- Do NOT include explanations

Return JSON ONLY in this exact format:
{{
  "headlines": ["...", "..."]
}}

TEXT:
{text}
"""
