import numpy as np
from ._utilityFunctions import calculate_angle, detect_cam_pos, play_audio_feedback, save_snapshot
import cv2
import pygame
import time

class BenchpressFormChecker:
    '''
    This class checks the form for benchpress exercises.
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
        self.initial_detection_timer_seconds = 10.0
        self.initial_detection_timer_started_at = None
        self.initial_detection_timer_done = False

        self.rep_counter = 0

        # Variables for AI feedback
        self.raw_feedbacks = []

        # Snapshot state tracking
        self._last_rom_state = None
        self._last_grip_state = None
        self._last_side_snapshot_at = 0.0
        self.side_snapshot_interval_seconds = 3.0


    def check_benchpress_form(self, annotated, landmarks: np.array, rom_achieved, init_pos):
        if landmarks is None or landmarks.shape[0] != 17:
            cv2.putText(self.annotated, "Insufficient landmarks for benchpress form check.", (10, 60), self.font, self.font_size, self.red, self.thickness, self.line)
            return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

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

            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                    text=message,
                                                                                                    filepath="feedback/camera_feedback.mp3", 
                                                                                                    last_audio_end_time=self.last_audio_end_time,
                                                                                                    color=self.red, 
                                                                                                    last_filepath=self.last_filepath,
                                                                                                    green_queue=self.green_queue, 
                                                                                                    detected=self.detected,
                                                                                                    play_local_audio=self.play_local_audio, 
                                                                                                    queue_audio_event=self.queue_audio_event)
            return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

        else:
            message = "You have been detected!"
            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                    text=message,
                                                                                                    filepath="feedback/camera_feedback.mp3",
                                                                                                    last_audio_end_time=self.last_audio_end_time,
                                                                                                    color=self.green,
                                                                                                    last_filepath=self.last_filepath,
                                                                                                    green_queue=self.green_queue,
                                                                                                    detected=self.detected,
                                                                                                    play_local_audio=self.play_local_audio,
                                                                                                    queue_audio_event=self.queue_audio_event
                                                                                                )
            # Show both grip width and ROM feedback for benchpress YOLO setup.
            if self.detected:
                if not self.initial_detection_timer_done:
                    if self.initial_detection_timer_started_at is None:
                        self.initial_detection_timer_started_at = time.monotonic()
                        return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

                    elapsed = time.monotonic() - self.initial_detection_timer_started_at
                    if elapsed < self.initial_detection_timer_seconds:
                        return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

                    self.initial_detection_timer_done = True
                    self.initial_detection_timer_started_at = None

                if cam_pos == "front":
                    self._check_grip_width()
                    rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks = self._check_range_of_motion(rom_achieved, init_pos)
                elif cam_pos in ("left", "right"):
                    self._capture_side_snapshot_if_due(cam_pos)
            
        return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

    def _capture_side_snapshot_if_due(self, cam_pos: str):
        now = time.monotonic()
        if now - self._last_side_snapshot_at < self.side_snapshot_interval_seconds:
            return

        timestamp = time.strftime("%M%S")
        save_snapshot(self.annotated, f"benchpress_side_{cam_pos}_{timestamp}.jpg")
        self._last_side_snapshot_at = now

    def _check_range_of_motion(self, rom_achieved, init_pos):

        left_elbow_angle = calculate_angle(self.left_shoulder[:2], self.left_elbow[:2], self.left_wrist[:2])
        right_elbow_angle = calculate_angle(self.right_shoulder[:2], self.right_elbow[:2], self.right_wrist[:2])

        elbow_flexion_threshold = 145
        range_of_motion_threshold = 50

        if left_elbow_angle < elbow_flexion_threshold and right_elbow_angle < elbow_flexion_threshold:
            # Start of Movement (Important for ROM check and to avoid false triggers)
            if init_pos:
                init_pos = False
                self.rom_start_time = time.time()
                return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

            # Check if we are still within the ROM delay period to false trigger audio feedback and only provide feedback after the delay has passed
            if self.rom_start_time is not None and (time.time() - self.rom_start_time) < self.rom_delay_seconds:
                return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

            if left_elbow_angle < range_of_motion_threshold or right_elbow_angle < range_of_motion_threshold:
                color = self.green
                message = "RANGE OF MOTION: Good range of motion."
                audio_text = f"{message}. Good job"
                rom_achieved = True
                file_ending = ".mp3"
                if self._last_rom_state != "good":
                    save_snapshot(self.annotated, "benchpress_romGood_snapshot.jpg")
                self._last_rom_state = "good"
            elif rom_achieved != True and init_pos == False:
                color = self.red
                message = "RANGE OF MOTION: Try to lower the weights to your lower chest for a better muscle activation."
                audio_text = f"{message}. Please adjust your form"
                file_ending = "_lower.mp3"
                if self._last_rom_state != "bad":
                    save_snapshot(self.annotated, "benchpress_romBad_snapshot.jpg")
                self._last_rom_state = "bad"
            else:
                color = self.red
                message = "RANGE OF MOTION: Try to push up the weights until your arms are fully extended."
                audio_text = f"{message}. Please adjust your form"
                file_ending = "_extended.mp3"
                if self._last_rom_state != "extended":
                    save_snapshot(self.annotated, "benchpress_romExtended_snapshot.jpg")
                self._last_rom_state = "extended"

            if self.tts:
                self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                    text=audio_text, 
                                                                                                    filepath=f"feedback/benchpress_rom{file_ending}", 
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
                self.rep_counter+= 1
            init_pos = True
            rom_achieved = False


        return rom_achieved, init_pos, self.detected, self.initial_detection_timer_done, self.rep_counter, self.raw_feedbacks

    def _check_grip_width(self):

        dist_shoulders = np.linalg.norm(self.right_shoulder[:2] - self.left_shoulder[:2])
        grip_width = np.linalg.norm(self.right_wrist[:2] - self.left_wrist[:2]) 

        grip_width_threshold_min = 1.75 * dist_shoulders
        grip_width_threshold_max = 2.25 * dist_shoulders

        if grip_width < grip_width_threshold_min:
            color = self.red
            message = "GRIP WIDTH: Try to widen your grip"
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_wider.mp3"
            if self._last_grip_state != "narrow":
                save_snapshot(self.annotated, "benchpress_gripNarrow_snapshot.jpg")
            self._last_grip_state = "narrow"
        elif grip_width > grip_width_threshold_max:
            color = self.red
            message = "GRIP WIDTH: Try to narrow your grip"
            audio_text = f"{message}. Please adjust your form"
            file_ending = "_narrower.mp3"
            if self._last_grip_state != "wide":
                save_snapshot(self.annotated, "benchpress_gripWide_snapshot.jpg")
            self._last_grip_state = "wide"
        else:
            color = self.green
            message = "GRIP WIDTH: Good grip width"
            audio_text = f"{message}. Good job!"
            file_ending = ".mp3"
            if self._last_grip_state != "good":
                save_snapshot(self.annotated, "benchpress_gripGood_snapshot.jpg")
            self._last_grip_state = "good"

        if self.tts:
            self.last_audio_end_time, self.last_filepath, self.green_queue, self.detected = play_audio_feedback(
                                                                                                text=audio_text, 
                                                                                                filepath=f"feedback/benchpress_grip{file_ending}", 
                                                                                                last_audio_end_time=self.last_audio_end_time, 
                                                                                                color=color,
                                                                                                last_filepath=self.last_filepath, 
                                                                                                green_queue=self.green_queue,
                                                                                                detected=self.detected,
                                                                                                play_local_audio=self.play_local_audio,
                                                                                                queue_audio_event=self.queue_audio_event
                                                                                                )
