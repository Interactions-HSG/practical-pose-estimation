import time
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
import numpy as np

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = vision.PoseLandmarker
PoseLandmarkerOptions = vision.PoseLandmarkerOptions
PoseLandmarkerResult = vision.PoseLandmarkerResult
VisionRunningMode = vision.RunningMode
model_path = 'trained_models/pose_landmarker_full.task'

# Pose connections from MediaPipe see webpage for reference https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32),
]
latest_result = None


def main():
    # Create a pose landmarker instance with the live stream mode:
    mode = input("Enter '1' for video file input or '2' for webcam input: ")

    if mode == '1':
        options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.VIDEO)
    else:
        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.LIVE_STREAM,
            result_callback=print_result)
    
    with PoseLandmarker.create_from_options(options) as landmarker:
        if mode == '1':
            video = cv2.VideoCapture('videos/test.mov')
        else:
            video  = cv2.VideoCapture(0)

        print("Starting pose estimation...")
        while True:
            detection_result, frame = process_video(video, landmarker, mode)

            if latest_result:
                annotated_frame = draw_landmarks_on_image(frame, latest_result)
            elif detection_result and mode == '1':
                annotated_frame = draw_landmarks_on_image(frame, detection_result)
            else:
                print("No pose landmarks detected.")
                annotated_frame = frame
            cv2.imshow('Pose Landmarker', annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cv2.destroyAllWindows()


def print_result(result: PoseLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global latest_result
    latest_result = result

def process_video(video, landmarker, mode):
    if not video.isOpened():
        print("Error: Could not open video.")
        SystemExit()

    status, frame = video.read()
    timestamp = int(time.perf_counter() * 1000)
    if not status:
        print("End of video or cannot read the frame.")
        SystemExit()

    # Convert the frame received from OpenCV to a MediaPipe’s Image object.
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    if mode == '1':
        detection_result = landmarker.detect_for_video(mp_image, timestamp)
    else:
        detection_result = landmarker.detect_async(mp_image, timestamp)
    return detection_result, frame

def draw_landmarks_on_image(rgb_image, detection_result):
    h, w, c = rgb_image.shape
    annotated_image = np.copy(rgb_image)
    
    # Loop through detected poses
    for landmarks in detection_result.pose_landmarks:
        for start_idx, end_idx in POSE_CONNECTIONS:
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                start = landmarks[start_idx]
                end = landmarks[end_idx]
                
                # Only draw if confidence is high enough
                if start.presence > 0.5 and end.presence > 0.5:
                    start_pos = (int(start.x * w), int(start.y * h))
                    end_pos = (int(end.x * w), int(end.y * h))
                    cv2.line(annotated_image, start_pos, end_pos, (0, 255, 0), 4)
        
        # Draw landmarks as circles
        for landmark in landmarks:
            if landmark.presence > 0.5:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                cv2.circle(annotated_image, (x, y), 8, (0, 0, 255), -1)
    
    return annotated_image


main()







