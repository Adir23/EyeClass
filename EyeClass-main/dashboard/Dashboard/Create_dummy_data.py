import os
import json
import random
import time
from datetime import datetime, timedelta

FOLDER = "JsonFilesData"
os.makedirs(FOLDER, exist_ok=True)

LESSONS = [
    {"subject": "Mathematics", "topic": "Calculus", "mode": "group"},
    {"subject": "History", "topic": "World War II", "mode": "single"},
    {"subject": "Physics", "topic": "Quantum Mechanics", "mode": "group"},
    {"subject": "Literature", "topic": "Shakespeare", "mode": "single"},
    {"subject": "Civics", "topic": "Human Rights", "mode": "group"},
    {"subject": "Biology", "topic": "Cell Structure", "mode": "single"},
]

SUGGESTIONS = [
    "Check back row engagement.", "Great pacing!", "Ask more questions.",
    "Energy is dropping.", "Perfect visual aids.", "Review last concept."
]


def create_files():
    print(f"--- Generating Data in {FOLDER} ---")

    # Clean old files
    for f in os.listdir(FOLDER):
        os.remove(os.path.join(FOLDER, f))

    # Generate 10 past lessons
    for i in range(10):
        lesson = random.choice(LESSONS)
        past_time = datetime.now() - timedelta(days=i * 2)
        timestamp = past_time.timestamp()

        avg_att = random.randint(50, 95)

        # Single vs Group logic
        if lesson["mode"] == "single":
            blocks = [{"id": 0, "attention": avg_att}]
        else:
            blocks = [{"id": x, "attention": avg_att + random.randint(-10, 10)} for x in range(6)]

        data = {
            "timestamp": timestamp,
            "date_str": past_time.strftime("%d/%m %H:%M"),
            "subject": lesson["subject"],
            "topic": lesson["topic"],
            "mode": lesson["mode"],
            "avg_attention": avg_att,
            "blocks": blocks,
            "attention_time": [avg_att + random.randint(-5, 5) for _ in range(6)],
            "suggestions": random.sample(SUGGESTIONS, 3)
        }

        filename = f"lesson_{int(timestamp)}.json"
        with open(os.path.join(FOLDER, filename), "w") as f:
            json.dump(data, f, indent=4)

    print("✅ Data Generated Successfully.")


if __name__ == "__main__":
    create_files()