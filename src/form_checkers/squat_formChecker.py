import cv2
import numpy as np
from ._angleCalculator import calculate_angle

class SquatFormChecker:

    def check_Squat_form(self, annotated, landmarks: np.array, depth_achieved):
        if landmarks is None or landmarks.shape[0] != 33:
            print("Insufficient landmarks for squat form check.")
            return annotated, depth_achieved
        
        self.left_hip = landmarks[23] 
        self.left_knee = landmarks[25]
        self.left_ankle = landmarks[27] 
        self.left_toe = landmarks[31]

        self.right_hip = landmarks[24]
        self.right_knee = landmarks[26]
        self.right_ankle = landmarks[28]  
        self.right_toe = landmarks[32]
        
        if self.right_hip[4] < 0.95 or self.right_knee[4] < 0.95 or self.right_ankle[4] < 0.95 or self.left_hip[4] < 0.95 or self.left_knee[4] < 0.95 or self.left_ankle[4] < 0.95:
            cv2.putText(annotated, "Please adjust the camera for better visibility.", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 255), 2, cv2.LINE_AA)
        else:
            depth_achieved = self._check_depth(annotated, depth_achieved)
            self._check_knee_tracking(annotated)
            # self._check_back_form() can add more text later
    

        return depth_achieved

    def _check_depth(self, annotated, depth_achieved):
        right_knee_angle = calculate_angle(self.right_hip[:3], self.right_knee[:3], self.right_ankle[:3])
        left_knee_angle = calculate_angle(self.left_hip[:3], self.left_knee[:3], self.left_ankle[:3])
        
        # Convert normalized coordinates to pixel coordinates for display
        h, w, _ = annotated.shape
        right_knee_x = int(self.right_knee[0] * w)
        right_knee_y = int(self.right_knee[1] * h)
        
        cv2.putText(annotated, str(int(right_knee_angle)), (right_knee_x - 70, right_knee_y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2, cv2.LINE_AA)

        left_knee_x = int(self.left_knee[0] * w)
        left_knee_y = int(self.left_knee[1] * h)

        cv2.putText(annotated, str(int(left_knee_angle)), (left_knee_x + 20, left_knee_y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2, cv2.LINE_AA)

        # Check if the squat depth is adequate
        if 160 > right_knee_angle and 160 > left_knee_angle:
            if right_knee_angle <= 110 and left_knee_angle <= 110:
                depth_achieved = True
                cv2.putText(annotated, "DEPTH: Good squat depth achieved.", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (0, 255, 0), 2, cv2.LINE_AA)
            elif depth_achieved == False:
                cv2.putText(annotated, "DEPTH: Try to squat lower to achieve better depth.", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (0, 0, 255), 2, cv2.LINE_AA)
        else:
            depth_achieved = False

        return annotated, depth_achieved

    def _check_knee_tracking(self, annotated):
        if (self.right_knee[2] < self.left_knee[2] and self.right_ankle[2] < self.left_ankle[2] and self.right_hip[2] < self.left_hip[2]):
            if self.right_knee[0] > self.right_toe[0] or self.left_knee[0] > self.left_toe[0]:
                cv2.putText(annotated, "KNEE TRACKING: Do not move Knees past the toes.", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (0, 0, 255), 2, cv2.LINE_AA)
            else:
                cv2.putText(annotated, "KNEE TRACKING: Knees are behind toes.", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (0, 255, 0), 2, cv2.LINE_AA)
        else:
            if self.right_knee[0] < self.right_toe[0] or self.left_knee[0] < self.left_toe[0]:
                    cv2.putText(annotated, "KNEE TRACKING: Do not move Knees past the toes.", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (0, 0, 255), 2, cv2.LINE_AA)
            else:
                cv2.putText(annotated, "KNEE TRACKING: Knees are behind toes.", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (0, 255, 0), 2, cv2.LINE_AA)

    def _check_back_form(self):
        pass 

 