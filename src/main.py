from pose_estimator import PoseEstimator
from pose_estimator_supine import PoseEstimatorSupine
from form_checkers import SquatFormChecker, BenchpressFormChecker, BentOverRowFormChecker
import cv2 

def main():

    # Get mode from user input
    mode = input("Enter mode ('1' for video file, '2' for live webcam): ")

    if mode == 'q':
        print("Exiting program.")
        return 
    
    # Exercises split and stored in lists for extensibility
    available_exercises = ['squat', 'bent']
    available_supine_exercises = ['bench']
    exercise_display = ', '.join(map(str, available_exercises + available_supine_exercises))
    chosen_exercise = input(f"Enter exercise type {exercise_display}: ")

    if chosen_exercise == 'q':
        print("Exiting program.")
        return

    #Depending on the user choice, initialize the appropriate Pose Estimation Model
    if chosen_exercise in available_exercises:
        pose_estimator = PoseEstimator(mode=mode)
    if chosen_exercise in available_supine_exercises:
        pose_estimator_supine = PoseEstimatorSupine(mode=mode)

    #Form Checkers
    squat_checker = SquatFormChecker() 
    benchpress_checker = BenchpressFormChecker()
    bentOver_checker = BentOverRowFormChecker()

    depth_achieved = False 
    correct_back_form = False
    rom_achieved = False
    init_pos = True 


    print("Starting pose estimation...")
    while True:
        try:
            #Run the MediaPipe Model for standing exercises
            if chosen_exercise in available_exercises:
                annotated = pose_estimator.run()
                if annotated is None:
                    break
                points = pose_estimator.get_landmarks_result()
                if points is not None:
                    match chosen_exercise:
                        case 'squat':
                            depth_achieved = squat_checker.check_Squat_form(annotated, points, depth_achieved)
                        case 'bent':
                            correct_back_form, rom_achieved, init_pos = bentOver_checker.check_bentover_form(annotated, points, correct_back_form, rom_achieved, init_pos)
                        case _:
                            print(f"Invalid exercise type. Please enter {exercise_display}.")
                            break

            #Run the YOLO Model for supine exercises for higher accuracy
            elif chosen_exercise in available_supine_exercises:
                annotated = pose_estimator_supine.run()
                if annotated is None:
                    break
                points = pose_estimator_supine.get_landmarks_result()
                if points is not None:
                    match chosen_exercise:
                        case 'bench':
                            # YOLO can return either (17, 3) for one person or (num_people, 17, 3) for many.
                            if points.ndim == 2:
                                person_points = points
                            else:
                                best_idx = int(points[:, :, 2].mean(axis=1).argmax())
                                person_points = points[best_idx]
                            rom_achieved, init_pos = benchpress_checker.check_benchpress_form(annotated, person_points, rom_achieved, init_pos)
                        case _:
                            print(f"Invalid exercise type. Please enter {exercise_display}.")
                            break            
        except Exception as e:
            print(f"Error during pose estimation: {e}")
            continue
        
        cv2.imshow("Visual Spotter", annotated)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    if chosen_exercise in available_exercises:
        pose_estimator._cleanup()
    if chosen_exercise in available_supine_exercises:
        pose_estimator_supine._cleanup()

if __name__ == "__main__":
    main()