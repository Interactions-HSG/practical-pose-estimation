import numpy as np
from ._angle_calculator import calculate_angle


def check_Squat_form(landmarks: np.array):
    if landmarks is None or landmarks.shape[0] != 33:
        print("Insufficient landmarks for squat form check.")
        return
    
    right_hip = landmarks[23] 
    right_knee = landmarks[25]
    right_ankle = landmarks[27] 

    left_hip = landmarks[24]
    left_knee = landmarks[26]
    left_ankle = landmarks[28]  

    if right_hip[4] < 0.95 or right_knee[4] < 0.95 or right_ankle[4] < 0.95 or left_hip[4] < 0.95 or left_knee[4] < 0.95 or left_ankle[4] < 0.95:
        print("Please adjust the camera for better visibility and remove any obstacles.")
        return
    else:
        right_knee_angle = calculate_angle(right_hip[:3], right_knee[:3], right_ankle[:3])
        left_knee_angle = calculate_angle(left_hip[:3], left_knee[:3], left_ankle[:3])

        # Certain threshold for squat depth is respected 
        if right_knee_angle <= 97 and left_knee_angle <= 97:
            print("Good squat depth!")
        else:
            print("Try to squat lower to achieve better depth.")

        
