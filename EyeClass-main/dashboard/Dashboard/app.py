import os
import json
import random
import time
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = "eyeclass-ultra-secret"

JSON_FOLDER = "JsonFilesData"
os.makedirs(JSON_FOLDER, exist_ok=True)

def generate_dummy_lesson():
    """Creates richer dummy data for the advanced visualizations."""
    # Generate blocks with attention AND a 'restlessness' factor for the heatmap visuals
    blocks = []
    for i in range(25): # 5x5 grid
        att = random.randint(30, 100)
        # Restlessness is higher when attention is lower, but with some noise
        restless = (100 - att) + random.randint(-10, 10)
        restless = max(0, min(100, restless)) # Clamp 0-100

        blocks.append({
            "id": i, 
            "attention": att,
            "restlessness": restless
        })

    dummy_data = {
        "overview": {"Engaged": "85%", "Distracted": "12%", "Drowsy": "3%"},
        "avg_attention": 82,
        "max_attention": 96,
        "min_attention": 54,
        "blocks": blocks,
        # Create a more realistic curve
        "attention_time": [70, 75, 82, 65, 88, 92, 85, 78], 
        "suggestions": [
            "Group 3 is losing focus. Try a quick poll.",
            "Excellent pacing. Engagement is peaking.",
            "Consider a 2-minute stretch break soon."
        ]
    }
    filename = f"lesson_{int(time.time())}.json"
    with open(os.path.join(JSON_FOLDER, filename), "w") as f:
        json.dump(dummy_data, f)
    return filename

# --- Routes ---

@app.route("/")
def index():
    if not os.listdir(JSON_FOLDER):
        generate_dummy_lesson()
    
    # Check if a live session exists in session storage
    active_session = all(k in session for k in ["subject", "topic"])
    # Pass initial data to render immediately without waiting for first fetch
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
    session["class_name"] = data.get("class_name")
    session["start_time"] = time.strftime("%H:%M")
    generate_dummy_lesson()
    return jsonify({"status": "success"})

@app.route("/api/get_dashboard_data")
def get_dashboard_data():
    # Simulate network delay for skeleton loader demo
    time.sleep(0.5) 
    
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

@app.route("/api/end_lesson", methods=["POST"])
def end_lesson():
    session.clear()
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)