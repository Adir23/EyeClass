import os
import json
import random
import time
import glob
from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "eyeclass-final-secret"

# --- CONFIG ---
JSON_FOLDER = "JsonFilesData"
os.makedirs(JSON_FOLDER, exist_ok=True)

# Set to True to use real Gemini API, False for simulation
ENABLE_AI = False
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

has_ai = False
if ENABLE_AI and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        has_ai = True
        print("✅ Gemini AI Connected")
    except:
        print("⚠️ AI Connection Failed")


# --- DATA GENERATION ---
def generate_lesson_snapshot(mode="group"):
    # Single vs Group Logic
    if mode == "single":
        blocks = [{"id": 0, "attention": random.randint(50, 100)}]
    else:
        blocks = [{"id": i, "attention": random.randint(40, 98)} for i in range(6)]

    avg_att = sum(b['attention'] for b in blocks) // len(blocks)

    return {
        "timestamp": time.time(),
        "date_str": time.strftime("%d/%m %H:%M"),
        "subject": session.get("subject", "General"),
        "topic": session.get("lesson_topic", "General"),
        "mode": mode,
        "avg_attention": avg_att,
        "blocks": blocks,
        "attention_time": [random.randint(60, 95) for _ in range(6)],
        "suggestions": [
            "Check the back row.",
            "Great energy!",
            "Pause for questions."
        ]
    }


# --- ROUTES ---

@app.route("/")
def index():
    active_session = "subject" in session
    return render_template("app_shell.html", active_session=active_session)


@app.route("/api/start_lesson", methods=["POST"])
def start_lesson():
    data = request.json
    session["subject"] = data.get("subject")
    session["lesson_topic"] = data.get("topic")
    session["mode"] = data.get("mode", "group")
    return jsonify({"status": "success"})


@app.route("/api/get_dashboard_data")
def get_dashboard_data():
    is_history = request.args.get('history') == 'true'
    file_id = request.args.get('file_id')

    if not is_history and "subject" in session:
        # Live Data
        data = generate_lesson_snapshot(session.get("mode", "group"))
    else:
        # History Data
        files = sorted(glob.glob(os.path.join(JSON_FOLDER, "*.json")), key=os.path.getmtime, reverse=True)
        if not files: return jsonify({"error": "No data"}), 404

        target_file = files[0]
        if file_id:
            for f in files:
                if str(int(os.path.getmtime(f))) == file_id or file_id in f:
                    target_file = f
                    break

        # Added Error Handling to prevent crashes on corrupted JSON
        try:
            with open(target_file, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading JSON history: {e}")
            return jsonify({"error": "Corrupted file data"}), 500

    return jsonify({"data": data})


@app.route("/api/get_history_list")
def get_history_list():
    files = sorted(glob.glob(os.path.join(JSON_FOLDER, "*.json")), key=os.path.getmtime, reverse=True)
    history = []
    for f in files:
        try:
            with open(f, "r") as reader:
                d = json.load(reader)
                history.append({
                    "id": str(int(d["timestamp"])),
                    "subject": d.get("subject", "Unknown"),
                    "date": d.get("date_str", "N/A"),
                    "score": d.get("avg_attention", 0),
                    "mode": d.get("mode", "group")
                })
        except:
            continue
    return jsonify(history)


@app.route("/api/monthly_insights")
def get_monthly_insights():
    return jsonify({
        "text": "Monthly Analysis: Engagement is up 15% compared to last month. Science classes show the highest improvement."
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")
    
    # Grab current lesson context (if active)
    current_subject = session.get("subject", "general education")
    current_topic = session.get("lesson_topic", "general topics")
    
    if has_ai:
        try:
            # Inject context into the prompt
            prompt = f"""
            You are an expert teaching assistant app called EyeClass. 
            The teacher is currently teaching a lesson on {current_subject} (Topic: {current_topic}).
            Keep your answers very brief, practical, and tailored to this specific subject.
            
            Teacher says: {user_msg}
            """
            response = model.generate_content(prompt)
            return jsonify({"reply": response.text})
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return jsonify({"reply": "AI Error. Please try again."})
            
    return jsonify({"reply": "AI is disabled. Set ENABLE_AI = True and check your API key."})


@app.route("/api/end_lesson", methods=["POST"])
def end_lesson():
    session.clear()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)