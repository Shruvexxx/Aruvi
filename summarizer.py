# summarizer.py
import os, requests, re
from dotenv import load_dotenv

# Only load .env if it actually exists; avoid REPL/frame issues
if os.path.exists(".env"):
    load_dotenv(".env")

API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HF_TOKEN = os.getenv("HF_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

def summarize_text(text: str, max_length: int = 140, min_length: int = 40) -> str:
    text = (text or "").strip()
    if not text:
        return "No input provided."
    if not HF_TOKEN:
        # Dev fallback so the UI still works even if token not injected
        return text[:max_length] + ("..." if len(text) > max_length else "")

    payload = {
        "inputs": text,
        "parameters": {"max_length": max_length, "min_length": min_length, "do_sample": False},
        "options": {"wait_for_model": True, "use_cache": True}
    }

    try:
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
    except requests.Timeout:
        return "Error: Summarization timed out. Please try again."
    except requests.RequestException as e:
        return f"Error: Network issue: {e}"

    if r.status_code != 200:
        try:
            detail = r.json().get("error", r.text)
        except Exception:
            detail = r.text
        detail = re.sub(r"\s+", " ", detail).strip()
        return f"Error: Unable to summarize. ({r.status_code}) {detail}"

    try:
        return r.json()[0]["summary_text"].strip()
    except Exception:
        return "Error: Unexpected response from summarizer."
