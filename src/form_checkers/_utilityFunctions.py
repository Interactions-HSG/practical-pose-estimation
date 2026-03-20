from collections import deque
import numpy as np
import time
import os
from gtts import gTTS
import pygame

def calculate_angle(a, b, c):
    a = np.array(a)  
    b = np.array(b)  
    c = np.array(c)  

    ba = a - b
    bc = c - b

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)

    return np.degrees(angle)


def detect_cam_pos(landmarks: list, standing = True):
    # Split landmarks in the middle to separate right and left sides
    # This works for both benchpress (6 landmarks) and bentover (10 landmarks)
    mid = len(landmarks) // 2
    right_landmarks = landmarks[0:mid]
    left_landmarks = landmarks[mid:]

    if standing:
        right_visibility = [lm[3] for lm in right_landmarks]
        left_visibility = [lm[3] for lm in left_landmarks]
        if np.mean(right_visibility) > 0.95 and np.mean(left_visibility) > 0.95:
            return "front"
        elif np.mean(right_visibility) > 0.95:
            return "right"
        elif np.mean(left_visibility) > 0.95:
            return "left"
        else:
            return "unknown"
    elif standing == False:  
        # Count the number of confidently detected keypoints on each side as YOLO does not have a visibility value
        right_count = sum(1 for lm in right_landmarks if lm[2] > 0.7)  
        left_count = sum(1 for lm in left_landmarks if lm[2] > 0.7)
        
        if right_count > left_count * 1.2:
            return "right"
        elif left_count > right_count * 1.2:
            return "left"
        else:
            return "front"

def play_audio_feedback(
    text,
    filepath,
    last_audio_end_time,
    color,
    last_filepath,
    green_queue,
    detected,
    red_cooldown=2.0,
    green_cooldown=5.0,
):
    current_time = time.time()
    green = (0, 255, 0)
    red = (0, 0, 255)

    is_green = color == green
    is_red = color == red

    if green_queue is None:
        green_queue = deque()

    if is_green:
        filepath = filepath.split('.')[0] + '_green.mp3'

    def ensure_audio_file_exists(path, feedback_text):
        if feedback_text and not os.path.exists(path):
            tts = gTTS(text=feedback_text, lang='en')
            tts.save(path)

    # If the feedback is red, play immediately if not on cooldown. Skip all green feedback
    if is_red:
        ensure_audio_file_exists(filepath, text)
        was_last_green = isinstance(last_filepath, str) and last_filepath.endswith('_green.mp3')
        if current_time >= last_audio_end_time or was_last_green:
            pygame.mixer.music.stop()
            green_queue.clear()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            estimated_audio_length = 5.0
            last_audio_end_time = current_time + estimated_audio_length + red_cooldown
            last_filepath = filepath
        return last_audio_end_time, last_filepath, green_queue, detected
    
    # If the feedback is green, queue it to play after current audio finishes. Do not play if same feedback just played
    if is_green:
        if filepath == last_filepath:
            return last_audio_end_time, last_filepath, green_queue, detected
        
        if detected is False and all(item[0] != filepath for item in green_queue):
            green_queue.append((filepath, text))

    #If currently no audio is playing and there are green feedback queued, play the next one in the queue 
    if not pygame.mixer.music.get_busy() and current_time >= last_audio_end_time:
            if green_queue:
                next_filepath, next_text = green_queue.popleft()
                ensure_audio_file_exists(next_filepath, next_text)
                pygame.mixer.music.load(next_filepath)
                pygame.mixer.music.play()
                if next_text == "You have been detected!":
                    detected = True
                estimated_audio_length = 3.0

                #If the queue is not empty yet -> Play the remaining messages and then insert a cooldown
                if len(green_queue) > 0:
                    last_audio_end_time = current_time + estimated_audio_length
                else:
                    last_audio_end_time = current_time + estimated_audio_length + green_cooldown
                last_filepath = next_filepath

    return last_audio_end_time, last_filepath, green_queue, detected

