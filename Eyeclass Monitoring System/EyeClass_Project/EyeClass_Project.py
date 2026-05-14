import cv2
import time
import json
import os
import sys
import threading
import queue
import math
import textwrap
from collections import defaultdict

import numpy as np
import mediapipe as mp
import speech_recognition as sr
from faster_whisper import WhisperModel

# Libraries for Hebrew Text
from PIL import Image, ImageDraw, ImageFont
from bidi.algorithm import get_display

# -----------------------------
# SYSTEM & PATH CONFIG
# -----------------------------
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

MODEL_DIR = "ModelFiles"
JSON_DIR = "JsonFilesData"

os.makedirs(JSON_DIR, exist_ok=True)

YOLO_WEIGHTS = os.path.join(MODEL_DIR, "yolov4-tiny.weights")
YOLO_CONFIG = os.path.join(MODEL_DIR, "yolov4-tiny.cfg")
COCO_NAMES = os.path.join(MODEL_DIR, "coco.names")

# -----------------------------
# PERFORMANCE CONFIG
# -----------------------------
REQUESTED_WIDTH = 1920
REQUESTED_HEIGHT = 1080
REQUESTED_FPS = 30  

PROCESSING_WIDTH = 640
PROCESSING_HEIGHT = 360

DISPLAY_WIDTH = 960
DISPLAY_HEIGHT = 540

YOLO_FRAME_INTERVAL = 60  

# -----------------------------
# EYE TRACKING CONSTANTS
# -----------------------------
LEFT_EYE_IDXS = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDXS = [362, 385, 387, 263, 373, 380]
LEFT_IRIS_IDX = [474, 475, 476, 477]
RIGHT_IRIS_IDX = [469, 470, 471, 472]

EAR_THRESHOLD = 0.20        
SLEEP_TIME_THRESHOLD = 1.5  
GAZE_CENTER_LIMIT = 0.4     

# -----------------------------
# HELPER: CONSOLE PRINTING
# -----------------------------
def print_hebrew(text):
    try:
        fixed_text = get_display(text)
        print(f" >> {fixed_text}")
    except Exception:
        print(f" >> {text}")

# -----------------------------
# CLASS: THREADED CAMERA
# -----------------------------
class ThreadedCamera:
    def __init__(self, src=0):
        self.capture = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, REQUESTED_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, REQUESTED_HEIGHT)
        self.capture.set(cv2.CAP_PROP_FPS, REQUESTED_FPS)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.status = False
        self.frame = None
        
        if self.capture.isOpened():
            self.status, self.frame = self.capture.read()
            self.thread = threading.Thread(target=self.update, args=())
            self.thread.daemon = True
            self.thread.start()

    def update(self):
        while True:
            if self.capture.isOpened():
                status, frame = self.capture.read()
                if status:
                    self.frame = frame
                    self.status = status
            else:
                break
            time.sleep(0.005)

    def get_frame(self):
        return self.status, self.frame

    def release(self):
        self.capture.release()

# -----------------------------
# CLASS: PRO AUDIO TRANSCRIBER (FULLY ASYNC QUEUE)
# -----------------------------
class SpeechTranscriber:
    def __init__(self, language="he", mic_index=None):
        self.recognizer = sr.Recognizer()
        
        # Hollyland Lark M2 optimizations
        self.recognizer.energy_threshold = 150  
        self.recognizer.dynamic_energy_threshold = False 
        self.recognizer.pause_threshold = 0.8 
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.4
        
        if mic_index is not None:
            self.microphone = sr.Microphone(device_index=mic_index, sample_rate=16000)
        else:
            self.microphone = sr.Microphone(sample_rate=16000)

        self.language = "he" if "he" in language else "en" 
        self.transcript_log = [] 
        self.text_buffer = ""
        self.last_speech_time = time.time()
        
        # ASYNC AUDIO QUEUE
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.stop_listening = None
        
        # --- NEW: MUTE STATE ---
        self.is_muted = False

        print("Calibrating Mic for 1 second... Please remain silent.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            
        print("Ready. Loading Faster-Whisper 'large-v3' Model...")
        self.model = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=2)
        print("Model Loaded & Ready!")

    def _callback(self, recognizer, audio):
        # If muted, just drop the audio completely
        if self.is_muted:
            return
        self.audio_queue.put(audio.get_raw_data())

    def _process_audio_queue(self):
        while self.is_running:
            try:
                raw_audio = self.audio_queue.get(timeout=1.0)
                audio_data = np.frombuffer(raw_audio, np.int16).flatten().astype(np.float32) / 32768.0
                
                segments, info = self.model.transcribe(
                    audio_data, 
                    language=self.language, 
                    beam_size=2,
                    vad_filter=True, 
                    condition_on_previous_text=False 
                )
                
                text = "".join([segment.text for segment in segments]).strip()
                if not text: continue

                timestamp = time.time()
                print_hebrew(f"[Speech]: {text}")
                self.transcript_log.append({"timestamp": timestamp, "text": text})
                
                if (timestamp - self.last_speech_time) < 4.0:
                    self.text_buffer += " " + text
                else:
                    self.text_buffer = text
                
                self.last_speech_time = timestamp
                
            except queue.Empty:
                continue 
            except Exception as e:
                print(f"Transcription Error: {e}")

    def start(self):
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._process_audio_queue, daemon=True)
        self.worker_thread.start()
        
        self.stop_listening = self.recognizer.listen_in_background(
            self.microphone, 
            self._callback, 
            phrase_time_limit=10 
        )

    def stop(self):
        self.is_running = False
        if self.stop_listening:
            self.stop_listening(wait_for_stop=False)
            
    def toggle_mute(self):
        self.is_muted = not self.is_muted
        return self.is_muted
    
    def get_log(self):
        return self.transcript_log
        
    def get_display_text(self):
        if time.time() - self.last_speech_time > 4.0:
            self.text_buffer = ""
            return ""
        return self.text_buffer

