from pose_estimator import PoseEstimator
from form_checkers import SquatFormChecker, BenchpressFormChecker, BentOverRowFormChecker
import cv2 

def main():

    # Get mode from user input
    mode = input("Enter mode ('1' for video file, '2' for live webcam): ")

    if mode == 'q':
        print("Exiting program.")
        return 
    
    exercise = input("Enter exercise type ('squat', 'bench', 'bent'): ")

    pose_estimator = PoseEstimator(mode=mode)
    squat_checker = SquatFormChecker() 
    benchpress_checker = BenchpressFormChecker()
    bentOver_checker = BentOverRowFormChecker()
    depth_achieved = False 
    correct_back_form = False
    rom_achieved = False
    init_pos = True 


    print("Starting pose estimation...")
    while True:
        annotated = pose_estimator.run()
        if annotated is None:
            break
        points = pose_estimator.get_landmarks_result()
        points_2d = pose_estimator.get_landmarks_2d()
        
        if points is not None:
            match exercise:
                case 'squat':
                    depth_achieved = squat_checker.check_Squat_form(annotated, points, depth_achieved)
                case 'bench':
                    rom_achieved, init_pos = benchpress_checker.check_benchpress_form(annotated, points, rom_achieved, init_pos, points_2d)
                case 'bent':
                    correct_back_form, rom_achieved, init_pos = bentOver_checker.check_bentover_form(annotated, points, correct_back_form, rom_achieved, init_pos, points_2d)
                case _:
                    print("Invalid exercise type. Please enter 'squat', 'bench', or 'bent'.")
                    break
        
        cv2.imshow("Visual Spotter", annotated)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    pose_estimator.cleanup()

if __name__ == "__main__":
    main()