# extractor/llm_extract.py
import os
import json
import copy
import re
from typing import List, Dict, Any
from pydantic import ValidationError
from extractor.schema import ExtractionResult
from openai import OpenAI
from dotenv import load_dotenv
import time
import random


# Load env vars from .env
load_dotenv()

# Initialize OpenRouter client
api_key = os.getenv("OPENROUTER_API_KEY")
print("Using API key:", api_key)    # Debug print (optional)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

def safe_json_parse(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract first JSON-like block
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            fixed = m.group(0)
            fixed = fixed.replace("'", '"')
            fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
            try:
                return json.loads(fixed)
            except Exception as e:
                print(f"[JSON PARSE ERROR] Failed after cleanup: {e}")
                return {"doc_type": "unknown", "fields": [], "overall_confidence": 0.0, "qa": {"passed_rules": [], "failed_rules": [], "notes": "json parse failed"}}
        return {"doc_type": "unknown", "fields": [], "overall_confidence": 0.0, "qa": {"passed_rules": [], "failed_rules": [], "notes": "no json detected"}}

        
def call_llm(messages, model="openai/gpt-oss-20b:free", temperature=0.0, max_tokens=1200, retries=3):
    """Call the LLM via OpenRouter/OpenAI client with retries (Windows-safe)."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                extra_headers={
                    "HTTP-Referer": "<YOUR_SITE_URL>",
                    "X-Title": "<YOUR_SITE_NAME>",
                },
            )
            return completion.choices[0].message.content

        except Exception as e:
            last_err = e
            print(f"[LLM ERROR] Attempt {attempt} failed: {e}")
            # backoff between retries
            time.sleep(random.uniform(1, 3))

    # After all retries fail
    raise RuntimeError(f"LLM call failed after {retries} retries: {last_err}")

def build_prompt(ocr_text, ocr_tokens, expected_fields, doc_type=None):
    """Return messages for the chat model. Keep instructions strict: return JSON only."""
    system = {
        "role": "system",
        "content": (
            "You are a document parser. "
            "Given OCR text and bounding boxes, extract the requested fields exactly in JSON. "
            "Output MUST be valid JSON only - no explanatory text.\n"
        )
    }
    hint = f"\nDOC_TYPE_HINT: {doc_type}" if doc_type else ""
    human = {
        "role": "user",
        "content": (
            "OCR_TEXT:\n" + ocr_text + "\n\n"
            "OCR_TOKENS (list of token objects: text, conf, bbox):\n" + json.dumps(ocr_tokens) + "\n\n"
            "EXTRACT FIELDS: " + json.dumps(expected_fields) +
            hint +
            "\n\nReturn JSON with keys: "
            "doc_type, fields (list of {name, value, confidence, source:{page,bbox}}), "
            "line_items (if present), overall_confidence (0..1), "
            "qa (passed_rules, failed_rules, notes)."
        )
    }
    return [system, human]

def extract_with_llm(ocr_text, ocr_tokens, expected_fields, n_consistency=3, doc_type=None):
    runs = []
    for i in range(n_consistency):
        messages = build_prompt(ocr_text, ocr_tokens, expected_fields, doc_type=doc_type)
        temp = 0.0 if n_consistency == 1 else 0.3
        raw = call_llm(messages, temperature=temp)
        j = safe_json_parse(raw)
        runs.append(j)

    result = copy.deepcopy(runs[0])
    result["_llm_runs"] = runs
    # If model didn’t set doc_type, backfill with the router hint
    if result and doc_type and not result.get("doc_type"):
        result["doc_type"] = doc_type
    return result
