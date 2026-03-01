import numpy as np

def calculate_angle(a, b, c):
    a = np.array(a)  
    b = np.array(b)  
    c = np.array(c)  

    ba = a - b
    bc = c - b

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)

    return np.degrees(angle)


def detect_cam_pos(landmarks: list):
    # Split landmarks in the middle to separate right and left sides
    # This works for both benchpress (6 landmarks) and bentover (10 landmarks)
    mid = len(landmarks) // 2
    right_landmarks = landmarks[0:mid]
    left_landmarks = landmarks[mid:]

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