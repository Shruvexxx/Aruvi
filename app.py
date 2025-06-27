from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    summary = ""
    if request.method == "POST":
        text = request.form["text"]
        summary = f"You entered: {text}"
    return render_template("index.html", summary=summary)

if __name__ == "__main__":
    app.run(debug=True)
