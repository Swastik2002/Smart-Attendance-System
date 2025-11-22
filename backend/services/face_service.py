# backend/services/face_service.py
import os
import cv2
import numpy as np
import base64
from deepface import DeepFace as df
from flask import current_app
from config import Config

KNOWN_FACES_DIR = os.path.join(Config.UPLOAD_FOLDER, "known_faces")
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

def _ensure_student_folder(student_id):
    student_folder = os.path.join(KNOWN_FACES_DIR, str(student_id))
    os.makedirs(student_folder, exist_ok=True)
    return student_folder

def copy_student_to_known(student_id):
    summary = {'copied': 0, 'errors': []}
    src_folder = os.path.join(Config.UPLOAD_FOLDER, str(student_id))
    if not os.path.exists(src_folder) or not os.path.isdir(src_folder):
        summary['errors'].append(f"Source folder not found: {src_folder}")
        return summary

    dest_folder = _ensure_student_folder(student_id)

    try:
        existing = set(os.listdir(dest_folder))
        for fname in sorted(os.listdir(src_folder)):
            src_path = os.path.join(src_folder, fname)
            if not os.path.isfile(src_path):
                continue
            base_ext = os.path.splitext(fname)[1] or ".jpg"
            next_index = len([f for f in os.listdir(dest_folder) if os.path.isfile(os.path.join(dest_folder, f))]) + 1
            dest_name = f"{student_id}_{next_index}{base_ext}"
            dest_path = os.path.join(dest_folder, dest_name)
            if os.path.exists(dest_path):
                continue
            try:
                with open(src_path, "rb") as fr, open(dest_path, "wb") as fw:
                    fw.write(fr.read())
                summary['copied'] += 1
            except Exception:
                try:
                    frame = cv2.imread(src_path)
                    if frame is not None:
                        cv2.imwrite(dest_path, frame)
                        summary['copied'] += 1
                    else:
                        summary['errors'].append(f"cv2 failed to read {src_path}")
                except Exception as e2:
                    summary['errors'].append(f"failed to copy {src_path}: {str(e2)}")
    except Exception as e:
        summary['errors'].append(str(e))

    return summary

def train_student_face(student_id):
    try:
        res = copy_student_to_known(student_id)
        dest_folder = os.path.join(KNOWN_FACES_DIR, str(student_id))
        files = [f for f in os.listdir(dest_folder) if os.path.isfile(os.path.join(dest_folder, f))]
        if len(files) == 0:
            raise Exception(f"No images present in known_faces for student {student_id} after copy: {dest_folder}")
        return {'success': True, 'student_id': student_id, 'copied': res.get('copied', 0), 'errors': res.get('errors', [])}
    except Exception as e:
        current_app.logger.exception("train_student_face error")
        return {'success': False, 'message': str(e)}

