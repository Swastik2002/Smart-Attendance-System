import os
from werkzeug.utils import secure_filename
from config import Config
from models import Subject, Enrollment
from db import db

def save_student_images(student_id, images):
    """
    Save uploaded FileStorage objects to UPLOAD_FOLDER/<student_id>/
    Returns a list of saved file paths (absolute).
    """
    student_folder = os.path.join(Config.UPLOAD_FOLDER, str(student_id))
    os.makedirs(student_folder, exist_ok=True)

    saved_paths = []
    for i, image in enumerate(images):
        if image and image.filename:
            filename = secure_filename(f"image_{i}_{image.filename}")
            image_path = os.path.join(student_folder, filename)
            image.save(image_path)
            saved_paths.append(image_path)

    return saved_paths

def enroll_student_in_all_subjects(student_id):
    subjects = Subject.query.all()

    for subject in subjects:
        existing_enrollment = Enrollment.query.filter_by(
            student_id=student_id,
            subject_id=subject.id
        ).first()

        if not existing_enrollment:
            enrollment = Enrollment(
                student_id=student_id,
                subject_id=subject.id
            )
            db.session.add(enrollment)

    db.session.commit()
    return True


# import os
# from werkzeug.utils import secure_filename
# from config import Config
# from models import Subject, Enrollment
# from db import db

# def save_student_images(student_id, images):
#     student_folder = os.path.join(Config.UPLOAD_FOLDER, str(student_id))
#     os.makedirs(student_folder, exist_ok=True)

#     for i, image in enumerate(images):
#         if image and image.filename:
#             filename = secure_filename(f"image_{i}_{image.filename}")
#             image_path = os.path.join(student_folder, filename)
#             image.save(image_path)

#     return True

# def enroll_student_in_all_subjects(student_id):
#     subjects = Subject.query.all()

#     for subject in subjects:
#         existing_enrollment = Enrollment.query.filter_by(
#             student_id=student_id,
#             subject_id=subject.id
#         ).first()

#         if not existing_enrollment:
#             enrollment = Enrollment(
#                 student_id=student_id,
#                 subject_id=subject.id
#             )
#             db.session.add(enrollment)

#     db.session.commit()
#     return True
