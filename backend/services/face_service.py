# backend/services/face_service.py
import os
import cv2
import numpy as np
from deepface import DeepFace as df
from flask import current_app
from config import Config

# DeepFace DB folder: known faces stored here, one subfolder per student id
KNOWN_FACES_DIR = os.path.join(Config.UPLOAD_FOLDER, "known_faces")
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

def _ensure_student_folder(student_id):
    student_folder = os.path.join(KNOWN_FACES_DIR, str(student_id))
    os.makedirs(student_folder, exist_ok=True)
    return student_folder

def copy_student_to_known(student_id):
    """
    Copy images from Config.UPLOAD_FOLDER/<student_id>/ -> KNOWN_FACES_DIR/<student_id>/
    Returns dict summary: {'copied': n, 'errors': [...]}
    """
    summary = {'copied': 0, 'errors': []}
    src_folder = os.path.join(Config.UPLOAD_FOLDER, str(student_id))
    if not os.path.exists(src_folder) or not os.path.isdir(src_folder):
        summary['errors'].append(f"Source folder not found: {src_folder}")
        return summary

    dest_folder = _ensure_student_folder(student_id)

    try:
        # get a baseline of existing files to avoid re-copying duplicates
        existing = set(os.listdir(dest_folder))
        for fname in sorted(os.listdir(src_folder)):
            src_path = os.path.join(src_folder, fname)
            if not os.path.isfile(src_path):
                continue
            # deterministic destination name (studentid_index.ext)
            base_ext = os.path.splitext(fname)[1] or ".jpg"
            next_index = len([f for f in os.listdir(dest_folder) if os.path.isfile(os.path.join(dest_folder, f))]) + 1
            dest_name = f"{student_id}_{next_index}{base_ext}"
            dest_path = os.path.join(dest_folder, dest_name)
            if os.path.exists(dest_path):
                # skip if exact dest exists
                continue
            try:
                with open(src_path, "rb") as fr, open(dest_path, "wb") as fw:
                    fw.write(fr.read())
                summary['copied'] += 1
            except Exception as e:
                # fallback using cv2 (in case of permissions / weird encodings)
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

# Legacy-style training: copy images for single student and return result
def train_student_face(student_id):
    """
    Copy that student's uploads into KNOWN_FACES_DIR/<student_id>.
    Returns summary dict.
    """
    try:
        res = copy_student_to_known(student_id)
        # include a quick sanity check: dest folder must now have files
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