# -----------------------------
# HELPER: DRAW TEXT
# -----------------------------
def draw_overlay(img, text_data, max_width_limit=800):
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil, "RGBA")
    
    font_cache = {}
    def get_font(size):
        if size not in font_cache:
            try:
                font_cache[size] = ImageFont.truetype("arialbd.ttf", size) 
            except:
                font_cache[size] = ImageFont.load_default()
        return font_cache[size]

    for item in text_data:
        text, (x, y), size, text_color, bg_color, is_subtitle = item
        font = get_font(size)
        
        lines = []
        if is_subtitle and len(text) > 0:
            chars_per_line = int(max_width_limit / (size * 0.55)) 
            wrapped = textwrap.wrap(text, width=chars_per_line)
            lines = wrapped
        else:
            lines = [text]

        current_y = y
        if is_subtitle and len(lines) > 1:
            current_y = y - (len(lines) - 1) * (size + 8)

        for line in lines:
            display_line = get_display(line)
            bbox = draw.textbbox((x, current_y), display_line, font=font)
            padding = 10
            rect = (bbox[0] - padding, bbox[1] - padding, bbox[2] + padding, bbox[3] + padding)
            
            if bg_color:
                draw.rectangle(rect, fill=bg_color)
                
            draw.text((x, current_y), display_line, font=font, fill=text_color)
            current_y += size + 10

    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGBA2BGR)

# -----------------------------
# SETUP MEDIAPIPE & YOLO
# -----------------------------
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils 

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False, 
    max_num_faces=1, 
    refine_landmarks=True,
    min_detection_confidence=0.6, 
    min_tracking_confidence=0.6
)

if os.path.exists(YOLO_WEIGHTS) and os.path.exists(YOLO_CONFIG):
    yolo_net = cv2.dnn.readNet(YOLO_WEIGHTS, YOLO_CONFIG)
    yolo_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    yolo_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    with open(COCO_NAMES, "r") as f:
        classes = [line.strip() for line in f.readlines()]
    output_layers = yolo_net.getUnconnectedOutLayersNames()
    PHONE_CLASS_ID = classes.index("cell phone")
else:
    yolo_net = None

