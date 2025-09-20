# feedback.py — send feedback to Google Sheets API
import os, requests

SHEETS_WEBAPP_URL = os.getenv(https://script.google.com/macros/s/AKfycbxdkgs261p9qWB1NHXWXHBmZMyuHpIWAmXF-kS6KAkJ5hhthcuo0NoHf1q2ulcKpRvWRA/exec)  # set this in env

def save_feedback(summary_text: str, feedback_text: str):
    if not SHEETS_WEBAPP_URL:
        print("Warning: FEEDBACK_SHEETS_URL not set; feedback not sent.")
        return

    payload = {
        "summary": (summary_text or "").strip(),
        "feedback": (feedback_text or "").strip()
    }
    try:
        r = requests.post(SHEETS_WEBAPP_URL, json=payload, timeout=10)
        if r.status_code != 200:
            print("Feedback POST failed:", r.text)
    except Exception as e:
        print("Feedback error:", e)

