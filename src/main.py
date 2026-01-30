from pose_estimator import PoseEstimator
from src.form_checkers.squat_formChecker import Squat_Form_Checker
from src.form_checkers.barbell_bentOver_formChecker import Barbell_Bent_Over_Row_Form_Checker
from src.form_checkers.benchpress_formChecker import Benchpress_Form_Checker
import cv2 

def main():
    mode = input("Enter mode ('1' for video file, '2' for live webcam): ")
    pose_estimator = PoseEstimator(mode=mode)
    squat_form_checker = Squat_Form_Checker()
    barbell_form_checker = Barbell_Bent_Over_Row_Form_Checker()
    benchpress_form_checker = Benchpress_Form_Checker()


    print("Starting pose estimation...")
    while True:
        annotated = pose_estimator.run()
        points = pose_estimator.get_landmarks_result()
        squat_form_checker.check_form(points)
        cv2.imshow("Pose Landmarker", annotated)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    pose_estimator.cleanup()


main()