# -----------------------------
# LOGIC UTILS
# -----------------------------
def euclidean_dist(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

def calculate_ear(landmarks, indices):
    p1 = landmarks[indices[0]] 
    p2 = landmarks[indices[1]]
    p3 = landmarks[indices[2]]
    p4 = landmarks[indices[3]] 
    p5 = landmarks[indices[4]]
    p6 = landmarks[indices[5]]

    v1 = euclidean_dist(p2, p6)
    v2 = euclidean_dist(p3, p5)
    horizontal = euclidean_dist(p1, p4)

    if horizontal == 0: return 0.0
    ear = (v1 + v2) / (2.0 * horizontal)
    return ear

def get_gaze_ratio(landmarks, eye_indices, iris_index):
    left_corner = landmarks[eye_indices[0]]
    right_corner = landmarks[eye_indices[3]]
    iris_center = landmarks[iris_index]

    eye_width = euclidean_dist(left_corner, right_corner)
    dist_to_left = euclidean_dist(left_corner, iris_center)
    
    if eye_width == 0: return 0.5
    return dist_to_left / eye_width

def estimate_head_direction(landmarks, image_h, image_w):
    y_delta = (landmarks[152].y - landmarks[1].y) * image_h
    if y_delta > 80: return "Looking Up"
    elif y_delta < 40: return "Looking Down"
    
    nose = landmarks[1]
    left_ear = landmarks[234]
    right_ear = landmarks[454]
    
    dist_left = euclidean_dist(nose, left_ear)
    dist_right = euclidean_dist(nose, right_ear)
    
    if dist_left / (dist_right + 1e-6) > 1.8: return "Looking Left"
    if dist_right / (dist_left + 1e-6) > 1.8: return "Looking Right"
    
    return "Looking Forward"

# -----------------------------
# MAIN LOOP
# -----------------------------
def main():
    lesson_name = input("Enter lesson name: ").strip()
    
    print("1. Hebrew (he)")
    print("2. English (en)")
    lang_choice = input("Choose language (1/2): ").strip()
    selected_lang = "he" if lang_choice == "1" else "en"
    
    print("\n--- Audio Devices ---")
    mics = sr.Microphone.list_microphone_names()
    for i, name in enumerate(mics):
        try:
            print(f"[{i}] {name}")
        except:
            print(f"[{i}] Microphone {i}")
            
    print("\n IMPORTANT: Select the index of your DJI Mic / USB Audio!")
    mic_idx_input = input("Microphone Index: ").strip()
    mic_index = int(mic_idx_input) if mic_idx_input.isdigit() else None
    
    transcriber = None
    try:
        transcriber = SpeechTranscriber(language=selected_lang, mic_index=mic_index)
        transcriber.start()
    except Exception as e:
        print(f"Audio Error: {e}")

    cam_input = input("Camera Index (0): ").strip()
    cam_index = int(cam_input) if cam_input.isdigit() else 0
    camera = ThreadedCamera(cam_index)
    time.sleep(1.0)

    # --- NEW: AUTO FULL SCREEN SETUP ---
    window_name = "EyeClass Pro Monitor"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    start_time = time.time()
    last_frame_time = start_time
    last_telemetry_time = start_time
    
    attentive_time = 0.0
    distracted_time = 0.0
    phone_event_count = 0
    sleeping_event_count = 0
    telemetry_data = []
    
    phone_active = False
    phone_last_seen = 0
    eyes_closed_start_time = None
    is_sleeping = False
    phone_boxes = []
    frame_count = 0

    while True:
        status, frame = camera.get_frame()
        if not status: break

        now = time.time()
        dt = now - last_frame_time
        last_frame_time = now
        frame_count += 1

        proc = cv2.resize(frame, (PROCESSING_WIDTH, PROCESSING_HEIGHT))
        rgb = cv2.cvtColor(proc, cv2.COLOR_BGR2RGB)
        ph, pw, _ = proc.shape
        
        distraction_reason = ""
        is_distracted_now = False 

        result = face_mesh.process(rgb)
        face_detected = False
        face_landmarks_data = None
        face_object = None
        
        if result.multi_face_landmarks:
            face_detected = True
            face = result.multi_face_landmarks[0]
            face_object = face
            face_landmarks_data = face.landmark
            lms = face.landmark
            
            direction = estimate_head_direction(lms, ph, pw)
            if direction != "Looking Forward": 
                is_distracted_now = True
                distraction_reason = f"Head Turned ({direction})"

            left_ear = calculate_ear(lms, LEFT_EYE_IDXS)
            right_ear = calculate_ear(lms, RIGHT_EYE_IDXS)
            avg_ear = (left_ear + right_ear) / 2.0
            
            if avg_ear < EAR_THRESHOLD:
                if eyes_closed_start_time is None:
                    eyes_closed_start_time = now
                elif (now - eyes_closed_start_time) > SLEEP_TIME_THRESHOLD:
                    if not is_sleeping:
                        sleeping_event_count += 1
                        is_sleeping = True
                    is_distracted_now = True
                    distraction_reason = "Drowsy / Sleeping"
            else:
                eyes_closed_start_time = None
                is_sleeping = False

            if not is_sleeping and not is_distracted_now:
                left_gaze = get_gaze_ratio(lms, LEFT_EYE_IDXS, 468)
                right_gaze = get_gaze_ratio(lms, RIGHT_EYE_IDXS, 473)
                avg_gaze = (left_gaze + right_gaze) / 2.0
                
                if avg_gaze < 0.35 or avg_gaze > 0.65:
                    is_distracted_now = True
                    distraction_reason = "Looking Away from Screen"

        if yolo_net and frame_count % YOLO_FRAME_INTERVAL == 0:
            phone_boxes.clear()
            blob = cv2.dnn.blobFromImage(proc, 1/255.0, (416, 416), swapRB=True)
            yolo_net.setInput(blob)
            outs = yolo_net.forward(output_layers)
            
            for out in outs:
                for det in out:
                    scores = det[5:]
                    cid = np.argmax(scores)
                    if cid == PHONE_CLASS_ID and scores[cid] > 0.5:
                        w, h = int(det[2]*pw), int(det[3]*ph)
                        if (w*h)/(pw*ph) > 0.01:
                            cx, cy = int(det[0]*pw), int(det[1]*ph)
                            phone_boxes.append((cx, cy, w, h))
                            if not phone_active: phone_event_count += 1
                            phone_active = True
                            phone_last_seen = now

        if phone_active:
            if now - phone_last_seen > 0.7: phone_active = False
            else: 
                is_distracted_now = True
                distraction_reason = "Phone Detected"

        if is_distracted_now: distracted_time += dt
        else: attentive_time += dt

        if now - last_telemetry_time >= 1.0:
            telemetry_data.append({
                "timestamp": round(now, 2),
                "relative_time_sec": round(now - start_time, 2),
                "state": "Distracted" if is_distracted_now else "Attentive",
                "reason": distraction_reason if is_distracted_now else "Focused"
            })
            last_telemetry_time = now

        disp = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8)
        
        scale_x = DISPLAY_WIDTH / PROCESSING_WIDTH
        scale_y = DISPLAY_HEIGHT / PROCESSING_HEIGHT

        if face_detected and face_landmarks_data:
            xs = [l.x for l in face_landmarks_data]
            ys = [l.y for l in face_landmarks_data]
            x1, y1 = int(min(xs)*pw*scale_x), int(min(ys)*ph*scale_y)
            x2, y2 = int(max(xs)*pw*scale_x), int(max(ys)*ph*scale_y)
            
            color = (0, 0, 255) if is_distracted_now else (0, 255, 0)
            cv2.rectangle(disp, (x1, y1), (x2, y2), color, 2)
            
            dot_color = (0, 0, 255) if is_distracted_now else (255, 255, 255)
            mp_drawing.draw_landmarks(
                image=disp,
                landmark_list=face_object,
                connections=None, 
                landmark_drawing_spec=mp_drawing.DrawingSpec(color=dot_color, thickness=1, circle_radius=1)
            )
            
            if not is_sleeping:
                lx, ly = int(face_landmarks_data[468].x * pw * scale_x), int(face_landmarks_data[468].y * ph * scale_y)
                rx, ry = int(face_landmarks_data[473].x * pw * scale_x), int(face_landmarks_data[473].y * ph * scale_y)
                cv2.circle(disp, (lx, ly), 3, (0, 255, 255), -1)
                cv2.circle(disp, (rx, ry), 3, (0, 255, 255), -1)

        for (cx, cy, w, h) in phone_boxes:
            x1 = int((cx-w//2)*scale_x)
            y1 = int((cy-h//2)*scale_y)
            x2 = int((cx+w//2)*scale_x)
            y2 = int((cy+h//2)*scale_y)
            cv2.rectangle(disp, (x1, y1), (x2, y2), (0, 0, 255), 3)

        text_items = []
        status_text = "Concentrated" if not is_distracted_now else "Distracted"
        status_color = (0, 255, 0) if not is_distracted_now else (255, 0, 0)
        
        text_items.append((status_text, (20, 20), 28, status_color, None, False))
        
        current_y_offset = 60
        if is_distracted_now and distraction_reason:
             text_items.append((f"Reason: {distraction_reason}", (20, current_y_offset), 22, (255, 100, 100), None, False))
             current_y_offset += 40
             
        # --- NEW: SHOW MUTE STATUS ---
        if transcriber and transcriber.is_muted:
            text_items.append(("MIC MUTED", (20, current_y_offset), 24, (0, 0, 255), None, False))

        if transcriber:
            final_text = transcriber.get_display_text()
            if final_text and not transcriber.is_muted:
                text_items.append((final_text, (DISPLAY_WIDTH - 520, DISPLAY_HEIGHT - 80), 30, (255, 255, 0), None, True))

        if text_items:
            disp = draw_overlay(disp, text_items, max_width_limit=480)

        cv2.imshow(window_name, disp)
        
        # --- NEW: KEY BINDINGS ---
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): 
            break
        elif key == ord('m'):
            if transcriber:
                is_muted = transcriber.toggle_mute()
                state = "Muted" if is_muted else "Unmuted"
                print(f" >> Microphone is now {state}")

    if transcriber: transcriber.stop()
    camera.release()
    cv2.destroyAllWindows()

    total_time = attentive_time + distracted_time
    output = {
        "metadata": {"lesson": lesson_name, "duration_sec": round(total_time, 2)},
        "analysis": {
            "attentive_sec": round(attentive_time, 2),
            "distracted_sec": round(distracted_time, 2),
        },
        "behavior": {
             "phone_events": phone_event_count,
             "drowsy_events": sleeping_event_count
        },
        "transcription": transcriber.get_log() if transcriber else [],
        "telemetry": telemetry_data  
    }

    path = os.path.join(JSON_DIR, f"{lesson_name}_data.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)
    
    print_hebrew(f"Saved to {path}")

if __name__ == "__main__":
    main()