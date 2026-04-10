import cv2
import numpy as np
from ._utilityFunctions import calculate_angle, detect_cam_pos, play_audio_feedback, save_snapshot
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

        # ROM delay
        self.rom_start_time = None
        self.rom_delay_seconds = 0.5

        # Variables for playing sounds
        self.language = 'en'
        self.last_audio_end_time = 0
        self.last_filepath = None
        self.green_queue = None
        self.detected = False

        # Run a one-time startup delay after the first successful detection.
        self.initial_detection_timer_seconds = 10.0
        self.initial_detection_timer_started_at = None
        self.initial_detection_timer_done = False

        self.rep_counter = 0

        # Variables for AI feedback
        self.raw_feedbacks = []

        # Snapshot state tracking
        self._last_knee_state = None
        self._last_back_state = None
        self._last_depth_state = None

    def check_Squat_form(self, annotated, landmarks: np.array, rom_achieved, init_pos):
        if landmarks is None or landmarks.shape[0] != 17:
            print("Insufficient landmarks for squat form check.")
            return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

        self.annotated = annotated
         
        #Relevant landmarks for squat form check
        self.right_shoulder = landmarks[5]
        self.right_hip = landmarks[12]
        self.right_knee = landmarks[14]
        self.right_ankle = landmarks[16]
        self.right_ear = landmarks[4]

        self.left_shoulder = landmarks[6]
        self.left_hip = landmarks[11]
        self.left_knee = landmarks[13]
        self.left_ankle = landmarks[15]
        self.left_ear = landmarks[3]


        self.right_knee_angle = calculate_angle(self.right_hip[:2], self.right_knee[:2], self.right_ankle[:2])
        self.left_knee_angle = calculate_angle(self.left_hip[:2], self.left_knee[:2], self.left_ankle[:2])
        self.init_pos_threshold = 140


        required_landmarks = [self.right_shoulder, self.right_hip, self.right_knee, self.right_ankle,
                              self.left_shoulder, self.left_hip, self.left_knee, self.left_ankle]
             
        self.cam_pos = detect_cam_pos([self.left_ear[2], self.right_ear[2]])

        if self.cam_pos == "left":
            relevant = required_landmarks[4:8]
        elif self.cam_pos == "right":
            relevant = required_landmarks[0:4]
        else:
            relevant = required_landmarks

        sufficient_visibility = all(lm[2] >= 0.60 for lm in relevant)

           
        if sufficient_visibility and not self.detected:
            message = "You have been detected!"
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

        if sufficient_visibility and self.detected:
                if not self.initial_detection_timer_done:
                    if self.initial_detection_timer_started_at is None:
                        self.initial_detection_timer_started_at = time.monotonic()
                        return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

                    elapsed = time.monotonic() - self.initial_detection_timer_started_at
                    if elapsed < self.initial_detection_timer_seconds:
                        return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

                    self.initial_detection_timer_done = True
                    self.initial_detection_timer_started_at = None
                rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks = self._check_depth(rom_achieved, init_pos)
                if self.cam_pos == "front":
                    self._check_knee_tracking()
                if self.init_pos_threshold > self.right_knee_angle and self.init_pos_threshold > self.left_knee_angle:
                    if self.cam_pos == "left" or self.cam_pos == "right":
                        self._check_back_form()
        else:
            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                    text="Please adjust the camera until your whole body is visible.",
                                                                                                    filepath='feedback/camera_feedback.mp3',
                                                                                                    last_audio_end_time=self.last_audio_end_time,
                                                                                                    color=self.red,
                                                                                                    last_filepath=self.last_filepath,
                                                                                                    green_queue=self.green_queue,
                                                                                                    detected=self.detected,
                                                                                                    play_local_audio=self.play_local_audio,
                                                                                                    queue_audio_event=self.queue_audio_event
                                                                                                )
        return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

    def _check_depth(self, rom_achieved, init_pos):
        # Check if the squat depth is adequate and do not check if depth already achieved or if the person is upright

        if self.cam_pos == "front":
            depth_achieved_threshold = 135
        else:
             depth_achieved_threshold = 120

        if self.init_pos_threshold > self.right_knee_angle and self.init_pos_threshold > self.left_knee_angle:
            # Start of Movement (Important for ROM check and to avoid false triggers)

            if init_pos:
                init_pos = False
                self.rom_start_time = time.monotonic()
                return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

            # Check if we are still within the ROM delay period to false trigger audio feedback and only provide feedback after the delay has passed
            if self.rom_start_time is not None and (time.monotonic() - self.rom_start_time) < self.rom_delay_seconds:
                return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks
            
            print("Knee Angle", self.right_knee_angle, self.left_knee_angle)
            if self.right_knee_angle <= depth_achieved_threshold and self.left_knee_angle <= depth_achieved_threshold:
                self.depth_achieved = True
                color = self.green
                message = "SQUAT DEPTH: Good squat depth achieved."
                audio_text = f"{message}. Good job!"
                file_ending = ".mp3"
                if self._last_depth_state != "good":
                    save_snapshot(self.annotated, "squat_depthGood_snapshot.jpg")
                self._last_depth_state = "good"
            elif self.depth_achieved == False:
                color = self.red
                message = "SQUAT DEPTH: Try to squat lower to achieve better depth."
                audio_text = f"{message}. Please adjust your form"
                file_ending = "_lower.mp3"
                if self._last_depth_state != "bad":
                    save_snapshot(self.annotated, "squat_depth_snapshot.jpg")
                self._last_depth_state = "bad"
            else:
                color = self.green
                message = "SQUAT DEPTH: Good squat depth achieved."
                audio_text = f"{message}. Good job!"
                file_ending = ".mp3"
                if self._last_depth_state != "good":
                    save_snapshot(self.annotated, "squat_depthGood_snapshot.jpg")
                self._last_depth_state = "good"
        
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
            return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

        else:
            if self.depth_achieved == True:
                self.rep_counter += 1
            self.depth_achieved = False
            init_pos = True
            rom_achieved = False
            self.rom_start_time = None
            return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks


    def _check_knee_tracking(self):
        
        dist_knees_x = abs(self.right_knee[0] - self.left_knee[0])
        dist_ankles_x = abs(self.right_ankle[0] - self.left_ankle[0])

        # Knees should be roughly in line with ankles, so we can compare the distance between knees to the distance between ankles to determine if knees are caving inwards

        ratio = dist_knees_x / dist_ankles_x if dist_ankles_x > 0 else 1.0

        knee_caving_threshold = 0.80 
        
        # Independent checks for both issues
        if ratio < knee_caving_threshold:
            message = "KNEE TRACKING: Knees are caving inwards."
            if self._last_knee_state != "caving":
                save_snapshot(self.annotated, "squat_kneeIn_snapshot.jpg")
            self._last_knee_state = "caving"
            self.raw_feedbacks.append(message)
            color = self.red
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_inwards.mp3"
        else:
            color = self.green
            message = "KNEE TRACKING: Knees are properly aligned"
            if self._last_knee_state != "good":
                save_snapshot(self.annotated, "squat_kneeGood_snapshot.jpg")
            self._last_knee_state = "good"
            audio_text = f"{message}. Good job!"
            file_ending = ".mp3"
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

        hip_below_left = [self.left_hip[0], self.left_hip[1] - 1]
        hip_below_right = [self.right_hip[0], self.right_hip[1] - 1]
        torso_inclination_left = calculate_angle(self.left_shoulder[:2], self.left_hip[:2], hip_below_left)
        torso_inclination_right = calculate_angle(self.right_shoulder[:2], self.right_hip[:2], hip_below_right)

        torso_inclination_threshold = 55

        if torso_inclination_left < torso_inclination_threshold and torso_inclination_right < torso_inclination_threshold:
            color = self.green
            message = "BACK FORM: Good back form." 
            if self._last_back_state != "good":
                save_snapshot(self.annotated, "squat_backGood_snapshot.jpg") 
            self._last_back_state = "good"
            audio_text = f"{message}. Good job!"
            file_ending = ".mp3"
        else:
            color = self.red
            message = "BACK FORM: Try to keep the trunk upright."
            if self._last_back_state != "bad":
                save_snapshot(self.annotated, "squat_trunkUp_snapshot.jpg")
            self._last_back_state = "bad"
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_bad.mp3"

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