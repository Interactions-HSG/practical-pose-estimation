import cv2
import numpy as np
from ._angleCalculator import calculate_angle, findAngle

class SquatFormChecker:
    '''
    This class is responsible for checking the form of a squat exercise using pose landmarks. It evaluates squat depth and knee tracking as well as checking the form of the back providing real-time feedback on the form.
    '''

    def check_Squat_form(self, annotated, landmarks: np.array, depth_achieved):
        if landmarks is None or landmarks.shape[0] != 33:
            print("Insufficient landmarks for squat form check.")
            return annotated, depth_achieved

        self.annotated = annotated
        
        # Set up for text display
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.line = cv2.LINE_AA
        self.green = (0, 255, 0)
        self.red = (0, 0, 255)

        #Relevant landmarks for squat form check
        self.left_hip = landmarks[23] 
        self.left_knee = landmarks[25]
        self.left_ankle = landmarks[27] 
        self.left_toe = landmarks[31]
        self.left_shoulder = landmarks[11]
        self.left_heel = landmarks[29]

        self.right_hip = landmarks[24]
        self.right_knee = landmarks[26]
        self.right_ankle = landmarks[28]  
        self.right_toe = landmarks[32] 
        self.right_shoulder = landmarks[12]
        self.right_heel = landmarks[30]

        self.right_knee_angle = calculate_angle(self.right_hip[:3], self.right_knee[:3], self.right_ankle[:3])
        self.left_knee_angle = calculate_angle(self.left_hip[:3], self.left_knee[:3], self.left_ankle[:3])

    
        if self.right_hip[4] < 0.95 or self.right_knee[4] < 0.95 or self.right_ankle[4] < 0.95 or self.left_hip[4] < 0.95 or self.left_knee[4] < 0.95 or self.left_ankle[4] < 0.95:
            cv2.putText(self.annotated, "Please adjust the camera for better visibility.", (10, 60), self.font, 1.25, self.red, 2, self.line)
        else:
            depth_achieved = self._check_depth(depth_achieved)
            if 155 > self.right_knee_angle and 155 > self.left_knee_angle:
                self._check_knee_tracking()
                self._check_back_form()

        return depth_achieved

    def _check_depth(self, depth_achieved):
        # Check if the squat depth is adequate and do not check if depth already achieved or if the person is upright
        if 160 > self.right_knee_angle and 160 > self.left_knee_angle:
            if self.right_knee_angle <= 110 and self.left_knee_angle <= 110:
                depth_achieved = True
                cv2.putText(self.annotated, "DEPTH: Good squat depth achieved.", (10, 60), self.font, 1.25, self.green, 2, self.line)
            elif depth_achieved == False:
                cv2.putText(self.annotated, "DEPTH: Try to squat lower to achieve better depth.", (10, 60), self.font, 1.25, self.red, 2, self.line)
        else:
            depth_achieved = False

        return depth_achieved

    def _check_knee_tracking(self): 

        # Values for knee tracking over toes calculation by projecting the knee position onto the foot direction vector
        right_foot_length = np.linalg.norm(self.right_toe[:3] - self.right_heel[:3])
        left_foot_length = np.linalg.norm(self.left_toe[:3] - self.left_heel[:3])

        norm_right_foot_direction = (self.right_toe[:3] - self.right_heel[:3]) / right_foot_length
        norm_left_foot_direction = (self.left_toe[:3] - self.left_heel[:3]) / left_foot_length

        right_knee_projection = abs(np.dot(self.right_heel[:3] - self.right_knee[:3], norm_right_foot_direction))
        left_knee_projection = abs(np.dot(self.left_heel[:3] - self.left_knee[:3], norm_left_foot_direction))

        # Threshold: buffer against measurement noise (5% of foot length)
        threshold_right = 0.04 * right_foot_length
        threshold_left = 0.04 * left_foot_length

        right_over_toes = right_knee_projection > (right_foot_length + threshold_right)
        left_over_toes = left_knee_projection > (left_foot_length + threshold_left)

        # Values for knee caving inwards calculation              
        right_dist_knee_heel = np.linalg.norm(self.right_knee[:3] - self.right_heel[:3])
        left_dist_knee_heel = np.linalg.norm(self.left_knee[:3] - self.left_heel[:3])
        dist_knees = np.linalg.norm(self.right_knee[:3] - self.left_knee[:3])


        if right_over_toes or left_over_toes:
            cv2.putText(self.annotated, "KNEE TRACKING: Knees are tracking over toes.", (10, 100), self.font, 1.25, self.red, 2, cv2.LINE_AA)
        # elif dist_knees < right_dist_knee_heel or dist_knees < left_dist_knee_heel:
        #     cv2.putText(self.annotated, "KNEE TRACKING: Knees are caving inwards.", (10, 100), self.font, 1.25, self.red, 2, cv2.LINE_AA)
        else:
            cv2.putText(self.annotated, "KNEE TRACKING: Knees are properly aligned.", (10, 100), self.font, 1.25, self.green, 2, cv2.LINE_AA)
            
    def _check_back_form(self, ):
        torso_inclination_left = findAngle(self.left_hip[0], self.left_hip[1], self.left_shoulder[0], self.left_shoulder[1])
        torso_inclination_right = findAngle(self.right_hip[0], self.right_hip[1], self.right_shoulder[0], self.right_shoulder[1])
        if torso_inclination_left < 55 and torso_inclination_right < 55:
            cv2.putText(self.annotated, "BACK FORM: Good back form.", (10, 140), self.font, 1.25, self.green, 2, cv2.LINE_AA)

        else:
            cv2.putText(self.annotated, "BACK FORM: Try to keep the trunk upright.", (10, 140), self.font, 1.25, self.red, 2, cv2.LINE_AA)
