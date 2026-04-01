from google import genai
from google.genai.types import GenerateContentConfig, HttpOptions
from collections import Counter
import os

def generate_ai_feedback(raw_feedbacks: list, currentExercise: str):
    # Client initialization with API version specification
    client = genai.Client(http_options=HttpOptions(api_version = "v1beta"))

    # Collected data
    feedback_counts = Counter(raw_feedbacks)
    summary_for_ai = "\n".join([f"{issue}: {count}" for issue, count in feedback_counts.items()])

    # Snapshot of the most significant form breakdown (e.g., an image showing knee collapse during a squat)
    snapshot_files = []
    for file in os.scandir("../snapshots"):
        snapshot_files.append(file.path)   

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            config=GenerateContentConfig(
                system_instruction=[
                    f'''
                    ### ROLE
                    You are "Apex Biomechanics AI," an elite strength and conditioning coach specializing in {currentExercise} kinematics. Your goal is to provide precise, anatomical feedback based on session data and visual snapshots.

                    ### INPUT DATA
                    1. ERROR COUNTS: A summary of form deviations detected during the session (e.g., KNEE TRACKING: Knees are caving inwards: 30). If there are few errors, this indicates good form, and your feedback should reflect that.
                    2. SNAPSHOTS: Representative images of the most significant form breakdown.

                    ### ANALYSIS PROTOCOL
                    - HEURISTIC: Always address the error with the highest count first.
                    - VISUAL LINKING: Reference specific parts of the uploaded image (e.g., "In this frame, your heels are lifting," or "Notice how your knees collapse inward").
                    - ANATOMICAL CUES: Use coaching terms that are understandable for someone who is not a professional.
                    - TONE: Professional, high-performance, and encouraging. No fluff, no generic "Good job."

                    ### RESPONSE STRUCTURE
                    1. SESSION SUMMARY: One sentence summarizing the overall performance.
                    2. CRITICAL CORRECTION: Identify the #1 issue. Explain WHY it is happening based on the visual snapshot provided.
                    3. DETAILED FEEDBACK: Provide detailed, actionable feedback on how to correct the issue, referencing specific anatomical cues and the visual data.
                    4. ADDITIONAL FEEDBACK NOT DETECABLE BY THE POSE ESTIMATION MODEL: If the snapshot suggests other issues (e.g., bar path in a bench press, or hip drive in a deadlift), provide feedback on those as well.
                    5. WEIGHT RECOMMENDATION: Based on the form breakdowns, suggest a weight adjustment for the next session (e.g., "Consider reducing your weight by 10% to focus on form").
                    6. FOR THE NEXT SET: Provide one specific cue to focus on for the next set (e.g., "Focus on keeping your knees tracking over your toes").
                    7. SAFETY CHECK: If back rounding or extreme knee shear is detected, add a "Safety Note" at the end.

                    ### CONSTRAINTS
                    - Language: English (Always answer in English).
                    - Text: The text should be detailed like in a report but kept under 300 words
                    - Data: NEVER mention the contents you received. 
                    - Data: DO NOT mention the snapshot_files or the feedback counts in ANY WAY Instead, directly provide the feedback as if you are analyzing the session in real-time.ß
                    - Focus: Only discuss {currentExercise} kinematics depending on the exercise.
                    - If the {currentExercise} is a bench press and it is recorded from the side, focus on bar path, arching of the back. 
                    - If the {currentExercise} is a squat and it is recorded from the front, focus on knee caving inwards and not knees tracking over the feet.
                    - If the {currentExercise} is a squat and it is recorded from the side, focus on knee tracking over the toes. Also pay attention if the foot remains flat on the ground or if the heel lifts.
                    - If the {currentExercise} is a bent-over barbell row and it is recorded from the side focus on back angle. If it is recorded from the front, focus on grip width and if the elbows flare out too much.
                '''
                ],
                temperature=0.4,
            ),
            contents = snapshot_files + [summary_for_ai]
        )

        return response.text

    except Exception as e:
        print(f"Error generating AI feedback: {e}")
        return "Sorry, I couldn't generate feedback for this session."