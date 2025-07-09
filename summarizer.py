import requests

API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
headers = {"Authorization": "Bearer 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"}

def summarize_text(text):
    if not text.strip():
        return "No input provided."

    response = requests.post(API_URL, headers=headers, json={"inputs": text})
    
    if response.status_code == 200:
        return response.json()[0]["summary_text"]
    else:
        return "Error: Unable to summarize text. Try again later."
