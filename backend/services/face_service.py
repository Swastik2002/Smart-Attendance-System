import os
import pickle
import face_recognition
import cv2
import numpy as np
from flask import current_app
from config import Config
from utils.encoding_utils import load_encodings, save_encodings

def train_student_face(student_id):
    student_folder = os.path.join(Config.UPLOAD_FOLDER, str(student_id))

    if not os.path.exists(student_folder):
        raise Exception(f"No images found for student {student_id}")

    encodings_data = load_encodings()

    student_encodings = []

    for image_name in os.listdir(student_folder):
        image_path = os.path.join(student_folder, image_name)

        image = face_recognition.load_image_file(image_path)

        face_encodings = face_recognition.face_encodings(image)

        if len(face_encodings) > 0:
            student_encodings.append(face_encodings[0])

    if len(student_encodings) == 0:
        raise Exception(f"No faces detected in images for student {student_id}")

    encodings_data[str(student_id)] = student_encodings

    save_encodings(encodings_data)

    return True

def recognize_face_from_image(image_file):
    try:
        encodings_data = load_encodings()

        if not encodings_data:
            return {
                'success': False,
                'message': 'No face encodings found. Please train the system first.'
            }

        image_bytes = image_file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        if len(face_encodings) == 0:
            return {
                'success': False,
                'message': 'No face detected in the image'
            }

        unknown_encoding = face_encodings[0]

        best_match_student_id = None
        best_match_distance = float('inf')

        for student_id, known_encodings in encodings_data.items():
            for known_encoding in known_encodings:
                distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]

                if distance < best_match_distance:
                    best_match_distance = distance
                    best_match_student_id = student_id

        threshold = 0.6

        if best_match_distance < threshold:
            confidence = (1 - best_match_distance) * 100

            return {
                'success': True,
                'student_id': int(best_match_student_id),
                'confidence': round(confidence, 2)
            }
        else:
            return {
                'success': False,
                'message': 'Face not recognized'
            }

    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }
