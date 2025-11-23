# backend/services/face_service.py
import os
import cv2
import numpy as np
import base64
from deepface import DeepFace as df
from flask import current_app
from config import Config

# Attempt to import Student model to resolve names (optional; wrapped to avoid hard crash)
try:
    from models import Student
except Exception:
    Student = None

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


def _iou(rectA, rectB):
    # rect: [x,y,w,h]
    (xA, yA, wA, hA) = rectA
    (xB, yB, wB, hB) = rectB
    x1 = max(xA, xB)
    y1 = max(yA, yB)
    x2 = min(xA + wA, xB + wB)
    y2 = min(yA + hA, yB + hB)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    areaA = wA * hA
    areaB = wB * hB
    union = areaA + areaB - inter
    return inter / union if union > 0 else 0.0


def _merge_overlapping(entries, iou_thresh=0.45):
    """
    Given a list of face entries (each containing bbox, status, confidence),
    merge entries that highly overlap. Preference order when merging:
      1) status 'matched' preferred over 'unknown'
      2) higher confidence preferred
    Returns a new list of merged entries.
    """
    out = []
    used = [False] * len(entries)

    for i, a in enumerate(entries):
        if used[i]:
            continue
        ax = a.get('bbox') or [0, 0, 0, 0]
        best = a.copy()
        used[i] = True
        for j in range(i + 1, len(entries)):
            if used[j]:
                continue
            b = entries[j]
            bx = b.get('bbox') or [0, 0, 0, 0]
            if _iou(ax, bx) > iou_thresh:
                # decide which one to keep/merge
                # if one is matched and other unknown -> keep matched
                if best.get('status') == 'unknown' and b.get('status') == 'matched':
                    best = b.copy()
                elif best.get('status') == 'matched' and b.get('status') == 'unknown':
                    pass
                else:
                    # prefer larger confidence
                    if (b.get('confidence') or 0) > (best.get('confidence') or 0):
                        best = b.copy()
                used[j] = True
        out.append(best)
    return out


def _looks_like_face(frame, bbox):
    """
    Heuristic checks to reduce false-positive detections (e.g., round objects, patterns).
    Returns True if bbox likely contains a face.

    Checks applied:
     - minimum size relative to image
     - aspect ratio within reasonable face bounds (0.6..1.6)
     - eye detector finds at least one eye region inside bbox (optional, used when available)
    """
    try:
        x, y, w, h = map(int, bbox)
    except Exception:
        return False

    h_img, w_img = frame.shape[:2]

    # reject tiny boxes: require minimum area fraction
    area = float(w * h)
    img_area = float(max(1, w_img * h_img))
    if area / img_area < 0.001:  # box smaller than 0.1% of image area -> ignore
        return False

    # reject extremely wide/tall boxes (faces are roughly square-ish)
    ar = (w / max(1.0, h))
    if ar < 0.5 or ar > 1.8:
        return False

    # check bbox stays inside image bounds
    if x < 0 or y < 0 or x + w > w_img or y + h > h_img:
        # clamp case may be ok, but conservatively reject if box outside.
        if x < -5 or y < -5 or x + w > w_img + 5 or y + h > h_img + 5:
            return False

    # eye-check: use a cascade to validate presence of eye-like features
    try:
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
        if eye_cascade.empty():
            # cascade failed to load — skip eye check
            return True
        # crop region with padding
        pad = int(max(4, min(w, h) * 0.15))
        sx = max(0, x - pad)
        sy = max(0, y - pad)
        ex = min(w_img, x + w + pad)
        ey = min(h_img, y + h + pad)
        crop = frame[sy:ey, sx:ex]
        if crop is None or crop.size == 0:
            return False
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        # eyes are small; set minSize relative to crop
        min_e = max(10, int(min(crop.shape[:2]) * 0.08))
        eyes = eye_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=2, minSize=(min_e, min_e))
        # require at least 1 eye detection to be confident it's a face
        if len(eyes) >= 1:
            return True
        else:
            # if eye check fails, still allow if bbox is large (likely face) and confidence high handled separately.
            return False
    except Exception:
        # if any error, be permissive (avoid hard fail)
        return True


