from pose_estimator import PoseEstimator
from form_checkers import squat_formChecker, barbell_bentOver_formChecker, benchpress_formChecker
import cv2 

def main():
    mode = input("Enter mode ('1' for video file, '2' for live webcam): ")
    pose_estimator = PoseEstimator(mode=mode)

    print("Starting pose estimation...")
    while True:
        annotated = pose_estimator.run()
        points = pose_estimator.get_landmarks_result()
        squat_formChecker.check_Squat_form(points)
        cv2.imshow("Pose Landmarker", annotated)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    pose_estimator.cleanup()




if __name__ == "__main__":
    main()