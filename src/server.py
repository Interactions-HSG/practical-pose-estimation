from fastapi import Request
from fastapi.responses import JSONResponse
import os
import sys
from feedback_ai import generate_ai_feedback
from contextlib import asynccontextmanager
from init_functions import download_packets, create_required_directories
from uuid import uuid4

# Make sure imports from src/ work when running from the src/ directory
sys.path.insert(0, os.path.dirname(__file__))

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pose_estimator import PoseEstimator
from pose_estimator_supine import PoseEstimatorSupine
from form_checkers import SquatFormChecker, BenchpressFormChecker, BentOverRowFormChecker

FEEDBACK_DIR = create_required_directories('src/feedback')

def initialize_app_resources() -> None:
    # Prepare required directories and model files once at API startup.
    trained_models_dir = create_required_directories('trained_models')
    create_required_directories('src/feedback')

    pose_model_path = os.path.join(trained_models_dir, 'pose_landmarker_full.task')
    download_packets(pose_model_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_app_resources()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/feedback", StaticFiles(directory=FEEDBACK_DIR), name="feedback")

# Video Delete Endpoint for feedback videos
@app.post("/delete_video")
async def delete_video(request: Request):
    data = await request.json()
    rel_path = data.get("path", "")
    if not rel_path or "/" in rel_path.strip("/"):
        return JSONResponse({"status": "error", "detail": "Invalid path."}, status_code=400)
    public_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "public")
    abs_path = os.path.abspath(os.path.join(public_dir, rel_path.lstrip("/")))
    if not abs_path.startswith(public_dir):
        return JSONResponse({"status": "error", "detail": "Invalid path."}, status_code=400)
    if os.path.exists(abs_path):
        try:
            os.remove(abs_path)
            return {"status": "success", "detail": f"Deleted {rel_path}"}
        except Exception as e:
            return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
    
    else:
        return {"status": "success", "detail": f"File {rel_path} does not exist."}
    
@app.post("/delete_snapshot")
async def delete_snapshot():
    snapshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "snapshots")
    if os.path.exists(snapshots_dir):
        try:
            for filename in os.listdir(snapshots_dir):
                file_path = os.path.join(snapshots_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            return {"status": "success", "detail": "Deleted all snapshots."}
        except Exception as e:
            return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)

# HTTP Upload Endpoint 
@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
):
    public_dir = os.path.dirname(os.path.abspath(__file__)) + "/frontend/public"
    filename = f"{file.filename}"
    save_path = os.path.join(public_dir, filename)
    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"status": "success", "filename": filename}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "https://renato-unpardoning-palatably.ngrok-free.dev"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API call for generating AI feedback based on collected raw feedbacks and the current exercise
@app.post("/generate_feedback")
async def generate_feedback(request: Request):
    data = await request.json()
    session_id = data.get("sessionId")
    currentExercise = data.get("exercise", "unknown")
    session = ACTIVE_SESSIONS.get(session_id)
    if not session:
        return JSONResponse({"error": "Session not found"}, status_code=404)

    feedbacks = session.accumulated_feedbacks.copy()
    session.accumulated_feedbacks.clear()

    feedback = generate_ai_feedback(feedbacks, currentExercise)
    session.close() 
    ACTIVE_SESSIONS.pop(session_id, None)  
    return {"feedback": feedback}

