import numpy as np
import cv2

class BenchpressFormChecker:
    '''
    This class checks the form for benchpress exercises.
    '''

    def check_benchpress_form(self, annotated, landmarks: np.array):
        if landmarks is None or landmarks.shape[0] != 33:
            print("Insufficient landmarks for benchpress form check.")
            return annotated

        self.annotated = annotated

        # Set up for text display
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.line = cv2.LINE_AA
        self.green = (0, 255, 0)
        self.red = (0, 0, 255)

        #Relevant landmarks for benchpress form check
        self.left_shoulder = landmarks[11]
        self.left_elbow = landmarks[13]
        self.left_wrist = landmarks[15]
        self.left_hip = landmarks[23]

        self.right_shoulder = landmarks[12]
        self.right_elbow = landmarks[14]
        self.right_wrist = landmarks[16]
        self.right_hip = landmarks[24]

    

    def _check_range_of_motion(self):
        return
    
    def _check_arm_position(self):
        return
