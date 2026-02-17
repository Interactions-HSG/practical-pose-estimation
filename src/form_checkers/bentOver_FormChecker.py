import numpy as np
from ._angleCalculator import calculate_angle
import cv2

class BentOverRowFormChecker:
    def check_bentover_form(self, annotated, landmarks: np.array):
        if landmarks is None or landmarks.shape[0] != 33:
            print("Insufficient landmarks for bent-over row form check.")
            return annotated
    
        self.annotated = annotated
        
        # Set up for text display
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.line = cv2.LINE_AA
        self.green = (0, 255, 0)
        self.red = (0, 0, 255)

        #Relevant landmarks for row check form
        self.left_shoulder = landmarks[11]
        self.left_ellbow = landmarks[13]
        self.left_wrist = landmarks[15]
        self.left_hip = landmarks[23]
        self.left_knee = landmarks[25]

        self.right_shoulder = landmarks[12]
        self.right_ellbow = landmarks[14]
        self.right_wrist = landmarks[16]
        self.right_hip = landmarks[24]
        self.right_knee = landmarks[26]

        # Check if required landmarks have sufficient visibility
        required_landmarks = [self.right_shoulder, self.right_ellbow, self.right_wrist, self.right_hip, self.right_knee, 
                              self.left_shoulder, self.left_ellbow, self.left_wrist, self.left_hip, self.left_knee]

        if any(landmark[4] < 0.95 for landmark in required_landmarks):
            cv2.putText(self.annotated, "Please adjust the camera for better visibility.", (10, 60), self.font, 1.25, self.red, 2, self.line)
        else:
            self._check_back_form()

    

    def _check_back_form(self):
        hip_below_left = [self.left_hip[0], self.left_hip[1] - 1, self.left_hip[2]]
        hip_below_right = [self.right_hip[0], self.right_hip[1] - 1, self.right_hip[2]]
        torso_inclination_left = calculate_angle(self.left_shoulder[:3], self.left_hip[:3], hip_below_left)
        torso_inclination_right = calculate_angle(self.right_shoulder[:3], self.right_hip[:3], hip_below_right)

        torso_lean_left = calculate_angle(self.left_shoulder[:3], self.left_hip[:3], self.left_knee[:3])
        torso_lean_right = calculate_angle(self.right_shoulder[:3], self.right_hip[:3], self.right_knee[:3])

        # Check if the torso is too horizontal or too upright and provide feedback accordingly with additional thresholds for bent-over rows
        if torso_lean_left > 100 or torso_lean_right > 100:
            cv2.putText(self.annotated, "BACK FORM: Try to keep the trunk more horizontal.", (10, 100), self.font, 1.25, self.red, 2, cv2.LINE_AA)
        elif torso_inclination_left > 65 and torso_inclination_right > 65:
            cv2.putText(self.annotated, "BACK FORM: Try to keep the trunk upright.", (10, 100), self.font, 1.25, self.red, 2, cv2.LINE_AA)
        else:
            cv2.putText(self.annotated, "BACK FORM: Good back form.", (10, 100), self.font, 1.25, self.green, 2, cv2.LINE_AA)

    def _check_range_of_motion(self):
        return
    
    