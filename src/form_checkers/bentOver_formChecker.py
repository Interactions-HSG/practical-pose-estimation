import numpy as np
from ._utilityFunctions import calculate_angle, detect_cam_pos, play_audio_feedback, save_snapshot
import cv2
import time

class BentOverRowFormChecker:
    '''
    This class is responsible for checking the form of a bent-over row exercise using pose landmarks. It evaluates the form of the back and the range of motion of the arms,
    providing real-time feedback on the form.
    '''

    def __init__(self, tts, play_local_audio=False, queue_audio_event=None):
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
        self.grey = (90, 90, 90)

        self.correct_back_form = False
         
        #ROM delay
        self.rom_start_time = None
        self.rom_delay_seconds = 0.6
  
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

        # Snapshot state tracking for AI feedback
        self._last_back_state = None
        self._last_rom_state = None
        self._last_grip_state = None


    def check_bentover_form(self, annotated, landmarks: np.array, rom_achieved, init_pos):
        if landmarks is None or landmarks.shape[0] != 17:
            print("Insufficient landmarks for bent-over row form check.")
            return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks
    
        self.annotated = annotated

        #Relevant landmarks for row check form
        self.right_shoulder = landmarks[5]
        self.right_elbow = landmarks[7]
        self.right_wrist = landmarks[9]
        self.right_hip = landmarks[11]
        self.right_knee = landmarks[13]
        self.right_ear = landmarks[3]

        self.left_shoulder = landmarks[6]
        self.left_elbow = landmarks[8]
        self.left_wrist = landmarks[10]
        self.left_hip = landmarks[12]
        self.left_knee = landmarks[14]
        self.left_ear = landmarks[4]

        # Check if required landmarks have sufficient visibility
        required_landmarks = [self.right_shoulder, self.right_elbow, self.right_wrist, self.right_hip, self.right_knee, 
                              self.left_shoulder, self.left_elbow, self.left_wrist, self.left_hip, self.left_knee]
        
        self.cam_pos = detect_cam_pos([self.left_ear[2], self.right_ear[2]])

        if self.cam_pos == "left":
            relevant = required_landmarks[5:10]
        elif self.cam_pos == "right":
            relevant = required_landmarks[0:5]
        else:
            relevant = required_landmarks

        sufficient_visibility = all(lm[2] >= 0.60 for lm in relevant)

        if sufficient_visibility and not self.detected:
            message = "You have been detected!"
            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                    text = message,
                                                                                                    filepath='feedback/camera_feedback.mp3',
                                                                                                    last_audio_end_time=self.last_audio_end_time,
                                                                                                    color=self.green,
                                                                                                    last_filepath=self.last_filepath,
                                                                                                    green_queue=self.green_queue,
                                                                                                    detected=self.detected,
                                                                                                    play_local_audio=self.play_local_audio,
                                                                                                    queue_audio_event=self.queue_audio_event
                                                                                                )

        elif sufficient_visibility and self.detected:
            if not self.initial_detection_timer_done:
                if self.initial_detection_timer_started_at is None:
                    self.initial_detection_timer_started_at = time.monotonic()
                    return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

                elapsed = time.monotonic() - self.initial_detection_timer_started_at
                if elapsed < self.initial_detection_timer_seconds:
                    return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

                self.initial_detection_timer_done = True
                self.initial_detection_timer_started_at = None

            if  (self.cam_pos == "left" or self.cam_pos == "right"):
                self._check_back_form()
                rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks = self._check_range_of_motion(rom_achieved, init_pos)
            elif self.cam_pos == "front":
                self._check_grip_width()
                rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks = self._check_range_of_motion(rom_achieved, init_pos)
        else:
            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                    text = "Please adjust the camera until your whole body is visible.",
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

    def _check_back_form(self):

        hip_below_left = [self.left_hip[0], self.left_hip[1] - 1]
        hip_below_right = [self.right_hip[0], self.right_hip[1] - 1]

        torso_inclination_left = calculate_angle(self.left_shoulder[:2], self.left_hip[:2], hip_below_left)
        torso_inclination_right = calculate_angle(self.right_shoulder[:2], self.right_hip[:2], hip_below_right)

        torso_lean_left = calculate_angle(self.left_shoulder[:2], self.left_hip[:2], self.left_knee[:2])
        torso_lean_right = calculate_angle(self.right_shoulder[:2], self.right_hip[:2], self.right_knee[:2])

        torso_lean_threshold = 120 
        torso_inclination_threshold = 80

        # Check if the torso is too horizontal or too upright and provide feedback accordingly with additional thresholds for bent-over rows
        if torso_lean_left > torso_lean_threshold or torso_lean_right > torso_lean_threshold:
            color = self.red
            message = "BACK FORM: Try to keep the trunk more horizontal."
            self.correct_back_form = False
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_horizontal.mp3"
            if self._last_back_state != "horizontal":
                save_snapshot(self.annotated, "bentOver_backHorizontal_snapshot.jpg")
            self._last_back_state = "horizontal"

        elif torso_inclination_left > torso_inclination_threshold or torso_inclination_right > torso_inclination_threshold:
            color = self.red
            message = "BACK FORM: Try to keep the trunk in a neutral position."
            self.correct_back_form = False
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_neutral.mp3"
            if self._last_back_state != "neutral":
                save_snapshot(self.annotated, "bentOver_backNeutral_snapshot.jpg")
            self._last_back_state = "neutral"
        else:
            color = self.green
            message = "BACK FORM: Good back form."
            self.correct_back_form = True
            audio_text = f"{message}. Good job!"
            file_ending = ".mp3"
            if self._last_back_state != "good":
                save_snapshot(self.annotated, "bentOver_backGood_snapshot.jpg")
            self._last_back_state = "good"
        
        if self.tts:
            self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                text=audio_text,
                                                                                                filepath=f'feedback/back_feedback{file_ending}',
                                                                                                last_audio_end_time=self.last_audio_end_time,
                                                                                                color=color,
                                                                                                last_filepath=self.last_filepath,
                                                                                                green_queue=self.green_queue,
                                                                                                detected=self.detected,
                                                                                                play_local_audio=self.play_local_audio,
                                                                                                queue_audio_event=self.queue_audio_event
                                                                                            )

    def _check_range_of_motion(self, rom_achieved, init_pos):

        left_elbow_angle = calculate_angle(self.left_shoulder[:2], self.left_elbow[:2], self.left_wrist[:2])
        right_elbow_angle = calculate_angle(self.right_shoulder[:2], self.right_elbow[:2], self.right_wrist[:2])

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
                self.rom_start_time = time.monotonic()
                return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

            # Check if we are still within the ROM delay period to false trigger audio feedback and only provide feedback after the delay has passed
            if self.rom_start_time is not None and (time.monotonic() - self.rom_start_time) < self.rom_delay_seconds:
                return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks   
            
            if self.cam_pos == "front" and left_elbow_angle < range_of_motion_threshold or right_elbow_angle < range_of_motion_threshold and init_pos == False:
                color = self.green
                message = "RANGE OF MOTION: Good range of motion."
                audio_text = f"{message}. Good job!"
                rom_achieved = True
                file_ending = ".mp3"
                if self._last_rom_state != "good":
                    save_snapshot(self.annotated, "bentOver_romGood_snapshot.jpg")
                self._last_rom_state = "good"
            elif self.cam_pos == "left" and left_elbow_angle < range_of_motion_threshold and init_pos == False:
                color = self.green
                message = "RANGE OF MOTION: Good range of motion."
                audio_text = f"{message}. Good job!"
                rom_achieved = True
                file_ending = ".mp3"
                if self._last_rom_state != "good":
                    save_snapshot(self.annotated, "bentOver_romGood_snapshot.jpg")
                self._last_rom_state = "good"
            elif self.cam_pos == "right" and right_elbow_angle < range_of_motion_threshold and init_pos == False:
                color = self.green
                message = "RANGE OF MOTION: Good range of motion."
                audio_text = f"{message}. Good job!"
                rom_achieved = True
                file_ending = ".mp3"
                if self._last_rom_state != "good":
                    save_snapshot(self.annotated, "bentOver_romGood_snapshot.jpg")
                self._last_rom_state = "good"
            elif rom_achieved != True and init_pos == False:
                color = self.red
                message = "RANGE OF MOTION: Try to pull the weights higher for a better muscle activation."
                audio_text = f"{message}. Please adjust your form"
                file_ending = "_higher.mp3"
                if self._last_rom_state != "bad":
                    save_snapshot(self.annotated, "bentOver_romBad_snapshot.jpg")
                self._last_rom_state = "bad"
            else:
                color = self.grey
                message = "RANGE OF MOTION: Good, now lower the weights to the starting position."
                audio_text = f"{message}"
                file_ending = "_lower.mp3"

            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                    text=audio_text,
                                                                                                    filepath=f'feedback/bent_rom{file_ending}',
                                                                                                    last_audio_end_time=self.last_audio_end_time,
                                                                                                    color=color,
                                                                                                    last_filepath=self.last_filepath,
                                                                                                    green_queue=self.green_queue,
                                                                                                    detected=self.detected,
                                                                                                    play_local_audio=self.play_local_audio,
                                                                                                    queue_audio_event=self.queue_audio_event
                                                                                                )
        
        else:
            if rom_achieved:
                self.rep_counter += 1
            init_pos = True
            rom_achieved = False
            self.rom_start_time = None  # Reset ROM timer when arms are extended

        return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

    def _check_grip_width(self):

        left_dist_elbow_wrist = np.linalg.norm(self.left_elbow[:2] - self.left_wrist[:2])
        right_dist_elbow_wrist = np.linalg.norm(self.right_elbow[:2] - self.right_wrist[:2])
        dist_wrists = np.linalg.norm(self.left_wrist[:2] - self.right_wrist[:2])

        width_threshold = 2.4
        narrow_threshold = 1.5

        if (dist_wrists > width_threshold * left_dist_elbow_wrist or dist_wrists > width_threshold * right_dist_elbow_wrist) and self._last_grip_state != "good":
            color = self.red
            message = "GRIP WIDTH: Try to hold the barbell narrower"
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_narrower.mp3"
            if self._last_grip_state != "wide":
                save_snapshot(self.annotated, "bentOver_gripWide_snapshot.jpg")
            self._last_grip_state = "wide"

        elif dist_wrists < narrow_threshold * left_dist_elbow_wrist and dist_wrists < narrow_threshold * right_dist_elbow_wrist and self._last_grip_state != "good":
            color = self.red
            message = "GRIP WIDTH: Try to hold the barbell wider"
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_wider.mp3"
            if self._last_grip_state != "narrow":
                save_snapshot(self.annotated, "bentOver_gripNarrow_snapshot.jpg")
            self._last_grip_state = "narrow"

        else:
            color = self.green
            message = "GRIP WIDTH: Good grip width."
            audio_text = f"{message}. Good job!"
            file_ending = ".mp3"
            if self._last_grip_state != "good":
                save_snapshot(self.annotated, "bentOver_gripGood_snapshot.jpg")
            self._last_grip_state = "good"

        if self.tts:
            self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                    text=audio_text,
                                                                                                    filepath=f'feedback/bent_grip{file_ending}',
                                                                                                    last_audio_end_time=self.last_audio_end_time,
                                                                                                    color=color,
                                                                                                    last_filepath=self.last_filepath,
                                                                                                    green_queue=self.green_queue,
                                                                                                    detected=self.detected,
                                                                                                    play_local_audio=self.play_local_audio,
                                                                                                    queue_audio_event=self.queue_audio_event
                                                                                                )
    

        
    
