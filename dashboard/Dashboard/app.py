from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def dashboard():
    lesson_name = "Mathematics – Class 8B"
    lesson_time = "08:15 – 09:50"
    avg_attention = 72

    overview = {
        "Total Students": 18,
        "Attentive Students": 12,
        "Distracted Students": 6
    }

    attention_time = [70, 75, 72, 68, 74, 70]

    attention_distribution = {
        "High": 10,
        "Medium": 5,
        "Low": 3
    }

    suggestions = [
        "Consider a short interactive question",
        "Attention dropped in the back of the class",
        "A short break may improve focus"
    ]

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

if __name__ == "__main__":
    app.run(debug=True)