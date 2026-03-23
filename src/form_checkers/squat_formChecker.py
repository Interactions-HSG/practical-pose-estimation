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

    def __init__(self, tts, play_local_audio, queue_audio_event=None):
        
        # Initialize with Text-to-Speech (TTS) option and audio event queue callback for server mode
        self.tts = tts
        self.play_local_audio = play_local_audio
        self.queue_audio_event = queue_audio_event

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
        self.detected = False

        # Run a one-time startup delay after the first successful detection.
        self.initial_detection_timer_seconds = 10.0
        self.initial_detection_timer_started_at = None
        self.initial_detection_timer_done = False

        self.rep_counter = 0

    def check_Squat_form(self, annotated, landmarks: np.array, rom_achieved, init_pos):
        if landmarks is None or landmarks.shape[0] != 33:
            print("Insufficient landmarks for squat form check.")
            return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter

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
        self.init_pos_threshold = 140


        required_landmarks = [self.right_shoulder, self.right_hip, self.right_knee, self.right_ankle, self.right_toe, self.right_heel,
                              self.left_shoulder, self.left_hip, self.left_knee, self.left_ankle, self.left_toe, self.left_heel]
             
        self.cam_pos = detect_cam_pos(required_landmarks)
        

        print(f"Camera Position Detected: {self.cam_pos}")
        if any(landmark[4] < 0.95 for landmark in required_landmarks):
            message = "Please adjust the camera until your whole body is visible."
           #cv2.putText(self.annotated, message, (10, 60), self.font, self.font_size, self.red, self.thickness, self.line)

            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                    text=message,
                                                                                                    filepath='feedback/camera_feedback.mp3',
                                                                                                    last_audio_end_time=self.last_audio_end_time,
                                                                                                    color=self.red,
                                                                                                    last_filepath=self.last_filepath,
                                                                                                    green_queue=self.green_queue,
                                                                                                    detected=self.detected,
                                                                                                    play_local_audio=self.play_local_audio,
                                                                                                    queue_audio_event=self.queue_audio_event
                                                                                                )
        else:
            message = "You have been detected!"
            #cv2.putText(self.annotated, message, (10, 60), self.font, self.font_size, self.green, self.thickness, self.line)
            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                    text=message,
                                                                                                    filepath='feedback/camera_feedback.mp3',
                                                                                                    last_audio_end_time=self.last_audio_end_time,
                                                                                                    color=self.green,
                                                                                                    last_filepath=self.last_filepath,
                                                                                                    green_queue=self.green_queue,
                                                                                                    detected=self.detected,
                                                                                                    play_local_audio=self.play_local_audio,
                                                                                                    queue_audio_event=self.queue_audio_event
                                                                                                )

            if self.detected:
                if not self.initial_detection_timer_done:
                    if self.initial_detection_timer_started_at is None:
                        self.initial_detection_timer_started_at = time.monotonic()
                        return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter

                    elapsed = time.monotonic() - self.initial_detection_timer_started_at
                    if elapsed < self.initial_detection_timer_seconds:
                        return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter

                    self.initial_detection_timer_done = True
                    self.initial_detection_timer_started_at = None
                rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter = self._check_depth(rom_achieved, init_pos)
                if self.init_pos_threshold > self.right_knee_angle and self.init_pos_threshold > self.left_knee_angle:
                    self._check_knee_tracking()
                    if self.cam_pos == "left" or self.cam_pos == "right":
                        self._check_back_form()

        return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter

    def _check_depth(self, rom_achieved, init_pos):
        # Check if the squat depth is adequate and do not check if depth already achieved or if the person is upright
        depth_achieved_threshold = 110

        if self.init_pos_threshold > self.right_knee_angle and self.init_pos_threshold > self.left_knee_angle:
            # Start of Movement (Important for ROM check and to avoid false triggers)
            if init_pos:
                init_pos = False
                self.rom_start_time = time.time()
                return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter

            # Check if we are still within the ROM delay period to false trigger audio feedback and only provide feedback after the delay has passed
            if self.rom_start_time is not None and (time.time() - self.rom_start_time) < self.rom_delay_seconds:
                return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter

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
        
            #cv2.putText(self.annotated, message, (10, 60), self.font, self.font_size, color, self.thickness, self.line)
            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                    text=audio_text,
                                                                                                    filepath=f'feedback/squat_depth{file_ending}',
                                                                                                    last_audio_end_time=self.last_audio_end_time,
                                                                                                    color=color,
                                                                                                    last_filepath=self.last_filepath,
                                                                                                    green_queue=self.green_queue,
                                                                                                    detected=self.detected,
                                                                                                    play_local_audio=self.play_local_audio,
                                                                                                    queue_audio_event=self.queue_audio_event
                                                                                                )
            return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter

        else:
            if self.depth_achieved == True:
                self.rep_counter += 1
            self.depth_achieved = False
            init_pos = True
            rom_achieved = False
            self.rom_start_time = None
            return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter


    def _check_knee_tracking(self): 

        feedback_position = (10, 100)

        # Values for knee tracking over toes calculation by projecting the knee position onto the foot direction vector
        right_foot_length = np.linalg.norm(self.right_toe[:2] - self.right_heel[:2])
        left_foot_length = np.linalg.norm(self.left_toe[:2] - self.left_heel[:2])

        norm_right_foot_direction = (self.right_toe[:2] - self.right_heel[:2]) / right_foot_length
        norm_left_foot_direction = (self.left_toe[:2] - self.left_heel[:2]) / left_foot_length

        right_knee_projection = abs(np.dot(self.right_heel[:2] - self.right_knee[:2], norm_right_foot_direction))
        left_knee_projection = abs(np.dot(self.left_heel[:2] - self.left_knee[:2], norm_left_foot_direction))

        threshold = 0.11  # Allow a small threshold for noise and natural movement

        right_foot_length = right_foot_length + threshold
        left_foot_length = left_foot_length + threshold

        print(f"Right Knee Projection: {right_knee_projection:.3f}, Left Knee Projection: {left_knee_projection:.3f}, Right Foot Length: {right_foot_length:.3f}, Left Foot Length: {left_foot_length:.3f}")

        right_over_toes = right_knee_projection > right_foot_length
        left_over_toes = left_knee_projection > left_foot_length

        # Values for knee caving inwards calculation    
        threshold_knee_caving = 0.05     
        right_dist_knee_heel = np.linalg.norm(self.right_knee[:2] - self.right_heel[:2]) 
        left_dist_knee_heel = np.linalg.norm(self.left_knee[:2] - self.left_heel[:2]) 
        dist_knees = np.linalg.norm(self.right_knee[:2] - self.left_knee[:2]) + threshold_knee_caving


        # Independent checks for both issues
        print("self.cam_pos:", self.cam_pos)
        if (self.cam_pos == "right" and right_over_toes) or (self.cam_pos == "left" and left_over_toes):
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
        #cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)
        if self.tts:
            self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                text=audio_text,
                                                                                                filepath=f'feedback/squat_kneeTracking{file_ending}',
                                                                                                last_audio_end_time=self.last_audio_end_time,
                                                                                                color=color,
                                                                                                last_filepath=self.last_filepath,
                                                                                                green_queue=self.green_queue,
                                                                                                detected=self.detected,
                                                                                                play_local_audio=self.play_local_audio,
                                                                                                queue_audio_event=self.queue_audio_event
                                                                                            )

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
        #cv2.putText(self.annotated, message, feedback_position, self.font, self.font_size, color, self.thickness, self.line)

        if self.tts:
            self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                text=audio_text,
                                                                                                filepath=f'feedback/squat_backForm{file_ending}',
                                                                                                last_audio_end_time=self.last_audio_end_time,
                                                                                                color=color,
                                                                                                last_filepath=self.last_filepath,
                                                                                                green_queue=self.green_queue,
                                                                                                detected=self.detected,
                                                                                                play_local_audio=self.play_local_audio,
                                                                                                queue_audio_event=self.queue_audio_event
                                                                                            )
