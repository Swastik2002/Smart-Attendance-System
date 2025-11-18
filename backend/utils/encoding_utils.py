# utils/encoding_utils.py
import os
import json
from flask import current_app

def get_model_dir():
    # models stored inside UPLOAD_FOLDER/models by default
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
    model_dir = os.path.join(upload_folder, "models")
    os.makedirs(model_dir, exist_ok=True)
    return model_dir

def labels_path():
    return os.path.join(get_model_dir(), "labels.json")

def model_path():
    return os.path.join(get_model_dir(), "lbph_model.yml")

def save_label_map(label_map: dict):
    """
    label_map: dict mapping student_id (str or int) -> label_index (int)
    """
    p = labels_path()
    with open(p, "w") as f:
        json.dump({str(k): int(v) for k, v in label_map.items()}, f)
    return True

def load_label_map():
    p = labels_path()
    if not os.path.exists(p):
        return {}
    with open(p, "r") as f:
        data = json.load(f)
    # keys are strings in file — keep them as str for consistent lookups
    return {str(k): int(v) for k, v in data.items()}
