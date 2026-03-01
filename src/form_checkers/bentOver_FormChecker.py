import numpy as np
from ._utilityFunctions import calculate_angle, detect_cam_pos
import cv2

class BentOverRowFormChecker:
    '''
    This class is responsible for checking the form of a bent-over row exercise using pose landmarks. It evaluates the form of the back and the range of motion of the arms,
    providing real-time feedback on the form.
    '''

    def check_bentover_form(self, annotated, landmarks: np.array, correct_back_form, rom_achieved, init_pos, landmarks_2d):
        if landmarks is None or landmarks.shape[0] != 33:
            print("Insufficient landmarks for bent-over row form check.")
            return annotated, correct_back_form, rom_achieved, init_pos
    
        self.annotated = annotated
        
        # Set up for text display
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_size = 1.25
        self.thickness = 2
        self.line = cv2.LINE_AA
        self.green = (0, 255, 0)
        self.red = (0, 0, 255)

        #Relevant landmarks for row check form
        self.left_shoulder = landmarks[11]
        self.left_elbow = landmarks[13]
        self.left_wrist = landmarks[15]
        self.left_hip = landmarks[23]
        self.left_knee = landmarks[25]

        self.right_shoulder = landmarks[12]
        self.right_elbow = landmarks[14]
        self.right_wrist = landmarks[16]
        self.right_hip = landmarks[24]
        self.right_knee = landmarks[26]    

        self.left_shoulder_2d = landmarks_2d[11]
        self.right_shoulder_2d = landmarks_2d[12]


        # Check if required landmarks have sufficient visibility
        required_landmarks = [self.right_shoulder, self.right_elbow, self.right_wrist, self.right_hip, self.right_knee, 
                              self.left_shoulder, self.left_elbow, self.left_wrist, self.left_hip, self.left_knee]
        
        self.cam_pos = detect_cam_pos(required_landmarks)

        if any(landmark[4] < 0.95 for landmark in required_landmarks):
            cv2.putText(self.annotated, "Please adjust the camera for better visibility.", (10, 60), self.font, self.font_size, self.red, self.thickness, self.line)
        else:
            correct_back_form = self._check_back_form(correct_back_form)

            if correct_back_form and (self.cam_pos == "left" or self.cam_pos == "right"):
                rom_achieved, init_pos = self._check_range_of_motion(rom_achieved, init_pos)
            elif correct_back_form and self.cam_pos == "front":
                self._check_grip_width()

        return  correct_back_form, rom_achieved, init_pos

    

    def _check_back_form(self, correct_back_form):

        feedback_position = (10, 100)

        hip_below_left = [self.left_hip[0], self.left_hip[1] - 1, self.left_hip[2]]
        hip_below_right = [self.right_hip[0], self.right_hip[1] - 1, self.right_hip[2]]

        torso_inclination_left = calculate_angle(self.left_shoulder[:3], self.left_hip[:3], hip_below_left)
        torso_inclination_right = calculate_angle(self.right_shoulder[:3], self.right_hip[:3], hip_below_right)

        torso_lean_left = calculate_angle(self.left_shoulder[:3], self.left_hip[:3], self.left_knee[:3])
        torso_lean_right = calculate_angle(self.right_shoulder[:3], self.right_hip[:3], self.right_knee[:3])

        torso_lean_threshold = 110 
        torso_inclination_threshold = 80

        # Check if the torso is too horizontal or too upright and provide feedback accordingly with additional thresholds for bent-over rows
        if torso_lean_left > torso_lean_threshold or torso_lean_right > torso_lean_threshold:
            color = self.red
            message = "BACK FORM: Try to keep the trunk more horizontal."
            correct_back_form = False
        elif torso_inclination_left > torso_inclination_threshold or torso_inclination_right > torso_inclination_threshold:
            color = self.red
            message = "BACK FORM: Try to keep the trunk in a neutral position."
        else:
            color = self.green
            message = "BACK FORM: Good back form."
            correct_back_form = True
        
        cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)

        return correct_back_form
            

    def _check_range_of_motion(self, rom_achieved, init_pos):

        feedback_position = (10, 140)

        left_elbow_angle = calculate_angle(self.left_shoulder[:3], self.left_elbow[:3], self.left_wrist[:3])
        right_elbow_angle = calculate_angle(self.right_shoulder[:3], self.right_elbow[:3], self.right_wrist[:3])

        elbow_flexion_threshold = 140
        range_of_motion_threshold = 100

        if left_elbow_angle < elbow_flexion_threshold and right_elbow_angle < elbow_flexion_threshold:
            init_pos = False
            if self.cam_pos == "left" and left_elbow_angle < range_of_motion_threshold and init_pos == False:
                color = self.green
                message = "RANGE OF MOTION: Good range of motion."
                rom_achieved = True
            elif self.cam_pos == "right" and right_elbow_angle < range_of_motion_threshold and init_pos == False:
                color = self.green
                message = "RANGE OF MOTION: Good range of motion."
                rom_achieved = True
            elif rom_achieved != True and init_pos == False:
                color = self.red
                message = "RANGE OF MOTION: Try to pull the weights higher for a better muscle activation."
            else:
                color = self.red
                message = "RANGE OF MOTION: Try to lower the weights until your arms are fully extended."
            
            cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)
        
        else:
            init_pos = True
            rom_achieved = False

        return rom_achieved, init_pos

    def _check_grip_width(self):

        feedback_position = (10, 140)

        left_dist_elbow_wrist = np.linalg.norm(self.left_elbow[:3] - self.left_wrist[:3])
        right_dist_elbow_wrist = np.linalg.norm(self.right_elbow[:3] - self.right_wrist[:3])
        dist_wrists = np.linalg.norm(self.left_wrist[:3] - self.right_wrist[:3])

        width_threshold = 2.4
        narrow_threshold = 1.5

        if dist_wrists > width_threshold * left_dist_elbow_wrist or dist_wrists > width_threshold * right_dist_elbow_wrist:
            color = self.red
            message = "GRIP WIDTH: Try to hold the barbell narrower"
        elif dist_wrists < narrow_threshold * left_dist_elbow_wrist and dist_wrists < narrow_threshold * right_dist_elbow_wrist:
            color = self.red
            message = "GRIP WIDTH: Try to hold the barbell wider"
        else:
            color = self.green
            message = "GRIP WIDTH: Good grip width."
        cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)
        
    