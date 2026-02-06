import os
import json
import random
import time
from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai

USE_GEMINI = False

app = Flask(__name__)
app.secret_key = "eyeclass-ultra-secret"

# --- CONFIGURATION ---
JSON_FOLDER = "JsonFilesData"
os.makedirs(JSON_FOLDER, exist_ok=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or "AIzaSyAK1FVwS6Zsw5Y061F3Db9TrSAY7jm45Uw"

has_ai = False
if GEMINI_API_KEY and USE_GEMINI:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        chat_model = genai.GenerativeModel('models/gemini-2.5-flash')
        has_ai = True
        print("✅ Gemini AI Connected Successfully!")
    except Exception as e:
        print(f"⚠️ AI Connection Error: {e}")
else:
    print("⚠️ Warning: No API Key found. AI features will use dummy data.")

# --- SMART CACHE SYSTEM ---
ai_cache = {
    "last_update": 0,
    "suggestions": [
        "Analyzing classroom dynamics...",
        "Waiting for more data points...",
        "AI insights will appear shortly."
    ]
}
AI_UPDATE_INTERVAL = 20


# --- HELPER FUNCTIONS ---

def generate_ai_insights(stats):
    """Sends class stats to Gemini and returns 3 short actionable insights."""
    if not has_ai:
        return ["⚠️ AI Offline", "Check API Key", "Using manual mode"]

    try:
        prompt = f"""
        You are an AI assistant for a teacher in a classroom called 'EyeClass'.
        Analyze this real-time data:
        - Average Attention: {stats['avg']}%
        - Max Attention: {stats['max']}%
        - Min Attention: {stats['min']}%
        - Subject: {stats['subject']}
        - Topic: {stats['topic']}

        Provide exactly 3 short, punchy, and actionable insights for the teacher (max 10 words each).
        Return them as a raw JSON list of strings. Example: ["Slow down, confusion detected.", "Great engagement in back row.", "Ask a question to reset focus."]
        """
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"AI Error: {e}")
        return ai_cache["suggestions"]


def generate_lesson_data():
    """Generates the data snapshot (Graphics + AI)"""

    blocks = []
    for i in range(25):
        att = random.randint(30, 100)
        restless = (100 - att) + random.randint(-10, 10)
        restless = max(0, min(100, restless))
        blocks.append({"id": i, "attention": att, "restlessness": restless})

    avg_att = sum(b['attention'] for b in blocks) // 25

    current_time = time.time()

    current_stats = {
        "avg": avg_att,
        "max": max(b['attention'] for b in blocks),
        "min": min(b['attention'] for b in blocks),
        "subject": session.get("subject", "General"),
        "topic": session.get("lesson_topic", "General")
    }

    if current_time - ai_cache["last_update"] > AI_UPDATE_INTERVAL:
        print("🤖 Fetching fresh insights from Gemini...")
        new_suggestions = generate_ai_insights(current_stats)
        if new_suggestions:
            ai_cache["suggestions"] = new_suggestions
        ai_cache["last_update"] = current_time

    dummy_data = {
        "overview": {"Engaged": f"{avg_att}%", "Distracted": f"{100 - avg_att}%", "Drowsy": "5%"},
        "avg_attention": avg_att,
        "max_attention": current_stats['max'],
        "min_attention": current_stats['min'],
        "blocks": blocks,
        "attention_time": [random.randint(60, 95) for _ in range(8)],
        "suggestions": ai_cache["suggestions"]
    }

    filename = f"lesson_{int(time.time())}.json"
    with open(os.path.join(JSON_FOLDER, filename), "w") as f:
        json.dump(dummy_data, f)
    return filename


# --- ROUTES ---

@app.route("/")
def index():
    if not os.listdir(JSON_FOLDER):
        generate_lesson_data()

    active_session = all(k in session for k in ["subject", "topic"])
    initial_data = None

    if active_session:
        files = sorted([f for f in os.listdir(JSON_FOLDER) if f.endswith(".json")],
                       key=lambda x: os.path.getmtime(os.path.join(JSON_FOLDER, x)), reverse=True)
        if files:
            with open(os.path.join(JSON_FOLDER, files[0]), "r") as f:
                initial_data = json.load(f)

    return render_template("app_shell.html", active_session=active_session, initial_data=initial_data)


@app.route("/api/start_lesson", methods=["POST"])
def start_lesson():
    data = request.json
    session["lesson_topic"] = data.get("topic")
    session["subject"] = data.get("subject")
    session["start_time"] = time.strftime("%H:%M")

    session["chat_history"] = []
    ai_cache["last_update"] = 0

    generate_lesson_data()
    return jsonify({"status": "success"})


@app.route("/api/get_dashboard_data")
def get_dashboard_data():
    is_history = request.args.get('history') == 'true'

    if not is_history:
        generate_lesson_data()

    files = [f for f in os.listdir(JSON_FOLDER) if f.endswith(".json")]
    if not files: return jsonify({"error": "No data"}), 404

    files.sort(key=lambda x: os.path.getmtime(os.path.join(JSON_FOLDER, x)), reverse=True)
    with open(os.path.join(JSON_FOLDER, files[0]), "r") as f:
        data = json.load(f)

    response = {
        "meta": {
            "subject": session.get("subject", "Demo"),
            "topic": session.get("lesson_topic", "Overview"),
        },
        "data": data
    }
    return jsonify(response)


@app.route("/api/chat", methods=["POST"])
def chat_with_ai():
    user_msg = request.json.get("message")

    if not has_ai:
        time.sleep(1)
        return jsonify(
            {"reply": "I am currently in offline mode. Please add a valid Gemini API Key to app.py to chat with me!"})

    history = session.get("chat_history", [])
    context = f"You are an AI teaching assistant. The teacher is currently teaching {session.get('subject')} - {session.get('lesson_topic')}. Keep answers short and helpful."

    try:
        chat = chat_model.start_chat(history=[])
        response = chat.send_message(f"{context}\nTeacher asks: {user_msg}")

        history.append({"role": "user", "parts": [user_msg]})
        history.append({"role": "model", "parts": [response.text]})
        session["chat_history"] = history[-10:]

        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"reply": "Sorry, I had trouble connecting to the AI brain."})


@app.route("/api/end_lesson", methods=["POST"])
def end_lesson():
    session.clear()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)