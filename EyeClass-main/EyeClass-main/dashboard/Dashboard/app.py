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
ENABLE_AI = True

"""
LIST OF API KEYS:
AIzaSyDYegp6bwItdwJZjmEwQQ-6EW9TdFd9Qwo
AIzaSyAI-zv5Xyqb_7KMncPUXLOvmbx08kI_YLQ
AIzaSyDyyHWUefAFT83McZJi6YO3340EnzfygdE
AIzaSyC8mSId8x1gQ-gJ6g9bmHVHu8iDM0-BTOk
"""
GEMINI_API_KEY = "AIzaSyB6vPuwiiuu5M4HKC4qQ7S2Bsm8TJrytL4"
has_ai = False
if ENABLE_AI and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        has_ai = True
        print("AI ENABLED")
    except Exception as e:
        print(f"AI CONNECTION FAILED: {e}")
else:
    print("AI DISABLED")


def clamp(value, min_val=0, max_val=100):
    return max(min_val, min(value, max_val))


def generate_realistic_blocks(avg_att):
    blocks = []

    # סיכוי של 40% שיהיה חלק בכיתה שמתנהג אחרת מהשאר
    has_outlier = random.random() < 0.4
    outlier_index = random.randint(0, 5) if has_outlier else -1

    for i in range(6):
        if i == outlier_index:
            if avg_att > 60:
                # הרוב מקשיבים, אבל חלק אחד מאבד קשב משמעותית
                val = avg_att - random.randint(30, 45)
            else:
                # הרוב לא מקשיבים, אבל חלק אחד מקשיב מעולה
                val = avg_att + random.randint(30, 45)
        else:
            # השאר עם סטייה קטנה מהממוצע (עד 15%)
            val = avg_att + random.randint(-15, 15)

        blocks.append({"id": i, "attention": clamp(val)})

    return blocks


# --- SMART DATA GENERATION ---
def generate_smart_suggestions(mode, blocks, avg_att, is_live):
    suggestions = []

    if is_live:
        if mode == "single":
            if avg_att >= 80:
                pool = [
                    "The student is highly focused.",
                    "Perfect pacing, keep it up!",
                    "Great eye contact and engagement.",
                    "The material seems to resonate well.",
                    "Excellent momentum in the session."
                ]
            elif avg_att >= 60:
                pool = [
                    "Attention is slightly fluctuating.",
                    "Consider asking a direct question to re-engage.",
                    "A quick interactive task might help.",
                    "Pacing is okay, but check comprehension.",
                    "Try connecting the topic to a real-world example."
                ]
            else:
                pool = [
                    "The student seems distracted.",
                    "Try switching to a visual explanation.",
                    "Consider taking a 2-minute stretch break.",
                    "Check if the difficulty level is appropriate.",
                    "Change the current activity to regain focus."
                ]
            suggestions = random.sample(pool, 3)
        else:
            if avg_att >= 80:
                pool1 = ["Overall class engagement is excellent!", "High energy in the room today.",
                         "Students are tracking perfectly."]
                pool2 = ["Great time to introduce complex concepts.",
                         "The current teaching method is highly effective.", "Perfect atmosphere for group discussion."]
            elif avg_att >= 60:
                pool1 = ["Class attention is moderate.", "Engagement is okay, but could be better.",
                         "Energy levels are starting to dip."]
                pool2 = ["Keep the energy up with a quick question.", "Try adding a short visual aid.",
                         "Consider slightly faster pacing."]
            else:
                pool1 = ["General focus is quite low.", "Many students seem distracted.",
                         "Attention has dropped significantly."]
                pool2 = ["Consider a quick stretch break.", "Change the activity immediately.",
                         "Switch from lecture to interactive mode."]

            suggestions.append(random.choice(pool1))

            lowest_block = min(blocks, key=lambda b: b['attention'])
            if lowest_block['attention'] < 60:
                if lowest_block['id'] < 2:
                    zone = "front row"
                elif lowest_block['id'] < 4:
                    zone = "middle rows"
                else:
                    zone = "back row"

                zone_pool = [
                    f"The {zone} is losing focus. Try walking towards them.",
                    f"Direct a question to the {zone} to re-engage them.",
                    f"Eye contact is dropping in the {zone}."
                ]
                suggestions.append(random.choice(zone_pool))
            else:
                good_zone_pool = [
                    "All rows are maintaining steady focus.",
                    "No specific weak spots detected in the class.",
                    "Even the back rows are highly engaged."
                ]
                suggestions.append(random.choice(good_zone_pool))

            while len(suggestions) < 3:
                cand = random.choice(pool2)
                if cand not in suggestions:
                    suggestions.append(cand)
    else:
        if mode == "single":
            if avg_att >= 75:
                pool = [
                    "A very successful 1-on-1 session.",
                    "The visual examples worked perfectly.",
                    "Student maintained strong focus throughout.",
                    "Good pacing and clear explanations.",
                    "Replicate this structure for future sessions."
                ]
            else:
                pool = [
                    "Engagement was below average.",
                    "Next time, try adding interactive tasks.",
                    "Consider breaking theory into smaller chunks.",
                    "Attention dropped in the second half.",
                    "Ask more questions to gauge understanding early."
                ]
            suggestions = random.sample(pool, 3)
        else:
            if avg_att >= 80:
                pool = [
                    "Excellent overall class engagement.",
                    "Group activity was highly effective.",
                    "Replicate this lesson structure next time.",
                    "High participation rates recorded.",
                    "Visuals kept the class highly focused."
                ]
            else:
                pool = [
                    "Engagement dropped during theoretical parts.",
                    "Consider shorter lecture segments.",
                    "More interactive elements recommended next time.",
                    "Back rows showed lower participation.",
                    "Try adding a mid-lesson break next time."
                ]
            suggestions = random.sample(pool, 3)

    return suggestions[:3]


