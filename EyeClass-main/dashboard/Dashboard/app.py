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
    "suggestions": ["Analyzing...", "Waiting for data...", "Insights coming soon."]
}
AI_UPDATE_INTERVAL = 20


# --- HELPER FUNCTIONS ---

def generate_ai_insights(stats):
    if not has_ai: return ["⚠️ AI Offline", "Check API Key", "Manual Mode"]
    try:
        prompt = f"""
        Teacher Assistant Analysis:
        - Avg Attention: {stats['avg']}%
        - Topic: {stats['topic']}
        Give 3 short (max 8 words) actionable tips for the teacher right now.
        Return raw JSON list of strings.
        """
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except:
        return ai_cache["suggestions"]


def generate_lesson_data():
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
        new_suggestions = generate_ai_insights(current_stats)
        if new_suggestions: ai_cache["suggestions"] = new_suggestions
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
    if not os.listdir(JSON_FOLDER): generate_lesson_data()
    active_session = all(k in session for k in ["subject", "topic"])
    return render_template("app_shell.html", active_session=active_session)


@app.route("/api/start_lesson", methods=["POST"])
def start_lesson():
    data = request.json
    session["lesson_topic"] = data.get("topic")
    session["subject"] = data.get("subject")
    ai_cache["last_update"] = 0
    generate_lesson_data()
    return jsonify({"status": "success"})


@app.route("/api/get_dashboard_data")
def get_dashboard_data():
    if request.args.get('history') != 'true': generate_lesson_data()
    files = sorted([f for f in os.listdir(JSON_FOLDER) if f.endswith(".json")],
                   key=lambda x: os.path.getmtime(os.path.join(JSON_FOLDER, x)), reverse=True)
    if not files: return jsonify({"error": "No data"}), 404

    with open(os.path.join(JSON_FOLDER, files[0]), "r") as f:
        data = json.load(f)
    return jsonify(
        {"meta": {"subject": session.get("subject", "Demo"), "topic": session.get("lesson_topic", "Overview")},
         "data": data})


@app.route("/api/chat", methods=["POST"])
def chat_with_ai():
    user_msg = request.json.get("message")
    if not has_ai: return jsonify({"reply": "AI is offline."})

    history = session.get("chat_history", [])
    try:
        chat = chat_model.start_chat(history=[])
        response = chat.send_message(
            f"Teacher Assistant Context: Teaching {session.get('subject')}. Keep answers short.\nUser: {user_msg}")
        history.append({"role": "user", "parts": [user_msg]})
        history.append({"role": "model", "parts": [response.text]})
        session["chat_history"] = history[-10:]
        return jsonify({"reply": response.text})
    except:
        return jsonify({"reply": "AI Connection Error"})


# --- NEW: WEEKLY INSIGHTS ENDPOINT ---
@app.route("/api/weekly_insights")
def get_weekly_insights():
    if not has_ai:
        time.sleep(1)
        return jsonify({"text": "AI is offline. Please check your API key to see the weekly summary."})

    try:
        # We simulate sending weekly stats to Gemini
        prompt = """
        You are a pedagogical expert. Analyze this teacher's weekly performance:
        - Average Engagement: 89% (High)
        - Best Class: 10-A (Math)
        - Improvement: +5% from last week.

        Write a short, encouraging paragraph (max 40 words) summarizing the week and giving one key takeaway. 
        Tone: Professional, Warm, Concise.
        """
        response = model.generate_content(prompt)
        return jsonify({"text": response.text.strip()})
    except Exception as e:
        return jsonify({"text": "Could not generate analysis at this moment."})


@app.route("/api/end_lesson", methods=["POST"])
def end_lesson():
    session.clear()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)