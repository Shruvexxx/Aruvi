# rss_ingest.py
import os, json, time, hashlib, re
from datetime import datetime
from urllib.parse import urlparse
import feedparser
import trafilatura

CORPUS_DIR = "corpus"
FEEDS_CFG = "feeds.json"
USER_AGENT = "ARUVI-Reader/1.0 (+https://example.com)"

os.makedirs(CORPUS_DIR, exist_ok=True)

def _slugify(text: str, maxlen=80):
    text = re.sub(r"[^\w\s-]", "", text, flags=re.U).strip().lower()
    text = re.sub(r"[-\s]+", "-", text)
    return text[:maxlen] or "article"

def _url_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]

def _save_doc(doc: dict):
    title = doc.get("title") or "untitled"
    host = urlparse(doc["url"]).netloc.replace("www.", "")
    ts = doc.get("published") or int(time.time())
    if isinstance(ts, str):
        try:
            # try parse RFC822/ISO formats and get epoch
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            ts = int(dt.timestamp())
        except Exception:
            ts = int(time.time())
    name = f"{_slugify(title)}_{host}_{ts}_{_url_id(doc['url'])}.json"
    path = os.path.join(CORPUS_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    return path

def _already_ingested(url: str) -> bool:
    uid = _url_id(url)
    for fn in os.listdir(CORPUS_DIR):
        if fn.endswith(".json") and uid in fn:
            return True
    return False

def _extract(url: str) -> str:
    # Respectful fetching (trafilatura uses requests under the hood)
    downloaded = trafilatura.fetch_url(url, no_ssl=True, user_agent=USER_AGENT)
    if not downloaded:
        return ""
    text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
    return (text or "").strip()

def main():
    with open(FEEDS_CFG, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    max_per_feed = int(cfg.get("max_per_feed", 25))
    feeds = cfg.get("feeds", [])

    total_new = 0
    for feed_url in feeds:
        d = feedparser.parse(feed_url)
        entries = d.entries[:max_per_feed]
        for e in entries:
            link = getattr(e, "link", None)
            title = getattr(e, "title", "")
            if not link or _already_ingested(link):
                continue

            # Published date best-effort
            published_ts = None
            if getattr(e, "published", None):
                published_ts = e.published
            elif getattr(e, "updated", None):
                published_ts = e.updated

            text = _extract(link)
            if not text:
                # Skip if we cannot extract main text
                continue

            doc = {
                "id": _url_id(link),
                "title": title,
                "url": link,
                "published": published_ts,
                "source": feed_url,
                "text": text
            }
            _save_doc(doc)
            total_new += 1

            # Be polite: small delay between page fetches
            time.sleep(0.8)

    print(f"Ingest complete. New documents: {total_new}")

if __name__ == "__main__":
    main()
