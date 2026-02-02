import json
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def dashboard():
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    return render_template(
        "index.html",
        lesson=data["lesson"],
        avg_attention=data["avg_attention"],
        overview=data["overview"],
        blocks=data["blocks"],
        attention_time=data["attention_time"],
        attention_distribution=data["attention_distribution"],
        max_attention=data["max_attention"],
        min_attention=data["min_attention"],
        suggestions=[
            "Add a short interactive question",
            "Change teaching pace",
            "Use visual examples",
            "Engage back-row students",
            "Consider a short break"
        ]
    )

if __name__ == "__main__":
    app.run(debug=True)