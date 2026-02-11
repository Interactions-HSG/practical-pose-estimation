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

# Used for back form check in squat form checker - Is not reliant on three points like the above method
def findAngle(x1, y1, x2, y2):
    theta = np.arccos( (y2 -y1)*(-y1) / (np.sqrt(
        (x2 - x1)**2 + (y2 - y1)**2 ) * y1) )
    degree = int(180/np.pi)*theta
    return degree