import numpy as np
from ._utilityFunctions import calculate_angle, detect_cam_pos, play_audio_feedback
import cv2
import pygame
import time

class BentOverRowFormChecker:
    '''
    This class is responsible for checking the form of a bent-over row exercise using pose landmarks. It evaluates the form of the back and the range of motion of the arms,
    providing real-time feedback on the form.
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
        self.grey = (90, 90, 90)

        self.correct_back_form = False
         
        #ROM delay
        self.rom_start_time = None
        self.rom_delay_seconds = 0.6
  
        # Variables for playing sounds
        self.language = 'en'
        pygame.mixer.init()
        self.last_audio_end_time = 0
        self.last_filepath = None
        self.green_queue = None
        self.detected = False

        # Run a one-time startup delay after the first successful detection.
        self.initial_detection_timer_seconds = 8.0
        self.initial_detection_timer_started_at = None
        self.initial_detection_timer_done = False

    def check_bentover_form(self, annotated, landmarks: np.array, rom_achieved, init_pos):
        if landmarks is None or landmarks.shape[0] != 33:
            print("Insufficient landmarks for bent-over row form check.")
            return annotated, rom_achieved, init_pos
    
        self.annotated = annotated

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

        # Check if required landmarks have sufficient visibility
        required_landmarks = [self.right_shoulder, self.right_elbow, self.right_wrist, self.right_hip, self.right_knee, 
                              self.left_shoulder, self.left_elbow, self.left_wrist, self.left_hip, self.left_knee]
        
        self.cam_pos = detect_cam_pos(required_landmarks)

        if any(landmark[4] < 0.95 for landmark in required_landmarks):
            message = "Please adjust the camera until your whole body is visible."
            #cv2.putText(self.annotated, message, (10, 60), self.font, self.font_size, self.red, self.thickness, self.line)

            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(message, 'feedback/camera_feedback.mp3',
                                                                                                    self.last_audio_end_time, self.red, self.last_filepath, self.green_queue, self.detected)
        else:
            message = "You have been detected!"
            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(message, 'feedback/camera_feedback.mp3',
                                                                                                    self.last_audio_end_time, self.green, self.last_filepath, self.green_queue, self.detected)

            if self.detected:
                if not self.initial_detection_timer_done:
                    if self.initial_detection_timer_started_at is None:
                        self.initial_detection_timer_started_at = time.monotonic()
                        return rom_achieved, init_pos

                    elapsed = time.monotonic() - self.initial_detection_timer_started_at
                    if elapsed < self.initial_detection_timer_seconds:
                        return rom_achieved, init_pos

                    self.initial_detection_timer_done = True
                    self.initial_detection_timer_started_at = None

                self._check_back_form()

                if self.correct_back_form and (self.cam_pos == "left" or self.cam_pos == "right"):
                    rom_achieved, init_pos = self._check_range_of_motion(rom_achieved, init_pos)
                elif self.correct_back_form and self.cam_pos == "front":
                    self._check_grip_width()

        return rom_achieved, init_pos

    def _check_back_form(self):

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
            self.correct_back_form = False
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_horizontal.mp3"
        elif torso_inclination_left > torso_inclination_threshold or torso_inclination_right > torso_inclination_threshold:
            color = self.red
            message = "BACK FORM: Try to keep the trunk in a neutral position."
            self.correct_back_form = False
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_neutral.mp3"
        else:
            color = self.green
            message = "BACK FORM: Good back form."
            self.correct_back_form = True
            audio_text = f"{message}. Good job!"
            file_ending = ".mp3"
            
        
        #cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)
        if self.tts:
            self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(audio_text, f'feedback/back_feedback{file_ending}', 
                                                                            self.last_audio_end_time, color, self.last_filepath, self.green_queue, self.detected)

            

    def _check_range_of_motion(self, rom_achieved, init_pos):
        feedback_position = (10, 140)

        left_elbow_angle = calculate_angle(self.left_shoulder[:3], self.left_elbow[:3], self.left_wrist[:3])
        right_elbow_angle = calculate_angle(self.right_shoulder[:3], self.right_elbow[:3], self.right_wrist[:3])

        elbow_flexion_threshold = 140
        range_of_motion_threshold = 100

        if self.cam_pos == "left":
            in_pull_phase = left_elbow_angle < elbow_flexion_threshold
        elif self.cam_pos == "right":
            in_pull_phase = right_elbow_angle < elbow_flexion_threshold
        else:
            in_pull_phase = (left_elbow_angle < elbow_flexion_threshold and right_elbow_angle < elbow_flexion_threshold)

        if in_pull_phase:

            # Start of Movement (Important for ROM check and to avoid false triggers)
            if init_pos:
                init_pos = False
                self.rom_start_time = time.time()
                return rom_achieved, init_pos

            # Check if we are still within the ROM delay period to false trigger audio feedback and only provide feedback after the delay has passed
            if self.rom_start_time is not None and (time.time() - self.rom_start_time) < self.rom_delay_seconds:
                return rom_achieved, init_pos
    
            if self.cam_pos == "left" and left_elbow_angle < range_of_motion_threshold and init_pos == False:
                color = self.green
                message = "RANGE OF MOTION: Good range of motion."
                audio_text = f"{message}. Good job!"
                rom_achieved = True
                file_ending = ".mp3"
            elif self.cam_pos == "right" and right_elbow_angle < range_of_motion_threshold and init_pos == False:
                color = self.green
                message = "RANGE OF MOTION: Good range of motion."
                audio_text = f"{message}. Good job!"
                rom_achieved = True
                file_ending = ".mp3"
            elif rom_achieved != True and init_pos == False:
                color = self.red
                message = "RANGE OF MOTION: Try to pull the weights higher for a better muscle activation."
                audio_text = f"{message}. Please adjust your form"
                file_ending = "_higher.mp3"
            else:
                color = self.grey
                message = "RANGE OF MOTION: Good, now lower the weights to the starting position."
                audio_text = f"{message}"
                file_ending = "_lower.mp3"

            #cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)
            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(audio_text, f'feedback/bent_rom{file_ending}', 
                                                                                                    self.last_audio_end_time, color, self.last_filepath, self.green_queue, self.detected)
        
        else:
            init_pos = True
            rom_achieved = False
            self.rom_start_time = None  # Reset ROM timer when arms are extended

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
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_narrower.mp3"
        elif dist_wrists < narrow_threshold * left_dist_elbow_wrist and dist_wrists < narrow_threshold * right_dist_elbow_wrist:
            color = self.red
            message = "GRIP WIDTH: Try to hold the barbell wider"
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_wider.mp3"
        else:
            color = self.green
            message = "GRIP WIDTH: Good grip width."
            audio_text = f"{message}. Good job!"
            file_ending = ".mp3"


        #cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)
        if self.tts:
            self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(audio_text, f'feedback/bent_grip{file_ending}',
                                                                                self.last_audio_end_time, color, self.last_filepath, self.green_queue, self.detected)
    

        
    