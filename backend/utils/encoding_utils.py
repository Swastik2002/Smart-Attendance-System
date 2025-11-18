import os
import pickle
from config import Config

def load_encodings():
    encodings_file = Config.ENCODINGS_FILE

    if os.path.exists(encodings_file):
        with open(encodings_file, 'rb') as f:
            return pickle.load(f)
    else:
        return {}

def save_encodings(encodings_data):
    encodings_file = Config.ENCODINGS_FILE

    with open(encodings_file, 'wb') as f:
        pickle.dump(encodings_data, f)

    return True
