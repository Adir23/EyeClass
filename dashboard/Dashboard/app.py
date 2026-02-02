import json
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "eyeclass-secret"

@app.route("/start", methods=["GET", "POST"])
def start():
    if request.method == "POST":
        session["teacher"] = request.form["teacher"]
        session["class"] = request.form["class"]
        session["subject"] = request.form["subject"]
        session["lesson"] = request.form["lesson"]
        session["time"] = f'{request.form["start_time"]} – {request.form["end_time"]}'
        return redirect("/")
    return render_template("start.html")

@app.route("/")
def dashboard():
    required = ["teacher", "class", "subject", "lesson", "time"]
    if not all(k in session for k in required):
        return redirect("/start")

    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    data["lesson"]["name"] = f'{session["subject"]} – {session["class"]}'
    data["lesson"]["time"] = session["time"]

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/start")

if __name__ == "__main__":
    app.run(debug=True)