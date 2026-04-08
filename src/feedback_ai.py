from google import genai
import anthropic
from google.genai.types import GenerateContentConfig, HttpOptions
from collections import Counter
import os
import base64
import mimetypes
import requests

def generate_ai_feedback(raw_feedbacks: list, currentExercise: str):
    # Client initialization with API version specification
    client = genai.Client(http_options=HttpOptions(api_version = "v1beta"))
    claude_client = anthropic.Client()

    # Collected data
    feedback_counts = Counter(raw_feedbacks)
    summary_for_ai = "\n".join([f"{issue}: {count}" for issue, count in feedback_counts.items()])

    # Snapshot of the most significant form breakdown (e.g., an image showing knee collapse during a squat)
    snapshot_files = []
    for file in os.scandir("../snapshots"):
        snapshot_files.append(file.path)  

    # System instructions for the AI model, tailored to the specific exercise and the type of feedback received. The instructions guide the AI to provide detailed, actionable feedback based on the form breakdowns detected during the session, while also referencing the visual data from the snapshots. The AI is prompted to focus on the most critical issue first and to provide a comprehensive analysis that includes safety considerations and weight recommendations for future sessions.

    structured_instruction = f'''
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
                    - Data: DO NOT mention the snapshot_files or the feedback counts in ANY WAY Instead, directly provide the feedback as if you are analyzing the session in real-time.
                    - Feedback: If the feedback counts indicate good form (e.g., very low counts of errors), the session summary should reflect that positively and not try to find issues, and the critical correction should focus on reinforcing good habits rather than correcting issues.
                    - Focus: Only discuss {currentExercise} kinematics.
                    - If there is no indication of errors in {summary_for_ai} DO NOT mention it at all. Only provide feedback on the issues that are actually present in the feedback counts and the snapshot.
                    '''

    # List of Gemini models to try in order
    gemini_models = ["gemini-3-flash-preview", "gemini-2.5-flash"]
    
    for model in gemini_models:
        try:
            response = client.models.generate_content(
                model=model,
                config=GenerateContentConfig(
                    system_instruction=[
                        structured_instruction
                    ],
                    temperature=0.4,
                ),
                contents = snapshot_files + [summary_for_ai]
            )
            return response.text
        except Exception as e:
            print(f"Error generating AI feedback with {model}: {e}")
            # Continue to the next model
            continue


    try:
        claude_images = []
        for image_path in snapshot_files:
            media_type, _ = mimetypes.guess_type(image_path)
            if media_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
                continue

            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

            claude_images.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": encoded_image,
                    },
                }
            )

        claude_response = claude_client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=700,
            temperature=0.4,
            system=structured_instruction,
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": summary_for_ai}] + claude_images,
                }
            ],
        )

        text_blocks = [block.text for block in claude_response.content if hasattr(block, "text")]
        return "\n".join(text_blocks).strip()

    except Exception as inner_e:
        print(f"Error generating fallback feedback: {inner_e}")
          # Fallback to Ollama (local, free, unlimited)

        try:
            print("Attempting Ollama vision fallback...")

            ollama_images = []
            for image_path in snapshot_files:
                media_type, _ = mimetypes.guess_type(image_path)
                if media_type not in {"image/jpeg", "image/png", "image/webp"}:
                    continue

                with open(image_path, "rb") as image_file:
                    ollama_images.append(base64.b64encode(image_file.read()).decode("utf-8"))

            ollama_payload = {
                "model": "llava",
                "prompt": f"{structured_instruction}\n\nSession Data:\n{summary_for_ai}",
                "stream": False,
                "temperature": 0.4,
            }

            if ollama_images:
                ollama_payload["images"] = ollama_images

            ollama_response = requests.post(
                "http://localhost:11434/api/generate",
                json=ollama_payload,
                timeout=180,
            )
            ollama_response.raise_for_status()
            return ollama_response.json().get("response", "").strip()

        except Exception as ollama_e:
            print(f"Error generating Ollama feedback: {ollama_e}")
            return (
                "Sorry, I couldn't generate feedback for this session. "
                "Please ensure Ollama vision is running "
                "(e.g., `ollama pull llava && ollama run llava`)."
            )
