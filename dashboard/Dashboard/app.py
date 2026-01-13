import json
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def dashboard():
    # Open data json
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Unpack json
    lesson_name = data["lesson"]["name"]
    lesson_time = data["lesson"]["time"]
    avg_attention = data["avg_attention"]
    overview = data["overview"]
    attention_time = data["attention_time"]
    attention_distribution = data["attention_distribution"]

    suggestions = [
        "Consider a short interactive question",
        "Attention dropped in the back of the class",
        "A short break may improve focus",
        "Try assigning a class work",
        "Use visual aids to regain focus"
    ]

    # Render page
    return render_template(
        "index.html",
        lesson_name=lesson_name,
        lesson_time=lesson_time,
        avg_attention=avg_attention,
        overview=overview,
        attention_time=attention_time,
        attention_distribution=attention_distribution,
        suggestions=suggestions
    )

# Run dashboard
if __name__ == "__main__":
    app.run(debug=True)