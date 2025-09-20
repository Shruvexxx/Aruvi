# summarizer.py
import re
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

def summarize_text(text: str, sentence_count: int = 3) -> str:
    text = (text or "").strip()
    if not text:
        return "No input provided."

    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = TextRankSummarizer()
        summary = summarizer(parser.document, sentence_count)
        # Join selected sentences
        return " ".join(str(s) for s in summary)
    except Exception as e:
        # fallback: truncate
        return text.split(". ")[:sentence_count]
