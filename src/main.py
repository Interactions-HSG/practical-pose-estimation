from pose_estimator import PoseEstimator
from pose_estimator_supine import PoseEstimatorSupine
from form_checkers import SquatFormChecker, BenchpressFormChecker, BentOverRowFormChecker
from init_functions import download_packets, create_required_directories
import cv2 
import os

def main():
    video_dir = create_required_directories('videos')
    trained_models_dir = create_required_directories('trained_models')
    feedback_dir = create_required_directories('src/feedback')
    # Get mode from user input
    mode = None
    while mode is None:
        mode = input("Enter mode ('1' for video file, '2' for live webcam): ")

        if mode == 'q':
            print("Exiting program.")
            return
        
        if mode not in ['1', '2', 'q']:
            print("Invalid mode. Please enter '1' for video file, '2' for live webcam, or 'q' to quit.")
            mode = None
        
    # Exercises split and stored in lists for extensibility
    available_exercises = ['squat', 'bent']
    available_supine_exercises = ['bench']
    exercise_display = ', '.join(map(str, available_exercises + available_supine_exercises))

    tts = None
    while tts is None:
        tts = input(f"Do you want audio feedback? (y/n): ")
        if tts not in ['y', 'n']:
            print("Invalid input. Please enter 'y' for yes or 'n' for no.")
            tts = None
        
        if tts == 'y':
            tts = True
        elif tts == 'n':
            tts = False


    chosen_exercise = None
    while chosen_exercise is None:
        chosen_exercise = input(f"Enter exercise type ({exercise_display}): ")
        
        if chosen_exercise == 'q':
            print("Exiting program.")
            return
        
        if chosen_exercise not in available_exercises + available_supine_exercises:
            print(f"Invalid exercise type. Please enter one of: {exercise_display}")
            chosen_exercise = None

    #Depending on the user choice, initialize the appropriate Pose Estimation Model
    if chosen_exercise in available_exercises:
        pose_model_path = os.path.join(trained_models_dir, 'pose_landmarker_full.task')
        download_packets(pose_model_path)
        pose_estimator = PoseEstimator(mode=mode, model_path=pose_model_path)

    if chosen_exercise in available_supine_exercises:
        pose_estimator_supine = PoseEstimatorSupine(mode=mode)

    #Form Checkers
    squat_checker = SquatFormChecker(tts, True, None) 
    benchpress_checker = BenchpressFormChecker(tts, True, None)
    bentOver_checker = BentOverRowFormChecker(tts, True, None)

    rom_achieved = False
    init_pos = True 


    print("Starting pose estimation...")
    while True:

        #Run the MediaPipe Model for standing exercises
        if chosen_exercise in available_exercises:
            annotated = pose_estimator.run()
            if annotated is None:
                break
            points = pose_estimator.get_landmarks_result()
            if points is not None:
                match chosen_exercise:
                    case 'squat':
                        rom_achieved, init_pos, _, _ = squat_checker.check_Squat_form(annotated, points, rom_achieved, init_pos)
                    case 'bent':
                        rom_achieved, init_pos, _, _ = bentOver_checker.check_bentover_form(annotated, points, rom_achieved, init_pos)

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
                        rom_achieved, init_pos, _, _ = benchpress_checker.check_benchpress_form(annotated, person_points, rom_achieved, init_pos)

        cv2.imshow("Visual Spotter", annotated)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    if chosen_exercise in available_exercises:
        pose_estimator._cleanup()
    if chosen_exercise in available_supine_exercises:
        pose_estimator_supine._cleanup()

if __name__ == "__main__":
    main()