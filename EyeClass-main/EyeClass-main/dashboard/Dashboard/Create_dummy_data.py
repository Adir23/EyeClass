import os
import json
import random
import glob
import argparse
from datetime import datetime, timedelta

FOLDER = "JsonFilesData"

LESSONS = [
    # STEM
    {"subject": "Mathematics", "topic": "Calculus: Derivatives", "mode": "group"},
    {"subject": "Mathematics", "topic": "Linear Algebra", "mode": "single"},
    {"subject": "Physics", "topic": "Quantum Mechanics", "mode": "group"},
    {"subject": "Biology", "topic": "Cellular Respiration", "mode": "single"},
    {"subject": "Chemistry", "topic": "Thermodynamics", "mode": "group"},
    {"subject": "Computer Science", "topic": "Data Structures", "mode": "single"},

    # Humanities & Social Sciences
    {"subject": "History", "topic": "World War II", "mode": "single"},
    {"subject": "Civics", "topic": "Human Rights Law", "mode": "group"},
    {"subject": "Geography", "topic": "Climate Change Impacts", "mode": "single"},
    {"subject": "Psychology", "topic": "Cognitive Biases", "mode": "group"},

    # Arts & Languages
    {"subject": "Literature", "topic": "Shakespearean Tragedies", "mode": "single"},
    {"subject": "English", "topic": "Creative Writing Workshop", "mode": "group"},
    {"subject": "Hebrew", "topic": "The verb", "mode": "single"},
    {"subject": "Art", "topic": "Color Theory", "mode": "single"},
]

SUGGESTIONS = {
    "high": [
        "Great pacing today!",
        "Excellent student participation!",
        "Perfect use of visual aids.",
        "High engagement throughout the lesson.",
        "Great tone and enthusiasm.",
        "The class tracked complex concepts well."
    ],
    "medium": [
        "Check back row engagement.",
        "Try a quick 'think-pair-share' activity.",
        "Call on specific students to increase focus.",
        "Use a quick poll to check for understanding.",
        "Summarize key takeaways to recenter the class.",
        "Provide more real-world examples."
    ],
    "low": [
        "Energy dropped significantly; try an interactive activity.",
        "Students seem confused, try simplifying.",
        "Pause longer for Q&A to clarify concepts.",
        "Break down the material into smaller chunks.",
        "Consider adding a 5-minute brain break.",
        "Allocate more time for guided practice.",
        "Speak a bit louder and move around the room."
    ]
}

SUBJECT_TIPS = {
    "Mathematics": "Work through another practice problem together on the board.",
    "Physics": "Try demonstrating with a physical model or simulation.",
    "History": "Encourage a short debate or discussion on this era.",
    "Literature": "Ask students to read a passage aloud to regain focus.",
    "Computer Science": "Do a quick live-coding walkthrough.",
    "Hebrew": "Try playing a little interactive game"
}


def clamp(value, min_val=0, max_val=100):
    return max(min_val, min(value, max_val))


def generate_realistic_blocks(avg_att):
    blocks = []

    # סיכוי של 40% שיהיה "תלמיד בעייתי" (או מצטיין) שחורג מהממוצע באופן קיצוני
    has_outlier = random.random() < 0.4
    outlier_index = random.randint(0, 5) if has_outlier else -1

    for i in range(6):
        if i == outlier_index:
            # אם זה ה-outlier, נזרוק אותו רחוק מהממוצע (עד 40% הפרש)
            if avg_att > 60:
                # ממוצע גבוה -> ה-outlier מאבד קשב
                val = avg_att - random.randint(30, 45)
            else:
                # ממוצע נמוך -> ה-outlier דווקא מקשיב מעולה
                val = avg_att + random.randint(30, 45)
        else:
            # השאר נעים סביב הממוצע בסטייה נורמלית יותר (עד 15% לפה או לשם)
            val = avg_att + random.randint(-15, 15)

        blocks.append({"id": i, "attention": clamp(val)})

    return blocks


def create_files(num_files=20):
    os.makedirs(FOLDER, exist_ok=True)
    print(f"--- Generating {num_files} smart files in '{FOLDER}' ---")

    old_files = glob.glob(os.path.join(FOLDER, "*.json"))
    for f in old_files:
        try:
            os.remove(f)
        except Exception as e:
            pass

    for _ in range(num_files):
        lesson = random.choice(LESSONS)

        days_ago = random.uniform(0, 30)
        past_time = datetime.now() - timedelta(days=days_ago)
        timestamp = past_time.timestamp()

        # הסטת הנתונים כלפי מעלה (ציונים גבוהים יותר)
        r = random.random()
        if r < 0.65:
            base_att = random.randint(70, 100)
        elif r < 0.90:
            base_att = random.randint(50, 69)
        else:
            base_att = random.randint(20, 49)

        if lesson["mode"] == "single":
            blocks = [{"id": 0, "attention": base_att}]
        else:
            blocks = generate_realistic_blocks(base_att)

        # נחשב את הממוצע האמיתי של הבלוקים אחרי שהוספנו את החריגות
        avg_att = sum(b['attention'] for b in blocks) // len(blocks)

        if avg_att >= 75:
            pool = SUGGESTIONS["high"]
        elif avg_att >= 50:
            pool = SUGGESTIONS["medium"]
        else:
            pool = SUGGESTIONS["low"]

        selected_suggestions = random.sample(pool, random.randint(2, 3))

        if lesson["subject"] in SUBJECT_TIPS and random.random() > 0.5:
            selected_suggestions.append(SUBJECT_TIPS[lesson["subject"]])

        data = {
            "timestamp": timestamp,
            "date_str": past_time.strftime("%d/%m %H:%M"),
            "subject": lesson["subject"],
            "topic": lesson["topic"],
            "mode": lesson["mode"],
            "avg_attention": avg_att,
            "blocks": blocks,
            "attention_time": [clamp(avg_att + random.randint(-10, 10)) for _ in range(6)],
            "suggestions": selected_suggestions
        }

        filename = f"lesson_{int(timestamp)}.json"
        filepath = os.path.join(FOLDER, filename)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

    print(f"✅ Successfully generated {num_files} context-aware sessions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate smart dummy JSON data for EyeClass.")
    parser.add_argument("--count", type=int, default=20, help="Number of dummy files to generate")
    args = parser.parse_args()

    create_files(args.count)