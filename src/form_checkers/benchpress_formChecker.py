import numpy as np
from ._utilityFunctions import calculate_angle, detect_cam_pos
import cv2

class BenchpressFormChecker:
    '''
    This class checks the form for benchpress exercises.
    '''

    def check_benchpress_form(self, annotated, landmarks: np.array, rom_achieved, init_pos, landmarks_2d):
        if landmarks is None or landmarks.shape[0] != 33:
            print("Insufficient landmarks for benchpress form check.")
            return annotated, rom_achieved, init_pos

        self.annotated = annotated

        # Set up for text display
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_size = 1.25
        self.thickness = 2
        self.line = cv2.LINE_AA
        self.green = (0, 255, 0)
        self.red = (0, 0, 255)

        #Relevant landmarks for benchpress form check
        self.left_shoulder = landmarks[11]
        self.left_elbow = landmarks[13]
        self.left_wrist = landmarks[15]
        self.left_finger = landmarks[19]
        self.left_hip = landmarks[23]

        self.right_shoulder = landmarks[12]
        self.right_elbow = landmarks[14]
        self.right_wrist = landmarks[16]
        self.right_finger = landmarks[20]
        self.right_hip = landmarks[24]


        self.left_elbow_2d = landmarks_2d[13]
        self.right_elbow_2d = landmarks_2d[14]

        required_landmarks = [self.right_shoulder, self.right_elbow, self.right_wrist,
                              self.left_shoulder, self.left_elbow, self.left_wrist]
        
        self.cam_pos = detect_cam_pos(required_landmarks)

        if any(landmark[4] < 0.95 for landmark in required_landmarks):
            cv2.putText(self.annotated, "Please adjust the camera for better visibility.", (10, 60), self.font, self.font_size, self.red, self.thickness, self.line)
        else:

            if self.cam_pos == "front":
                self._check_grip_width() 
            rom_achieved, init_pos = self._check_range_of_motion(rom_achieved, init_pos)
        
        return rom_achieved, init_pos

    def _check_range_of_motion(self, rom_achieved, init_pos):

        feedback_position = (10, 140)

        h, w = self.annotated.shape[:2]


        left_elbow_angle = calculate_angle(self.left_shoulder[:3], self.left_elbow[:3], self.left_wrist[:3])
        right_elbow_angle = calculate_angle(self.right_shoulder[:3], self.right_elbow[:3], self.right_wrist[:3])

        cv2.putText(self.annotated, f"{int(left_elbow_angle)}", (int(self.left_elbow_2d[0] * w), int(self.left_elbow_2d[1] * h)), self.font, self.font_size, self.red, self.thickness, self.line)
        cv2.putText(self.annotated, f"{int(right_elbow_angle)}", (int(self.right_elbow_2d[0] * w), int(self.right_elbow_2d[1] * h)), self.font, self.font_size, self.red, self.thickness, self.line)

        elbow_flexion_threshold = 145
        range_of_motion_threshold = 75

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
                message = "RANGE OF MOTION: Try to lower the weights to your lower chest for a better muscle activation."
            else:
                color = self.red
                message = "RANGE OF MOTION: Try to push up the weights until your arms are fully extended."
            
            cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)
        
        else:
            init_pos = True
            rom_achieved = False

        return rom_achieved, init_pos
    

    def _check_back_form(self):
        return
    
    def _check_grip_width(self):
        feedback_position = (10, 100)

        dist_shoulders = np.linalg.norm(self.right_shoulder[:3] - self.left_shoulder[:3])
        grip_width = np.linalg.norm(self.right_wrist[:3] - self.left_wrist[:3]) 

        grip_width_threshold_min = 1.75 * dist_shoulders
        grip_width_threshold_max = 2.25 * dist_shoulders

        if grip_width < grip_width_threshold_min:
            color = self.red
            message = "GRIP WIDTH: Try to widen your grip"
        elif grip_width > grip_width_threshold_max:
            color = self.red
            message = "GRIP WIDTH: Try to narrow your grip"
        else:
            color = self.green
            message = "GRIP WIDTH: Good grip width"
        cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)