def generate_lesson_snapshot(mode="group", is_live=True):
    # פונקציית הטיה כלפי מעלה ליצירת נתונים מציאותיים יותר
    def get_skewed_att():
        r = random.random()
        if r < 0.65:
            return random.randint(70, 100)
        elif r < 0.90:
            return random.randint(50, 69)
        else:
            return random.randint(20, 49)

    base_att = get_skewed_att()

    if mode == "single":
        blocks = [{"id": 0, "attention": base_att}]
    else:
        # שימוש בפונקציה החדשה שיוצרת מפת כיתה מציאותית עם חריגים
        blocks = generate_realistic_blocks(base_att)

    # נחשב את הממוצע האמיתי אחרי ההפרעות שהוספנו
    avg_att = sum(b['attention'] for b in blocks) // len(blocks)

    session["current_avg_attention"] = avg_att

    if is_live:
        history = session.get("attention_history", [65, 70, 75, 80, 85])
        history.append(avg_att)
        history = history[-6:]
        session["attention_history"] = history
        chart_data = history
    else:
        chart_data = [random.randint(55, 95) for _ in range(5)] + [avg_att]

    suggestions = generate_smart_suggestions(mode, blocks, avg_att, is_live)

    return {
        "timestamp": time.time(),
        "date_str": time.strftime("%d/%m %H:%M"),
        "subject": session.get("subject", "General"),
        "topic": session.get("lesson_topic", "General"),
        "mode": mode,
        "avg_attention": avg_att,
        "blocks": blocks,
        "attention_time": chart_data,
        "suggestions": suggestions
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

    session["attention_history"] = [70, 75, 80, 85, 90, 95]
    session["current_avg_attention"] = 100

    return jsonify({"status": "success"})


@app.route("/api/get_dashboard_data")
def get_dashboard_data():
    is_history = request.args.get('history') == 'true'
    file_id = request.args.get('file_id')

    if not is_history and "subject" in session:
        data = generate_lesson_snapshot(session.get("mode", "group"), is_live=True)
    else:
        files = sorted(glob.glob(os.path.join(JSON_FOLDER, "*.json")), key=os.path.getmtime, reverse=True)

        if not files:
            mock_data = generate_lesson_snapshot("group", is_live=False)
            return jsonify({"data": mock_data})

        target_file = files[0]
        if file_id:
            for f in files:
                if str(int(os.path.getmtime(f))) == file_id or file_id in f:
                    target_file = f
                    break

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

    if not history:
        history = [
            {"id": "1", "subject": "Psychology", "date": "16/02 12:55", "score": 94, "mode": "group"},
            {"id": "2", "subject": "History", "date": "16/02 14:11", "score": 62, "mode": "single"},
            {"id": "3", "subject": "Civics", "date": "18/02 10:36", "score": 84, "mode": "group"}
        ]

    return jsonify(history)


@app.route("/api/monthly_insights")
def get_monthly_insights():
    return jsonify({
        "text": "Monthly Analysis: Engagement is up 8% compared to last month. Science classes show the highest improvement, while History might need more visual aids."
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")

    current_subject = session.get("subject", "None")
    current_topic = session.get("lesson_topic", "None")
    is_live = "subject" in session

    app_context = ""
    if is_live:
        current_avg = session.get("current_avg_attention", "N/A")
        app_context = f"The teacher is currently in a LIVE LESSON. Subject: {current_subject}. Topic: {current_topic}. Current class attention average is {current_avg}%."
    else:
        files = sorted(glob.glob(os.path.join(JSON_FOLDER, "*.json")), key=os.path.getmtime, reverse=True)[:3]
        hist_str = ""
        for f in files:
            try:
                with open(f, 'r') as r:
                    d = json.load(r)
                    hist_str += f"[{d.get('subject')} - Score: {d.get('avg_attention')}%] "
            except:
                pass

        if not hist_str:
            hist_str = "No recent sessions available."

        app_context = f"The teacher is NOT in a live lesson right now. Recent lessons history: {hist_str}."

    if has_ai:
        try:
            prompt = f"""
            You are the EyeClass AI Assistant. 

            CRITICAL RULES:
            1. LANGUAGE: You MUST reply ONLY in Hebrew (עברית). Never use English. Do not introduce yourself with a specific name.
            2. NO GREETINGS: NEVER say 'שלום', 'היי', 'בוקר טוב', 'ערב טוב', or 'אהלן' in any of your messages. Start answering the question immediately and directly.
            3. TONE & LENGTH: Be conversational, friendly, direct, and very short. Keep your answer to 1-3 sentences maximum. Do not use bullet points. Do not be annoying or overly formal.
            4. CONTEXT: Use the following app data to answer questions about the class state if relevant:
            --- APP DATA CONTEXT ---
            {app_context}
            ------------------------
            5. OFF-TOPIC: If asked about things unrelated to education or the EyeClass app (like recipes, sports), politely say in Hebrew that you are an educational assistant and offer to help with the lesson instead.

            Teacher says: {user_msg}
            """
            response = model.generate_content(prompt)
            return jsonify({"reply": response.text})
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return jsonify(
                {"reply": "יש בעיה בחיבור לשרת כרגע, אנא נסה שוב מאוחר יותר."})

    if is_live:
        if any(word in user_msg for word in ["ריכוז", "קשב", "ישנים", "משעמם", "עזרה"]):
            reply = f"לפי הנתונים של שיעור {current_subject}, אני ממליץ לעשות הפסקה קצרה או לשאול שאלה כדי להחזיר את הריכוז."
        elif any(word in user_msg for word in ["טוב", "מעולה", "מצוין", "יופי"]):
            reply = "הנתונים מסכימים איתך! רמת הקשב נראית מצוין כרגע."
        else:
            reply = f"אני עוקב אחרי שיעור {current_subject} בלייב. הקשב עומד על {session.get('current_avg_attention', 'N/A')}%. איך אפשר לעזור?"
    else:
        if any(word in user_msg for word in ["סיכום", "אחרון", "היסטוריה", "עבר"]):
            reply = "מבט על השיעורים האחרונים מראה שעבודה בקבוצות העלתה את הקשב ב-15% בממוצע."
        else:
            reply = "אנחנו כרגע לא בשיעור חי. אפשר להתחיל שיעור כדי לקבל משוב בזמן אמת, או לשאול אותי על שיעורי עבר."

    return jsonify({"reply": reply})


@app.route("/api/end_lesson", methods=["POST"])
def end_lesson():
    if "subject" in session:
        data = generate_lesson_snapshot(session.get("mode", "group"), is_live=False)
        filename = os.path.join(JSON_FOLDER, f"session_{int(data['timestamp'])}.json")
        try:
            with open(filename, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Failed to save session: {e}")

    session.clear()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)