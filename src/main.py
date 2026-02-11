from pose_estimator import PoseEstimator
from form_checkers import SquatFormChecker, BenchpressFormChecker, BentOverRowFormChecker
import cv2 

def main():

    # Get mode from user input
    mode = input("Enter mode ('1' for video file, '2' for live webcam): ")

    if mode == 'q':
        print("Exiting program.")
        return

    pose_estimator = PoseEstimator(mode=mode)
    squat_checker = SquatFormChecker() 
    benchpress_checker = BenchpressFormChecker()
    bentOver_checker = BentOverRowFormChecker()
    depth_achieved = False 

    print("Starting pose estimation...")
    while True:
        annotated = pose_estimator.run()
        if annotated is None:
            break
        points = pose_estimator.get_landmarks_result()
        
        if points is not None:
            depth_achieved = squat_checker.check_Squat_form(annotated, points, depth_achieved)
        
        cv2.imshow("Visual Spotter", annotated)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    pose_estimator.cleanup()

if __name__ == "__main__":
    main()