# Decode an incoming JPEG blob into an OpenCV frame
def jpeg_to_frame(data: bytes) -> np.ndarray | None:
    """Convert raw JPEG bytes (sent by the browser) into an OpenCV BGR image."""
    arr = np.frombuffer(data, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return frame  # None if decoding failed


# Encode an OpenCV frame back to JPEG bytes
def frame_to_jpeg(frame: np.ndarray, quality: int = 75) -> bytes:
    """Encode an OpenCV BGR image as JPEG bytes to send back to the browser."""
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes()

class ExerciseSession:
    def __init__(self, exercise: str):
        self.exercise = exercise
        self.rom_achieved = False
        self.init_pos = True
        self.pending_audio_events = []
        self.initial_detection_timer_done = False
        self.detected = False
        self.lastDetectedStatus = None
        self.lastTimerStatus = None
        self.last_rep_counter = 0
        self.rep_counter = 0
        self.raw_feedbacks = [] 
        self.accumulated_feedbacks = []
        self.currentExercise = None

        if exercise in ("squat", "bent"):
            self.estimator = PoseEstimator(mode='image', open_camera=False)
        else:
            self.estimator = PoseEstimatorSupine(mode='image', open_camera=False)

        if exercise == "squat":
            self.checker = SquatFormChecker(tts=True, play_local_audio=False, queue_audio_event=self.queue_audio_event)
        elif exercise == "bench":
            self.checker = BenchpressFormChecker(tts=True, play_local_audio=False, queue_audio_event=self.queue_audio_event)
        else: 
            self.checker = BentOverRowFormChecker(tts=True, play_local_audio=False, queue_audio_event=self.queue_audio_event)

    def queue_audio_event(self, filepath: str, text: str, color: tuple[int, int, int]) -> None:
        color_name = "green" if color == (0, 255, 0) else "red" if color == (0, 0, 255) else "unknown"
        normalized_path = filepath.lstrip("./").replace("\\", "/")
        if normalized_path.startswith("feedback/"):
            normalized_path = normalized_path[len("feedback/"):]
        self.pending_audio_events.append(
            {
                "type": "audio_feedback",
                "path": normalized_path,
                "text": text,
                "color": color_name,
            }
        )

    def pop_audio_events(self) -> list[dict]:
        events = self.pending_audio_events
        self.pending_audio_events = []
        return events

    # Process a single frame
    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Runs the same steps as the while-loop in main.py on a single frame.
        Returns the annotated frame (skeleton + feedback text drawn on it).
        """

        if self.exercise in ("squat", "bent"):
            # 1. Run PoseEstimator on the externally provided frame.
            annotated = self.estimator.process_external_frame(frame)

            # 2. Run form checker with 33x5 landmarks.
            points = self.estimator.get_landmarks_result()
            if points is not None:

                if self.exercise == "squat":
                    self.rom_achieved, self.init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks = self.checker.check_Squat_form(
                        annotated, points, self.rom_achieved, self.init_pos
                    )
                    self.currentExercise = "squat"
                else:
                    self.rom_achieved, self.init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks = self.checker.check_bentover_form(
                        annotated, points, self.rom_achieved, self.init_pos
                    )
                    self.currentExercise = "bent"

            for item in self.raw_feedbacks:
              if isinstance(item, (str, dict)):
                  self.accumulated_feedbacks.append(item)
            self.raw_feedbacks.clear()

        elif self.exercise == "bench":
            # 1. Run supine estimator on one frontend-provided frame.
            annotated = self.estimator.process_external_frame(frame)

            # 2. Run bench checker with highest-confidence person.
            people = self.estimator.get_landmarks_result()
            if people is not None:
                best_idx = int(people[:, :, 2].mean(axis=1).argmax())
                points = people[best_idx]
                self.rom_achieved, self.init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks = self.checker.check_benchpress_form(
                    annotated, points, self.rom_achieved, self.init_pos
                )
                self.currentExercise = "bench"

        return annotated

    def close(self):
        if hasattr(self, "estimator") and hasattr(self.estimator, "landmarker"):
            self.estimator.landmarker.close()


ACTIVE_SESSIONS: dict[str, ExerciseSession] = {}

# WebSocket endpoint
@app.websocket("/livestream")
async def livestream_endpoint(websocket: WebSocket, exercise: str = "squat"):
    """
    The browser connects here, sends JPEG frames, receives annotated JPEG frames.
    """
    await websocket.accept()
    session_id = str(uuid4())
    session = ExerciseSession(exercise)
    ACTIVE_SESSIONS[session_id] = session
    http_scheme = "https" if websocket.url.scheme == "wss" else "http"
    host = websocket.headers.get("host")
    if not host:
        host = websocket.url.netloc
    http_base = f"{http_scheme}://{host}"

    await websocket.send_json({"type": "session_id", "session_id": session_id})
    
    try:
        while True:
            # 1. Receive either a raw JPEG frame or a JSON control message
            try:
                message = await websocket.receive()
            except (WebSocketDisconnect, RuntimeError):
                break

            if "bytes" in message:
                # JPEG frame from browser
                data = message["bytes"]
                frame = jpeg_to_frame(data)
                if frame is None:
                    continue  # skip unreadable frames

                # 3. Run the full pipeline (pose + skeleton + form check)
                annotated = session.process(frame)

                # 4. Encode result back to JPEG and send to browser
                await websocket.send_bytes(frame_to_jpeg(annotated))

                if session.lastDetectedStatus != session.detected or session.lastTimerStatus != session.initial_detection_timer_done or session.last_rep_counter != session.rep_counter:
                    await websocket.send_json({
                        "type": "detection_status",
                        "detected": session.detected,
                        "timer_done": session.initial_detection_timer_done
                    })

                session.lastDetectedStatus = session.detected
                session.lastTimerStatus = session.initial_detection_timer_done

                if session.rep_counter != session.last_rep_counter:
                    await websocket.send_json({
                        "type": "rep_update",
                        "rep_counter": session.rep_counter
                    })
                    session.last_rep_counter = session.rep_counter

                # 5. Send any queued audio feedback events (as JSON on the same WebSocket)
                for audio_event in session.pop_audio_events():
                    # Build the audio URL based on the backend URL
                    audio_path = audio_event.get("path", "")
                    audio_url = f"{http_base}/feedback/{audio_path}"

                    # Send the audio feedback as a JSON message
                    await websocket.send_json({
                        "type": "audio_feedback",
                        "url": audio_url,
                        "text": audio_event.get("text", ""),
                        "color": audio_event.get("color", "unknown"),
                    })

            elif "text" in message:
                # JSON control message from browser
                try:
                    payload = message["text"]
                    import json
                    data = json.loads(payload)
                    if isinstance(data, dict) and data.get("type") == "reset_reps":
                        # Reset rep counter in session
                        if hasattr(session, "rep_counter"):
                            session.rep_counter = 0
                            session.last_rep_counter = 0
                except Exception:
                    pass  # ignore malformed control messages

    except Exception as e:
        pass  # browser closed the tab or stopped the stream