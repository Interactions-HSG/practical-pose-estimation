import time
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.components import containers

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = vision.PoseLandmarker
PoseLandmarkerOptions = vision.PoseLandmarkerOptions
PoseLandmarkerResult = vision.PoseLandmarkerResult
VisionRunningMode = vision.RunningMode
model_path = 'trained_models/pose_landmarker_full.task'


def main():
    # Create a pose landmarker instance with the live stream mode:
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=print_result)
    
    with PoseLandmarker.create_from_options(options) as landmarker:
        video  = cv2.VideoCapture(0)
        while True:
            detection_result, frame = process_video(video, landmarker)
            annotated_frame = draw_landmarks(frame, detection_result)
            cv2.imshow('Pose Landmarker', annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cv2.destroyAllWindows()


def print_result(result: PoseLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    print('Pose landmarker result: {}'.format(result))

def process_video(video, landmarker):
    if not video.isOpened():
        print("Error: Could not open video.")
    else:
        print("Video capture started successfully.")

    status, frame = video.read()
    timestamp = int(time.perf_counter() * 1000)
    if not status:
        print("End of video or cannot read the frame.")
        SystemExit()

    # Convert the frame received from OpenCV to a MediaPipe’s Image object.
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    detection_result = landmarker.detect_async(mp_image, timestamp)
    return detection_result, frame

def draw_landmarks(rgb_image, detection_result):
    # Das Bild muss für OpenCV bearbeitbar sein
    annotated_image = rgb_image.copy()
    height, width, _ = annotated_image.shape

    for pose_landmarks in detection_result.pose_landmarks:
        # 1. Zeichne die Punkte
        for landmark in pose_landmarks:
            x_px = int(landmark.x * width)
            y_px = int(landmark.y * height)
            cv2.circle(annotated_image, (x_px, y_px), 4, (0, 255, 0), -1)

        # 2. Zeichne die Verbindungen (optional)
        # Die Verbindungen musst du bei Tasks oft manuell definieren 
        # oder aus der Dokumentation übernehmen
    return annotated_image


main()







