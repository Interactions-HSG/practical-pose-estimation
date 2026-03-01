import cv2
import numpy as np
from ._utilityFunctions import calculate_angle, detect_cam_pos

class SquatFormChecker:
    '''
    This class is responsible for checking the form of a squat exercise using pose landmarks. It evaluates squat depth and knee tracking as well as checking the form of
    the back providing real-time feedback on the form.
    '''

    def check_Squat_form(self, annotated, landmarks: np.array, depth_achieved):
        if landmarks is None or landmarks.shape[0] != 33:
            print("Insufficient landmarks for squat form check.")
            return annotated, depth_achieved

        self.annotated = annotated
        
        # Set up for text display
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_size = 1.25
        self.thickness = 2
        self.line = cv2.LINE_AA
        self.green = (0, 255, 0)
        self.red = (0, 0, 255)

        #Relevant landmarks for squat form check
        self.left_shoulder = landmarks[11]
        self.left_hip = landmarks[23] 
        self.left_knee = landmarks[25]
        self.left_ankle = landmarks[27] 
        self.left_heel = landmarks[29]
        self.left_toe = landmarks[31]

        self.right_shoulder = landmarks[12]
        self.right_hip = landmarks[24]
        self.right_knee = landmarks[26]
        self.right_ankle = landmarks[28]  
        self.right_heel = landmarks[30]
        self.right_toe = landmarks[32] 


        self.right_knee_angle = calculate_angle(self.right_hip[:3], self.right_knee[:3], self.right_ankle[:3])
        self.left_knee_angle = calculate_angle(self.left_hip[:3], self.left_knee[:3], self.left_ankle[:3])
        self.init_pos_threshold = 155


        required_landmarks = [self.right_shoulder, self.right_hip, self.right_knee, self.right_ankle, self.right_toe, self.right_heel,
                              self.left_shoulder, self.left_hip, self.left_knee, self.left_ankle, self.left_toe, self.left_heel]
             
        self.cam_pos = detect_cam_pos(required_landmarks)
        
        if any(landmark[4] < 0.95 for landmark in required_landmarks):
            cv2.putText(self.annotated, "Please adjust the camera for better visibility.", (10, 60), self.font, self.font_size, self.red, self.thickness, self.line)
        else:
            depth_achieved = self._check_depth(depth_achieved)
            if self.init_pos_threshold > self.right_knee_angle and self.init_pos_threshold > self.left_knee_angle:
                self._check_knee_tracking()
                if self.cam_pos == "left" or self.cam_pos == "right":
                    self._check_back_form()

        return depth_achieved

    def _check_depth(self, depth_achieved):
        # Check if the squat depth is adequate and do not check if depth already achieved or if the person is upright
        depth_achieved_threshold = 110

        if self.init_pos_threshold > self.right_knee_angle and self.init_pos_threshold > self.left_knee_angle:
            if self.right_knee_angle <= depth_achieved_threshold and self.left_knee_angle <= depth_achieved_threshold:
                depth_achieved = True
                color = self.green
                message = "DEPTH: Good squat depth achieved."
            elif depth_achieved == False:
                color = self.red
                message = "DEPTH: Try to squat lower to achieve better depth."
            cv2.putText(self.annotated, message, (10, 60), self.font, self.font_size, color, self.thickness, self.line)
        else:
            depth_achieved = False

        return depth_achieved

    def _check_knee_tracking(self): 

        feedback_position = (10, 100)

        # Values for knee tracking over toes calculation by projecting the knee position onto the foot direction vector
        right_foot_length = np.linalg.norm(self.right_toe[:3] - self.right_heel[:3])
        left_foot_length = np.linalg.norm(self.left_toe[:3] - self.left_heel[:3])

        norm_right_foot_direction = (self.right_toe[:3] - self.right_heel[:3]) / right_foot_length
        norm_left_foot_direction = (self.left_toe[:3] - self.left_heel[:3]) / left_foot_length

        right_knee_projection = abs(np.dot(self.right_heel[:3] - self.right_knee[:3], norm_right_foot_direction))
        left_knee_projection = abs(np.dot(self.left_heel[:3] - self.left_knee[:3], norm_left_foot_direction))

        # Threshold: buffer against measurement noise (3% of foot length)
        threshold = 0.03
        threshold_right = threshold * right_foot_length
        threshold_left = threshold * left_foot_length

        right_over_toes = right_knee_projection > (right_foot_length + threshold_right)
        left_over_toes = left_knee_projection > (left_foot_length + threshold_left)

        # Values for knee caving inwards calculation              
        right_dist_knee_heel = np.linalg.norm(self.right_knee[:3] - self.right_heel[:3])
        left_dist_knee_heel = np.linalg.norm(self.left_knee[:3] - self.left_heel[:3])
        dist_knees = np.linalg.norm(self.right_knee[:3] - self.left_knee[:3])


        # Independent checks for both issues
        warnings = []
        if self.cam_pos == "left" or self.cam_pos == "right":
            if right_over_toes or left_over_toes:
                warnings.append("over toes")
        if self.cam_pos == "front":
            if dist_knees < right_dist_knee_heel or dist_knees < left_dist_knee_heel:
                warnings.append("caving inwards")
        
        if warnings:
            message = "KNEE TRACKING: Knees are " + " and ".join(warnings)
            color = self.red
        else:
            color = self.green
            message = "KNEE TRACKING: Knees are properly aligned"
        cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)
            
    def _check_back_form(self):
        
        feedback_position = (10, 140)

        hip_below_left = [self.left_hip[0], self.left_hip[1] - 1, self.left_hip[2]]
        hip_below_right = [self.right_hip[0], self.right_hip[1] - 1, self.right_hip[2]]
        torso_inclination_left = calculate_angle(self.left_shoulder[:3], self.left_hip[:3], hip_below_left)
        torso_inclination_right = calculate_angle(self.right_shoulder[:3], self.right_hip[:3], hip_below_right)

        torso_inclination_threshold = 55

        if torso_inclination_left < torso_inclination_threshold and torso_inclination_right < torso_inclination_threshold:
            color = self.green
            message = "BACK FORM: Good back form."      
        else:
            color = self.red
            message = "BACK FORM: Try to keep the trunk upright."
        cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)
