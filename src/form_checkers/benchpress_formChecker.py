import numpy as np
from ._utilityFunctions import calculate_angle, detect_cam_pos, play_audio_feedback
import cv2
import pygame
import time

class BenchpressFormChecker:
    '''
    This class checks the form for benchpress exercises.
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

        #ROM delay
        self.rom_start_time = None
        self.rom_delay_seconds = 0.6

        #Variables for playing sounds
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

    def check_benchpress_form(self, annotated, landmarks: np.array, rom_achieved, init_pos):
        if landmarks is None or landmarks.shape[0] != 17:
            cv2.putText(self.annotated, "Insufficient landmarks for benchpress form check.", (10, 60), self.font, self.font_size, self.red, self.thickness, self.line)
            return rom_achieved, init_pos

        self.annotated = annotated

        #Relevant landmarks for benchpress form check
        self.left_shoulder = landmarks[5]
        self.left_elbow = landmarks[7]
        self.left_wrist = landmarks[9]
        self.left_hip = landmarks[11]

        self.right_shoulder = landmarks[6]
        self.right_elbow = landmarks[8]
        self.right_wrist = landmarks[10]
        self.right_hip = landmarks[12]

        required_landmarks = [self.right_elbow, self.right_wrist, self.left_elbow, self.left_wrist]

        cam_pos = detect_cam_pos(required_landmarks, standing=False)

        # YOLO keypoints are [x, y, conf]. Require confident keypoints before feedback.
        if any(landmark[2] < 0.75 for landmark in required_landmarks):
            message = "Please adjust the camera until your whole body is visible."
           # cv2.putText(self.annotated, message, (10, 60), self.font, self.font_size, self.red, self.thickness, self.line)

            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(message, "feedback/camera_feedback.mp3", 
                                                                                                    self.last_audio_end_time, self.red, self.last_filepath, self.green_queue, self.detected)
            return rom_achieved, init_pos

        else:
            message = "You have been detected!"
            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(message, "feedback/camera_feedback.mp3", 
                                                                                                    self.last_audio_end_time, self.green, self.last_filepath, self.green_queue, self.detected)
            # Show both grip width and ROM feedback for benchpress YOLO setup.
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

                if cam_pos == "front":
                    self._check_grip_width()
                    rom_achieved, init_pos = self._check_range_of_motion(rom_achieved, init_pos)
                #elif cam_pos == "left" or cam_pos == "right":
                    # For side view --> AI feedback 
            
        return rom_achieved, init_pos

    def _check_range_of_motion(self, rom_achieved, init_pos):

        feedback_position = (10, 140)

        left_elbow_angle = calculate_angle(self.left_shoulder[:2], self.left_elbow[:2], self.left_wrist[:2])
        right_elbow_angle = calculate_angle(self.right_shoulder[:2], self.right_elbow[:2], self.right_wrist[:2])

        # cv2.putText(self.annotated, f"{int(left_elbow_angle)}", (int(self.left_elbow[0]), int(self.left_elbow[1])), self.font, self.font_size, self.green, self.thickness, self.line)
        # cv2.putText(self.annotated, f"{int(right_elbow_angle)}", (int(self.right_elbow[0]), int(self.right_elbow[1])), self.font, self.font_size, self.green, self.thickness, self.line)

        elbow_flexion_threshold = 145
        range_of_motion_threshold = 50

        if left_elbow_angle < elbow_flexion_threshold and right_elbow_angle < elbow_flexion_threshold:
            # Start of Movement (Important for ROM check and to avoid false triggers)
            if init_pos:
                init_pos = False
                self.rom_start_time = time.time()
                return rom_achieved, init_pos

            # Check if we are still within the ROM delay period to false trigger audio feedback and only provide feedback after the delay has passed
            if self.rom_start_time is not None and (time.time() - self.rom_start_time) < self.rom_delay_seconds:
                return rom_achieved, init_pos
            
            if left_elbow_angle < range_of_motion_threshold or right_elbow_angle < range_of_motion_threshold:
                color = self.green
                message = "RANGE OF MOTION: Good range of motion."
                audio_text = f"{message}. Good job"
                rom_achieved = True
                file_ending = ".mp3"
            elif rom_achieved != True and init_pos == False:
                color = self.red
                message = "RANGE OF MOTION: Try to lower the weights to your lower chest for a better muscle activation."
                audio_text = f"{message}. Please adjust your form"
                file_ending = "_lower.mp3"
            else:
                color = self.red
                message = "RANGE OF MOTION: Try to push up the weights until your arms are fully extended."
                audio_text = f"{message}. Please adjust your form"
                file_ending = "_extended.mp3"
            
           # cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)


            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(audio_text, f"feedback/benchpress_rom{file_ending}", 
                                                                                                self.last_audio_end_time, color, self.last_filepath, self.green_queue, self.detected)
        else:
            init_pos = True
            rom_achieved = False

        return rom_achieved, init_pos
    
    def _check_grip_width(self):
        feedback_position = (10, 100)

        dist_shoulders = np.linalg.norm(self.right_shoulder[:2] - self.left_shoulder[:2])
        grip_width = np.linalg.norm(self.right_wrist[:2] - self.left_wrist[:2]) 

        grip_width_threshold_min = 1.75 * dist_shoulders
        grip_width_threshold_max = 2.25 * dist_shoulders

        if grip_width < grip_width_threshold_min:
            color = self.red
            message = "GRIP WIDTH: Try to widen your grip"
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_wider.mp3"
        elif grip_width > grip_width_threshold_max:
            color = self.red
            message = "GRIP WIDTH: Try to narrow your grip"
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_narrower.mp3"
        else:
            color = self.green
            message = "GRIP WIDTH: Good grip width"
            audio_text = f"{message}. Good job!"
            file_ending = ".mp3"
        #cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)

        if self.tts:
            self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(audio_text, f"feedback/benchpress_grip{file_ending}", 
                                                                                                self.last_audio_end_time, color, self.last_filepath, self.green_queue, self.detected)