def _annotate_frame(frame, face_entries):
    """
    face_entries: list of dicts { bbox: [x,y,w,h], student_name, status }
    status: 'matched' | 'unknown' | 'already_marked'
    Name color rules:
      - matched (green box): label text should be green
      - already_marked (black box): label text should be white
      - unknown (red box): label text red (keeps label visible)
    """
    for ent in face_entries:
        loc = ent.get('bbox', [0, 0, 0, 0])
        name = ent.get('student_name') or ent.get('name') or "UNKNOWN"
        status = ent.get('status', 'unknown')
        try:
            x, y, w, h = map(int, loc)
        except Exception:
            x, y, w, h = 0, 0, 0, 0

        if status == 'unknown':
            box_color = (0, 0, 255)     # red
            font_color = (0, 0, 255)
            thick = 3
        elif status == 'already_marked':
            box_color = (0, 0, 0)       # black
            font_color = (255, 255, 255)  # white text for black box
            thick = 2
        else:
            box_color = (0, 255, 0)     # green
            font_color = (0, 255, 0)    # green text for green box
            thick = 2

        # draw rectangle
        try:
            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, thick)
        except Exception:
            pass

        # prepare label background (solid black rectangle behind text)
        label = str(name)
        try:
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            lx = max(0, x)
            ly = max(0, y - th - 8)
            # draw filled rectangle as label background
            cv2.rectangle(frame, (lx, ly), (lx + tw + 8, ly + th + 6), (0, 0, 0), -1)
            # put text
            cv2.putText(frame, label, (lx + 4, ly + th - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, font_color, 2)
        except Exception:
            # fallback: ignore label drawing if something goes wrong
            pass
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

        # Run DeepFace.find to locate faces and nearest identities
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

        results = []
        face_entries_for_annot = []

        # collect candidate bboxes reported by deepface + best match per bbox
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
                    x, y, w, h = 0, 0, 0, 0

                # best (minimum) distance row for this face
                try:
                    min_row = dataframe.loc[dataframe['distance'].idxmin()]
                    distance = float(min_row['distance'])
                    identity_path = min_row.get('identity', None)
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
                        # expected: known_faces/<student_id>/<imagefile>
                        if len(parts) >= 2 and parts[0].isdigit():
                            student_id = int(parts[0])
                            student_name = str(student_id)  # will attempt DB resolve below
                        else:
                            base = os.path.basename(identity_path)
                            face_name = os.path.splitext(base)[0]
                            student_name = ''.join(filter(lambda x: not x.isdigit(), face_name)).strip() or face_name
                    except Exception:
                        base = os.path.basename(identity_path) if identity_path else "UNKNOWN"
                        face_name = os.path.splitext(base)[0]
                        student_name = ''.join(filter(lambda x: not x.isdigit(), face_name)).strip() or face_name

                confidence = round((1.0 - distance) * 100, 2) if distance <= 1.0 else 0.0

                threshold = getattr(Config, 'DEEPFACE_THRESHOLD', 0.40)
                status = 'unknown'
                if student_id is not None and distance < threshold:
                    status = 'matched'
                else:
                    status = 'unknown'

                candidate_bbox = [int(x), int(y), int(w), int(h)]

                # validate bbox heuristically to reduce false positives
                if not _looks_like_face(frame, candidate_bbox):
                    # if DeepFace matched but bbox fails heuristics, skip adding it
                    current_app.logger.debug("Discarding candidate bbox due to heuristics: %s", candidate_bbox)
                    continue

                entry = {
                    'student_id': int(student_id) if student_id is not None else None,
                    'student_name': student_name,
                    'confidence': confidence,
                    'bbox': candidate_bbox,
                    'status': status
                }
                results.append(entry)
                face_entries_for_annot.append(entry)

        # Haarcascade fallback detection to find additional faces (only add if not overlapping)
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            # tightened parameters: larger minSize, higher minNeighbors to reduce false positives
            rects = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(70, 70))
        except Exception:
            rects = []

        existing_bboxes = [r['bbox'] for r in results if r.get('bbox')]
        for (x, y, w, h) in rects:
            rect = [int(x), int(y), int(w), int(h)]
            # skip if overlaps a deepface bbox strongly
            overlap = False
            for eb in existing_bboxes:
                if _iou(rect, eb) > 0.45:
                    overlap = True
                    break
            if overlap:
                continue

            # apply heuristics to reduce false positives (roadside, round objects)
            if not _looks_like_face(frame, rect):
                current_app.logger.debug("Haar fallback rejected by heuristics: %s", rect)
                continue

            entry = {
                'student_id': None,
                'student_name': 'UNKNOWN',
                'confidence': 0.0,
                'bbox': rect,
                'status': 'unknown'
            }
            results.append(entry)
            face_entries_for_annot.append(entry)

        # Merge/cleanup overlapping detections so we don't annotate duplicates
        merged = _merge_overlapping(results, iou_thresh=0.45)

        # Resolve student_id -> real name from DB if possible (to show nicer labels)
        if Student is not None:
            for r in merged:
                sid = r.get('student_id')
                if sid is not None:
                    try:
                        stud = Student.query.get(int(sid))
                        if stud:
                            r['student_name'] = getattr(stud, 'name', r.get('student_name') or str(sid))
                    except Exception:
                        current_app.logger.debug("Unable to resolve student id to name for ID %s", sid)

        # prepare annotation only for merged entries
        annotated_entries = merged.copy()

        # annotate a copy of frame
        annotated = frame.copy()
        annotated = _annotate_frame(annotated, annotated_entries)

        # encode annotated image to base64
        try:
            _, enc = cv2.imencode('.jpg', annotated)
            b64 = base64.b64encode(enc.tobytes()).decode('utf-8')
            annotated_base64 = f"data:image/jpeg;base64,{b64}"
        except Exception:
            annotated_base64 = None

        # Return merged results (clean, deduped)
        return {
            'success': True,
            'results': merged,
            'annotated_base64': annotated_base64
        }

    except Exception as e:
        current_app.logger.exception("recognize_face_from_image error")
        return {'success': False, 'message': str(e)}
