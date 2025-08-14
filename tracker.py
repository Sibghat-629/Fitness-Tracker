import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog
from threading import Thread
from PIL import Image, ImageTk

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose()

# Exercise Tracking Variables
exercise = None
counter = 0
stage = None
video_path = None

def calculate_angle(a, b, c):
    """Calculate the angle between three points."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    return angle if angle <= 180 else 360 - angle

def process_frame(image):
    """Process each frame for pose detection."""
    global counter, stage, exercise

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)
    
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        landmarks = results.pose_landmarks.landmark

        shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                 landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                 landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
               landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                 landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

        if exercise == "Squats":
            angle = calculate_angle(hip, knee, ankle)
            if angle < 90:
                stage = "down"
            elif angle > 160 and stage == "down":
                stage = "up"
                counter += 1

        elif exercise == "Dumbbell Curls":
            angle = calculate_angle(shoulder, elbow, wrist)
            if angle > 160:
                stage = "down"
            elif angle < 50 and stage == "down":
                stage = "up"
                counter += 1

        elif exercise == "Push-ups":
            angle = calculate_angle(shoulder, elbow, wrist)
            if angle < 90:
                stage = "down"
            elif angle > 160 and stage == "down":
                stage = "up"
                counter += 1

        elif exercise == "Pull-ups":
            head = [landmarks[mp_pose.PoseLandmark.NOSE.value].x, landmarks[mp_pose.PoseLandmark.NOSE.value].y]
            chin = [landmarks[mp_pose.PoseLandmark.MOUTH_BOTTOM.value].x, landmarks[mp_pose.PoseLandmark.MOUTH_BOTTOM.value].y]

            if head[1] < shoulder[1]:  # Head is above shoulders
                stage = "up"
            elif head[1] > shoulder[1] and stage == "up":  # Dropping back down
                stage = "down"
                counter += 1

        cv2.putText(image, f'Count: {counter}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    return image

def start_camera(video_source=0):
    """Open the camera or process a video file."""
    cap = cv2.VideoCapture(video_source)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)  # Mirror effect
        
        # Resize the frame before processing (reduce to 50% of original size)
        frame = cv2.resize(frame, (frame.shape[1] // 2, frame.shape[0] // 2))

        frame = process_frame(frame)

        cv2.imshow('AI Fitness Trainer', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def select_exercise():
    """Set the selected exercise and start the camera."""
    global exercise, counter, stage, video_path
    exercise = exercise_var.get()
    counter, stage = 0, None
    
    if video_path:
        Thread(target=start_camera, args=(video_path,), daemon=True).start()
    else:
        Thread(target=start_camera, daemon=True).start()

def upload_video():
    """Allow the user to select a video file."""
    global video_path
    video_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4;*.avi;*.mov")])
    if video_path:
        video_label.config(text=f"Video: {video_path.split('/')[-1]}")
    
# Tkinter UI
root = tk.Tk()
root.title("AI Fitness Trainer")
root.geometry("600x500")
root.configure(bg="#1e1e1e")

# Header
header = tk.Label(root, text="AI Fitness Trainer", font=("Arial", 18, "bold"), fg="#ffffff", bg="#333333", pady=10)
header.pack(fill="x")

# Exercise Selection
frame = tk.Frame(root, bg="#1e1e1e")
frame.pack(pady=20)

tk.Label(frame, text="Select Exercise", font=("Arial", 14), fg="#ffffff", bg="#1e1e1e").pack()

exercise_var = tk.StringVar(value="Squats")
exercises = ["Squats", "Dumbbell Curls", "Push-ups", "Pull-ups"]

for ex in exercises:
    ttk.Radiobutton(frame, text=ex, variable=exercise_var, value=ex, style="Custom.TRadiobutton").pack(anchor="w")

# Upload Video Button
video_label = tk.Label(root, text="No video selected", fg="white", bg="#1e1e1e")
video_label.pack()
upload_btn = ttk.Button(root, text="Upload Video", command=upload_video)
upload_btn.pack(pady=10)

# Start Button
start_btn = ttk.Button(root, text="Start Exercise", command=select_exercise)
start_btn.pack(pady=10)

# Exit Button
exit_btn = ttk.Button(root, text="Exit", command=root.quit)
exit_btn.pack(pady=10)

# Style
style = ttk.Style()
style.configure("Custom.TRadiobutton", background="#1e1e1e", foreground="white", font=("Arial", 12))

root.mainloop()
