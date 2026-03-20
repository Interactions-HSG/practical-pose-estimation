import os
import urllib.request


def download_packets(target_path):
    if os.path.exists(target_path):
        return
    
    print(f"Model not found at '{target_path}'. Downloading...")
    download_url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task"
    try:
        urllib.request.urlretrieve(download_url, target_path)
    except Exception as exc:
        raise RuntimeError(f"Failed to download model from {download_url}: {exc}") from exc

    print(f"Model downloaded: {target_path}")

def create_required_directories(target_path):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    new_directory = os.path.join(project_root, target_path)
    if not os.path.exists(new_directory):
        os.makedirs(new_directory)
        print(f"Directory '{new_directory}' created.")
    
    return new_directory