def _annotate_frame(frame, face_bboxes, recognized_names):
    duplicate_names = set()
    seen = set()
    for loc, name in zip(face_bboxes, recognized_names):
        x, y, w, h = map(int, loc)
        if name in seen:
            duplicate_names.add(name)
        seen.add(name)

    for loc, name in zip(face_bboxes, recognized_names):
        x, y, w, h = map(int, loc)
        if name == "UNKNOWN":
            box_color = (0, 0, 255)
            thick = 3
            font_color = (0, 0, 255)
        else:
            if name in duplicate_names:
                box_color = (0, 0, 0)
                font_color = (0, 255, 0)
            else:
                box_color = (0, 255, 0)
                font_color = (0, 0, 255)
            thick = 2

        cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, thick)
        cv2.putText(frame, str(name), (x, max(0, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, font_color, 2)

    return frame

def recognize_face_from_image(image_file):
    try:
        frame = _frame_from_file_storage(image_file)
        if frame is None:
            return {'success': False, 'message': 'Invalid image uploaded'}

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

        if not matches:
            return {'success': False, 'message': 'No matches found'}

        face_bboxes = []
        recognized_names = []
        best_student_id = None
        best_distance = float('inf')

        for dataframe in matches:
            if dataframe is None or dataframe.empty:
                continue

            x = int(dataframe['source_x'].iloc[0])
            y = int(dataframe['source_y'].iloc[0])
            w = int(dataframe['source_w'].iloc[0])
            h = int(dataframe['source_h'].iloc[0])
            face_bboxes.append([x, y, w, h])

            min_row = dataframe.loc[dataframe['distance'].idxmin()]
            distance = float(min_row['distance'])
            identity_path = min_row['identity']

            student_id = None
            student_name = "UNKNOWN"
            try:
                rel = os.path.relpath(identity_path, KNOWN_FACES_DIR)
                parts = rel.split(os.sep)
                if len(parts) >= 2 and parts[0].isdigit():
                    student_id = int(parts[0])
                    student_name = str(student_id)
                else:
                    base = os.path.basename(identity_path)
                    face_name = os.path.splitext(base)[0]
                    student_name = ''.join(filter(lambda x: not x.isdigit(), face_name)).strip() or face_name
            except Exception:
                base = os.path.basename(identity_path)
                face_name = os.path.splitext(base)[0]
                student_name = ''.join(filter(lambda x: not x.isdigit(), face_name)).strip() or face_name

            recognized_names.append(student_name)

            if distance < best_distance:
                best_distance = distance
                best_student_id = student_id

        threshold = getattr(Config, 'DEEPFACE_THRESHOLD', 0.40)

        if best_distance < threshold:
            confidence = round((1.0 - best_distance) * 100, 2)
            annotated = _annotate_frame(frame.copy(), face_bboxes, recognized_names)
            out_name = f"recognized_{int(np.random.random()*1e9)}.jpg"
            out_path = os.path.join(Config.TEMP_FOLDER, out_name)
            os.makedirs(Config.TEMP_FOLDER, exist_ok=True)
            cv2.imwrite(out_path, annotated)

            return {
                'success': True,
                'student_id': int(best_student_id) if best_student_id is not None else None,
                'student_name': recognized_names[0] if recognized_names else None,
                'confidence': confidence,
                'annotated_image_path': out_name
            }
        else:
            return {'success': False, 'message': 'Face not recognized', 'best_distance': best_distance}

    except Exception as e:
        current_app.logger.exception("recognize_face_from_image error")
        return {'success': False, 'message': str(e)}

def train_all_students():
    """
    Bulk copy: copy each folder under UPLOAD_FOLDER -> KNOWN_FACES_DIR/<student_id>
    Returns summary dict.
    """
    summary = {'processed_students': 0, 'copied_images': 0, 'errors': []}
    src_root = Config.UPLOAD_FOLDER
    if not os.path.exists(src_root):
        return summary

    for entry in sorted(os.listdir(src_root)):
        src_folder = os.path.join(src_root, entry)
        # skip if this is the known_faces or models directory itself
        if not os.path.isdir(src_folder):
            continue
        if entry == "known_faces":
            continue
        try:
            res = copy_student_to_known(entry)
            summary['processed_students'] += 1
            summary['copied_images'] += res.get('copied', 0)
            if res.get('errors'):
                summary['errors'].extend(res['errors'])
        except Exception as e:
            summary['errors'].append(f"{entry}: {str(e)}")

    return summary




# services/face_service.py
# import os
# import io
# import json
# import cv2
# import numpy as np
# from flask import current_app
# from utils.encoding_utils import get_model_dir, model_path, labels_path, save_label_map, load_label_map

# CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

# def ensure_dirs():
#     upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
#     os.makedirs(upload_folder, exist_ok=True)
#     os.makedirs(get_model_dir(), exist_ok=True)

# def _read_image_from_file(path):
#     # Use imdecode to support unicode paths on Windows
#     nparr = np.fromfile(path, dtype=np.uint8)
#     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#     return img

# def collect_dataset(img_size=(200,200)):
#     """
#     Scan UPLOAD_FOLDER and collect images per student.
#     Returns (faces_list, labels_list, label_map)
#     label_map: student_id(str) -> label_index(int)
#     """
#     ensure_dirs()
#     upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
#     face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

#     faces = []
#     labels = []
#     label_map = {}
#     cur_label = 0

#     # each student's images are expected in upload_folder/<student_id>/
#     for entry in sorted(os.listdir(upload_folder)):
#         student_folder = os.path.join(upload_folder, entry)
#         if not os.path.isdir(student_folder):
#             continue
#         student_id = str(entry)
#         # skip models dir if located under upload folder
#         if student_id == "models":
#             continue
#         # gather images
#         found_any = False
#         for fname in os.listdir(student_folder):
#             fp = os.path.join(student_folder, fname)
#             try:
#                 img = _read_image_from_file(fp)
#                 if img is None:
#                     continue
#                 gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#                 # detect faces and pick the largest face (if any); else use whole image
#                 rects = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(80,80))
#                 if len(rects) > 0:
#                     # choose largest rectangle
#                     rects = sorted(rects, key=lambda r: r[2]*r[3], reverse=True)
#                     x,y,w,h = rects[0]
#                     face = gray[y:y+h, x:x+w]
#                 else:
#                     # fallback: use center crop or full gray
#                     face = gray
#                 face_resized = cv2.resize(face, img_size)
#                 faces.append(face_resized)
#                 labels.append(cur_label)
#                 found_any = True
#             except Exception:
#                 # ignore corrupted images
#                 continue
#         if found_any:
#             label_map[student_id] = cur_label
#             cur_label += 1

#     return faces, labels, label_map

# def train_all_students(img_size=(200,200)):
#     """
#     Train LBPH model from all students present in UPLOAD_FOLDER and save model + labels.json
#     """
#     ensure_dirs()
#     faces, labels, label_map = collect_dataset(img_size=img_size)
#     if not faces:
#         raise RuntimeError("No training images found. Ensure images are saved in UPLOAD_FOLDER/<student_id>/")

#     # create LBPH recognizer
#     recognizer = cv2.face.LBPHFaceRecognizer_create()
#     recognizer.train(faces, np.array(labels, dtype=np.int32))

#     # save model and label map
#     mp = model_path()
#     recognizer.save(mp)
#     save_label_map(label_map)
#     return {"model_path": mp, "labels_count": len(label_map)}

# def _load_recognizer():
#     mp = model_path()
#     lp = labels_path()
#     if not os.path.exists(mp) or not os.path.exists(lp):
#         return None, None
#     recognizer = cv2.face.LBPHFaceRecognizer_create()
#     recognizer.read(mp)
#     label_map = load_label_map()  # student_id (str) -> label
#     # invert mapping: label -> student_id
#     inv_map = {int(v): str(k) for k,v in label_map.items()}
#     return recognizer, inv_map

# def _image_bytes_to_cv2(img_bytes):
#     nparr = np.frombuffer(img_bytes, np.uint8)
#     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#     return img

# def recognize_face_from_image(image_file, threshold=70):
#     """
#     image_file: werkzeug FileStorage or a file-like object with .read()
#     threshold: LBPH confidence threshold (lower means stricter). Typical: 50-80.
#     Returns: dict: {'success':bool, 'student_id':int or None, 'confidence':float, 'message':...}
#     """
#     try:
#         ensure_dirs()
#         recognizer, inv_map = _load_recognizer()
#         if recognizer is None:
#             return {'success': False, 'message': 'Model not trained. Run training first.'}

#         # read image bytes
#         image_bytes = image_file.read()
#         img = _image_bytes_to_cv2(image_bytes)
#         if img is None:
#             return {'success': False, 'message': 'Invalid image'}

#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
#         rects = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(80,80))

#         if len(rects) == 0:
#             return {'success': False, 'message': 'No face detected'}

#         # choose the largest face (or you can loop over all)
#         rects = sorted(rects, key=lambda r: r[2]*r[3], reverse=True)
#         x,y,w,h = rects[0]
#         face = gray[y:y+h, x:x+w]
#         face_resized = cv2.resize(face, (200,200))

#         label, conf = recognizer.predict(face_resized)
#         # conf: smaller = better match. Decide accept if conf <= threshold
#         if conf <= threshold and label in inv_map:
#             student_id = int(inv_map[label])
#             # convert to confidence percentage: smaller conf -> higher percentage
#             confidence_pct = max(0.0, min(100.0, (100.0 - conf)))
#             return {'success': True, 'student_id': student_id, 'confidence': round(confidence_pct, 2)}
#         else:
#             return {'success': False, 'message': 'Face not recognized', 'confidence': round(100.0 - conf, 2)}
#     except Exception as e:
#         return {'success': False, 'message': str(e)}
