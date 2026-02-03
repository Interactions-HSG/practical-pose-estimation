import cv2
import numpy as np
from ._angleCalculator import calculate_angle

class SquatFormChecker:
    def __init__(self,landmarks: np.array):

        self.right_hip = landmarks[23] 
        self.right_knee = landmarks[25]
        self.right_ankle = landmarks[27] 

        self.left_hip = landmarks[24]
        self.left_knee = landmarks[26]
        self.left_ankle = landmarks[28]  

        if landmarks is None or landmarks.shape[0] != 33:
            print("Insufficient landmarks for squat form check.")
            return

    def check_Squat_form(self, annotated):
        if self.right_hip[4] < 0.95 or self.right_knee[4] < 0.95 or self.right_ankle[4] < 0.95 or self.left_hip[4] < 0.95 or self.left_knee[4] < 0.95 or self.left_ankle[4] < 0.95:
            cv2.putText(annotated, "Please adjust the camera for better visibility.", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
        else:
            annotated = self._check_depth(annotated)
            # self._check_back_form() can add more text later

        return annotated

    def _check_depth(self, annotated):
        right_knee_angle = calculate_angle(self.right_hip[:3], self.right_knee[:3], self.right_ankle[:3])
        left_knee_angle = calculate_angle(self.left_hip[:3], self.left_knee[:3], self.left_ankle[:3])

        # Check if the squat depth is adequate
        if 160 > right_knee_angle and 160 > left_knee_angle:
            if right_knee_angle <= 110 and left_knee_angle <= 110:
                cv2.putText(annotated, "DEPTH: Good squat depth achieved.", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            else:
                cv2.putText(annotated, "DEPTH: Try to squat lower to achieve better depth.", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        
        return annotated

    def _check_back_form(self):
        pass 
    
