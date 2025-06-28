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
    
    if request.method == "POST":
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
