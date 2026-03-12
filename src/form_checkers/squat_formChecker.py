import cv2
import numpy as np
from ._utilityFunctions import calculate_angle, detect_cam_pos, play_audio_feedback
import pygame
import time 
class SquatFormChecker:
    '''
    This class is responsible for checking the form of a squat exercise using pose landmarks. It evaluates squat depth and knee tracking as well as checking the form of
    the back providing real-time feedback on the form.
    '''

    def __init__(self, tts):
        self.tts = tts

        # Set up for text display
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_size = 1.25
        self.thickness = 2
        self.line = cv2.LINE_AA
        self.green = (0, 255, 0)
        self.red = (0, 0, 255)
        self.depth_achieved = False

        #ROM delay
        self.rom_start_time = None
        self.rom_delay_seconds = 1.8

        #Variables for playing sounds
        self.language = 'en'
        pygame.mixer.init()
        self.last_audio_end_time = 0
        self.last_filepath = None
        self.green_queue = None




    def check_Squat_form(self, annotated, landmarks: np.array, rom_achieved, init_pos):
        if landmarks is None or landmarks.shape[0] != 33:
            print("Insufficient landmarks for squat form check.")
            return rom_achieved, init_pos

        self.annotated = annotated
         
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
            message = "Please adjust the camera for better visibility."
            cv2.putText(self.annotated, message, (10, 60), self.font, self.font_size, self.red, self.thickness, self.line)

            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue = play_audio_feedback(message, 'feedback/camera_feedback.mp3',
                                                                                                self.last_audio_end_time, self.red, self.last_filepath, self.green_queue)
        else:
            rom_achieved, init_pos = self._check_depth(rom_achieved, init_pos)
            if self.init_pos_threshold > self.right_knee_angle and self.init_pos_threshold > self.left_knee_angle:
                self._check_knee_tracking()
                if self.cam_pos == "left" or self.cam_pos == "right":
                    self._check_back_form()

        return rom_achieved, init_pos

    def _check_depth(self, rom_achieved, init_pos):
        # Check if the squat depth is adequate and do not check if depth already achieved or if the person is upright
        depth_achieved_threshold = 110

        if self.init_pos_threshold > self.right_knee_angle and self.init_pos_threshold > self.left_knee_angle:
            # Start of Movement (Important for ROM check and to avoid false triggers)
            if init_pos:
                init_pos = False
                self.rom_start_time = time.time()
                return rom_achieved, init_pos

            # Check if we are still within the ROM delay period to false trigger audio feedback and only provide feedback after the delay has passed
            if self.rom_start_time is not None and (time.time() - self.rom_start_time) < self.rom_delay_seconds:
                return rom_achieved, init_pos
            
            if self.right_knee_angle <= depth_achieved_threshold and self.left_knee_angle <= depth_achieved_threshold:
                self.depth_achieved = True
                color = self.green
                message = "SQUAT DEPTH: Good squat depth achieved."
                audio_text = f"{message}. Good job!"
                file_ending = ".mp3"
            elif self.depth_achieved == False:
                color = self.red
                message = "SQUAT DEPTH: Try to squat lower to achieve better depth."
                audio_text = f"{message}. Please adjust your form"
                file_ending = "_lower.mp3"
            else:
                color = self.green
                message = "SQUAT DEPTH: Good squat depth achieved."
                audio_text = f"{message}. Good job!"
                file_ending = ".mp3"
        
            cv2.putText(self.annotated, message, (10, 60), self.font, self.font_size, color, self.thickness, self.line)
            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue = play_audio_feedback(audio_text, f'feedback/squat_depth{file_ending}',
                                                                                                    self.last_audio_end_time, color, self.last_filepath, self.green_queue)
            return rom_achieved, init_pos

        else:
            self.depth_achieved = False
            init_pos = True
            rom_achieved = False
            self.rom_start_time = None
            return rom_achieved, init_pos


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
        if right_over_toes or left_over_toes:
            message = "KNEE TRACKING: Knees are going over your toes."
            color = self.red
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_overToes.mp3"

        elif self.cam_pos == "front" and (dist_knees < right_dist_knee_heel or dist_knees < left_dist_knee_heel):
            message = "KNEE TRACKING: Knees are caving inwards."
            color = self.red
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_inwards.mp3"
        else:
            color = self.green
            message = "KNEE TRACKING: Knees are properly aligned"
            audio_text = f"{message}. Good job!"
            file_ending = ".mp3"
        cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)
        if self.tts:
            self.last_audio_end_time, self.last_filepath, self.green_queue = play_audio_feedback(audio_text, f'feedback/squat_kneeTracking{file_ending}',
                                                                                                self.last_audio_end_time, color, self.last_filepath, self.green_queue)

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
            audio_text = f"{message}. Good job!"
            file_ending = ".mp3"
        else:
            color = self.red
            message = "BACK FORM: Try to keep the trunk upright."
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_bad.mp3"
        cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)

        if self.tts:
            self.last_audio_end_time, self.last_filepath, self.green_queue = play_audio_feedback(audio_text, f'feedback/squat_backForm{file_ending}',
                                                                                            self.last_audio_end_time, color, self.last_filepath, self.green_queue)
