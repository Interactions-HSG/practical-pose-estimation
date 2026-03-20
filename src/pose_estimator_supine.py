from ultralytics import YOLO
import cv2
import numpy as np


class PoseEstimatorSupine:
    '''
    This class is responsible for estimating human poses in a supine position using the YOLOv8 pose estimation model instead of MediaPipe. 
    '''
    POSE_CONNECTIONS = [
        (0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 7), (6, 8), (7, 9), (8, 10),
          (5, 11), (6, 12), (11, 12), (11, 13), (12, 14), (13, 15), (14, 16)
    ]

    def __init__(self, mode: str, open_camera: bool = True):
        self.source = '../videos/test11.mov'
        self.results = None
        self.mode = mode
        self.model = YOLO('../trained_models/yolo26s-pose.pt') 
        if open_camera:
            self.video = self._open_video_source()
        else:
            self.video = None


    def _open_video_source(self):
        if self.mode == '1':
            cap = cv2.VideoCapture(self.source)
        else:
            cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            raise RuntimeError("Could not open video source")

        return cap

    def _process_frame(self):
        if self.video is None:
            return None

        status, frame = self.video.read()
        if not status:
            return None

        self.results = self._predict(frame)
        return frame

    def _predict(self, frame):
        try:
            # Set verbose false to reduce console output
            return self.model.predict(source=frame, conf=0.5, verbose=False)
        except Exception as e:
            print(f"Error in prediction: {e}")
            return None

    def process_external_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process one frame provided externally (e.g., frontend WebSocket)."""
        self.results = self._predict(frame)
        return self._draw_landmarks(frame, self.results)

    def _draw_landmarks(self, image, results=None):
        if results is None:
            results = self.results
        if not results:
            print("No results to draw.")
            return image
        
        annotated_frame = image.copy()
        
        for result in results:
            if result.keypoints is None or result.keypoints.data is None:
                continue

            # Normalize shape so we always iterate over persons: (num_people, 17, 3) / (1, 17, 3) for a single person.
            # YOLO returns keypoints in a tensor format, convert to numpy first usig .cpu().numpy()
            landmarks = result.keypoints.data.cpu().numpy()
            if landmarks.ndim == 2:
                landmarks = np.expand_dims(landmarks, axis=0)

            for person_keypoints in landmarks:
                keypoints = person_keypoints
                
                for start_idx, end_idx in self.POSE_CONNECTIONS:
                    if start_idx < len(keypoints) and end_idx < len(keypoints):
                        start = keypoints[start_idx]
                        end = keypoints[end_idx]
                    
                        if start[2] > 0.5 and end[2] > 0.5:
                            p1 = (int(start[0]), int(start[1]))
                            p2 = (int(end[0]), int(end[1]))
                            cv2.line(annotated_frame, p1, p2, (0, 255, 0), 4)
                            
                for kp in keypoints:
                    if kp[2] > 0.5: 
                        x, y = int(kp[0]), int(kp[1])
                        cv2.circle(annotated_frame, (x, y), 8, (255, 255, 0), -1)
                        cv2.circle(annotated_frame, (x, y), 8, (0, 0, 0), 2)

        return annotated_frame

    def get_landmarks_result(self):
        if not self.results:
            return None
        
        all_landmarks = []
        for result in self.results:
            if result.keypoints is None or result.keypoints.data is None:
                continue
            landmarks = result.keypoints.data.cpu().numpy()

            # Handle both single-person (1, 17,3) and multi-person (N,17,3) outputs.
            if landmarks.ndim == 2:
                landmarks = np.expand_dims(landmarks, axis=0)

            for person_keypoints in landmarks:
                all_landmarks.append(person_keypoints.tolist())

        if not all_landmarks:
            return None

        return np.array(all_landmarks, dtype=np.float32)
        
    def run(self):
        frame = self._process_frame()
        if frame is None:
            return None
        annotated = self._draw_landmarks(frame)
        return annotated   

    def _cleanup(self):
        if self.video is not None:
            self.video.release()
        cv2.destroyAllWindows()
        