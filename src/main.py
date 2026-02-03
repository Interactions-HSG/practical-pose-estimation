from pose_estimator import PoseEstimator
from form_checkers import SquatFormChecker
import cv2 

def main():

    # Get mode from user input
    mode = input("Enter mode ('1' for video file, '2' for live webcam): ")
    pose_estimator = PoseEstimator(mode=mode)

    print("Starting pose estimation...")
    while True:
        annotated = pose_estimator.run()
        points = pose_estimator.get_landmarks_result()
        
        if points is not None:
            annotated = SquatFormChecker(points).check_Squat_form(annotated)
        
        cv2.imshow("Pose Landmarker", annotated)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    pose_estimator.cleanup()




if __name__ == "__main__":
    main()