from flask import Flask, render_template, request
from summarizer import summarize_text
from recommender import get_recommendations
from feedback import save_feedback

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    summary = ""
    recommendations = []
    feedback = ""
    
    if request.m# app.py
from flask import Flask, render_template, request, redirect, url_for
from summarizer import summarize_text
from recommender import get_recommendations
from feedback import save_feedback

app = Flask(__name__)
LAST_SUMMARY = {"text": ""}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "summarize":
            input_text = request.form.get("text", "")
            summary = summarize_text(input_text)  # or style="paragraph"/"bullets"
            LAST_SUMMARY["text"] = summary
            return redirect(url_for("index"))
        elif action == "feedback":
            fb = request.form.get("feedback_text", "")
            save_feedback(LAST_SUMMARY.get("text",""), fb)
            return redirect(url_for("index"))

    summary = LAST_SUMMARY.get("text", "")
    recs = get_recommendations(summary) if summary else []
    return render_template("index.html", summary=summary, recommendations=recs)

if __name__ == "__main__":
    app.run(debug=True)
ethod == "POST":
        if "text" in request.form:
            input_text = request.form["text"]
            summary = summarize_text(input_text)
            recommendations = get_recommendations(input_text)
        elif "feedback" in request.form:
            feedback = request.form["feedback"]
            save_feedback(feedback)
    
    return render_template("index.html", summary=summary, recommendations=recommendations, feedback=feedback)

if __name__ == "__main__":
    app.run(debug=True)