def _frame_from_file_storage(file_storage):
    file_bytes = file_storage.read()
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def _annotate_frame(frame, face_entries):
    """
    face_entries: list of dicts { bbox: [x,y,w,h], student_name, status }
    status: 'matched' | 'unknown' | 'already_marked'
    """
    # draw boxes and labels
    for ent in face_entries:
        loc = ent.get('bbox', [0,0,0,0])
        name = ent.get('student_name') or ent.get('name') or "UNKNOWN"
        status = ent.get('status', 'unknown')
        x, y, w, h = map(int, loc)

        if status == 'unknown':
            box_color = (0, 0, 255)     # red
            font_color = (0, 0, 255)
            thick = 3
        elif status == 'already_marked':
            box_color = (0, 0, 0)       # black
            font_color = (0, 255, 0)
            thick = 2
        else:
            box_color = (0, 255, 0)     # green
            font_color = (0, 0, 0)
            thick = 2

        cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, thick)
        # label background
        label = str(name)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        lx = max(0, x)
        ly = max(0, y - th - 8)
        # draw filled rectangle as label background
        cv2.rectangle(frame, (lx, ly), (lx + tw + 8, ly + th + 6), (0,0,0), -1)
        cv2.putText(frame, label, (lx + 4, ly + th - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, font_color, 2)
    return frame

def recognize_face_from_image(image_file):
    """
    Returns:
      {
        success: bool,
        results: [ { student_id, student_name, confidence, bbox, status } ... ],
        annotated_base64: <data:image/jpeg;base64,...> (if produced),
        message: optional
      }
    """
    try:
        frame = _frame_from_file_storage(image_file)
        if frame is None:
            return {'success': False, 'message': 'Invalid image uploaded'}

        # use DeepFace.find to get matches for all faces in the image
        matches = df.find(
            img_path=frame,
            db_path=KNOWN_FACES_DIR,
            model_name='Facenet512',
            distance_metric='cosine',
            enforce_detection=False,
            detector_backend='retinaface',
            align=True,
            expand_percentage=5,
        )

        # matches is list of dataframes when there are faces; if no faces, it may be empty or None
        results = []
        face_entries_for_annot = []

        if matches and len(matches) > 0:
            for dataframe in matches:
                if dataframe is None or dataframe.empty:
                    continue

                # bounding box in source image
                try:
                    x = int(dataframe['source_x'].iloc[0])
                    y = int(dataframe['source_y'].iloc[0])
                    w = int(dataframe['source_w'].iloc[0])
                    h = int(dataframe['source_h'].iloc[0])
                except Exception:
                    x, y, w, h = 0,0,0,0

                # find best (minimum) distance row for this face
                try:
                    min_row = dataframe.loc[dataframe['distance'].idxmin()]
                    distance = float(min_row['distance'])
                    identity_path = min_row['identity']
                except Exception:
                    distance = 1.0
                    identity_path = None

                # derive student id/name from identity_path if possible
                student_id = None
                student_name = "UNKNOWN"
                if identity_path:
                    try:
                        rel = os.path.relpath(identity_path, KNOWN_FACES_DIR)
                        parts = rel.split(os.sep)
                        # expected known_faces/<student_id>/<imagefile>
                        if len(parts) >= 2 and parts[0].isdigit():
                            student_id = int(parts[0])
                            # temporary name set to ID string; route can replace with DB name
                            student_name = str(student_id)
                        else:
                            base = os.path.basename(identity_path)
                            face_name = os.path.splitext(base)[0]
                            student_name = ''.join(filter(lambda x: not x.isdigit(), face_name)).strip() or face_name
                    except Exception:
                        base = os.path.basename(identity_path)
                        face_name = os.path.splitext(base)[0]
                        student_name = ''.join(filter(lambda x: not x.isdigit(), face_name)).strip() or face_name

                confidence = round((1.0 - distance) * 100, 2) if distance <= 1.0 else 0.0

                # decide status by threshold
                threshold = getattr(Config, 'DEEPFACE_THRESHOLD', 0.40)
                status = 'unknown'
                if student_id is not None and distance < threshold:
                    status = 'matched'
                else:
                    status = 'unknown'

                entry = {
                    'student_id': int(student_id) if student_id is not None else None,
                    'student_name': student_name,
                    'confidence': confidence,
                    'bbox': [int(x), int(y), int(w), int(h)],
                    'status': status
                }
                results.append(entry)
                face_entries_for_annot.append(entry)
        else:
            # no matches found => try to detect faces and annotate them as UNKNOWN
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            rects = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(80,80))
            for (x,y,w,h) in rects:
                entry = {
                    'student_id': None,
                    'student_name': 'UNKNOWN',
                    'confidence': 0.0,
                    'bbox': [int(x), int(y), int(w), int(h)],
                    'status': 'unknown'
                }
                results.append(entry)
                face_entries_for_annot.append(entry)

        # annotate copy of frame
        annotated = frame.copy()
        annotated = _annotate_frame(annotated, face_entries_for_annot)

        # encode annotated image to base64 data URL
        try:
            _, enc = cv2.imencode('.jpg', annotated)
            b64 = base64.b64encode(enc.tobytes()).decode('utf-8')
            annotated_base64 = f"data:image/jpeg;base64,{b64}"
        except Exception:
            annotated_base64 = None

        return {
            'success': True,
            'results': results,
            'annotated_base64': annotated_base64
        }

    except Exception as e:
        current_app.logger.exception("recognize_face_from_image error")
        return {'success': False, 'message': str(e)}
