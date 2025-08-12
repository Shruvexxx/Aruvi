# feedback.py
import csv, time, hashlib

CSV_PATH = "feedback.csv"

def _safe_csv_cell(s: str) -> str:
    if s and s[0] in ("=", "+", "-", "@"):
        return "'" + s
    return s

def save_feedback(summary_text: str, feedback_text: str):
    ts = int(time.time())
    sid = hashlib.sha1((summary_text or "").encode("utf-8")).hexdigest()[:12]
    headers = ["ts", "summary_id", "feedback_text"]
    row = [ts, sid, _safe_csv_cell(feedback_text or "")]
    need_header = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if need_header:
            w.writerow(headers)
        w.writerow(row)
