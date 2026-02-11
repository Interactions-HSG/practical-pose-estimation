import time
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
import numpy as np


class PoseEstimator:
    # Pose connections from MediaPipe see webpage for reference https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker
    POSE_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
        (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
        (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
        (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
        (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32),
    ]

    def __init__(self, mode: str, model_path: str = '../trained_models/pose_landmarker_full.task'):
        self.model_path = model_path
        self.mode = mode
        self.latest_result = None

        self.BaseOptions = mp.tasks.BaseOptions
        self.PoseLandmarker = vision.PoseLandmarker
        self.PoseLandmarkerOptions = vision.PoseLandmarkerOptions
        self.VisionRunningMode = vision.RunningMode
        self.PoseLandmarkerResult = vision.PoseLandmarkerResult

        self.landmarker = self._create_landmarker()
        self.video = self._open_video_source()

    def _create_landmarker(self):
        if self.mode == '1':
            options = self.PoseLandmarkerOptions(
                base_options=self.BaseOptions(model_asset_path=self.model_path),
                running_mode=self.VisionRunningMode.VIDEO
            )
        else:
            options = self.PoseLandmarkerOptions(
                base_options=self.BaseOptions(model_asset_path=self.model_path),
                running_mode=self.VisionRunningMode.LIVE_STREAM,
                result_callback=self._result_callback
            )

        return self.PoseLandmarker.create_from_options(options)

    def _open_video_source(self):
        if self.mode == '1':
            cap = cv2.VideoCapture('../videos/test2.mov')
        else:
            cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            raise RuntimeError("Could not open video source")

        return cap

    def _result_callback(self, result, output_image, timestamp_ms):
        self.latest_result = result

    def _process_frame(self):
        status, frame = self.video.read()
        if not status:
            return None

        timestamp = int(time.perf_counter() * 1000)

        # Convert the frame received from OpenCV to a MediaPipe’s Image object.
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

        if self.mode == '1':
            self.latest_result = self.landmarker.detect_for_video(mp_image, timestamp)
        else:
            self.landmarker.detect_async(mp_image, timestamp)

        return frame

    def _draw_landmarks(self, image, result):
        if not result:
            return image

        h, w, _ = image.shape
        annotated_frame = image.copy()

        for landmarks in result.pose_landmarks:
            for start_idx, end_idx in self.POSE_CONNECTIONS:
                if start_idx < len(landmarks) and end_idx < len(landmarks):
                    start = landmarks[start_idx]
                    end = landmarks[end_idx]

                    # Only draw if confidence is high enough
                    if start.presence > 0.75 and end.presence > 0.75:
                        p1 = (int(start.x * w), int(start.y * h))
                        p2 = (int(end.x * w), int(end.y * h))
                        cv2.line(annotated_frame, p1, p2, (0, 255, 0), 4)

            for lm in landmarks:
                if lm.presence > 0.75:
                    x, y = int(lm.x * w), int(lm.y * h)
                    cv2.circle(annotated_frame, (x, y), 8, (255, 255, 0), -1)
                    cv2.circle(annotated_frame, (x, y), 8, (0, 0, 0), 2)

        return annotated_frame
    
    def get_landmarks_result(self):
        # Use 3D real-world (in meters) coordinates for more accurate angle and distance calculations, and include visibility and presence for form checks
        if not self.latest_result or not self.latest_result.pose_world_landmarks:
            return None
        
        landmarks = self.latest_result.pose_world_landmarks[0]
        
        result = []
        for lm in landmarks:
            result.append([lm.x, lm.y, lm.z, lm.visibility, lm.presence])
        
        # Returns a 33 x 5 Numpy Array (Matrix) for the 33 landmarks
        return np.array(result, dtype=np.float32)

    def run(self):
        frame = self._process_frame()
        if frame is None:
            return None
        annotated = self._draw_landmarks(frame, self.latest_result)
        return annotated   

    def cleanup(self):
        self.video.release()
        cv2.destroyAllWindows()
        self.landmarker.close()