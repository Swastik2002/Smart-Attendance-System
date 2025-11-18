from flask import Blueprint, request, jsonify, url_for, current_app
from models import Subject, Student, Enrollment
from db import db
from services.attendance_service import mark_student_attendance
from services.face_service import recognize_face_from_image
from datetime import datetime, date

faculty_bp = Blueprint('faculty', __name__)
attendance_bp = Blueprint('attendance', __name__)

@faculty_bp.route('/subjects', methods=['GET'])
def get_subjects():
    try:
        subjects = Subject.query.all()

        subjects_data = [{
            'id': subject.id,
            'name': subject.name,
            'code': subject.code
        } for subject in subjects]

        return jsonify({
            'success': True,
            'data': subjects_data
        })

    except Exception as e:
        current_app.logger.exception("get_subjects error")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@faculty_bp.route('/students', methods=['GET'])
def get_students():
    try:
        subject_id = request.args.get('subject_id')

        if not subject_id:
            return jsonify({
                'success': False,
                'message': 'Subject ID is required'
            }), 400

        enrollments = Enrollment.query.filter_by(subject_id=subject_id).all()
        student_ids = [e.student_id for e in enrollments]

        students = Student.query.filter(Student.id.in_(student_ids)).all()

        students_data = [{
            'id': student.id,
            'name': student.name,
            'roll': student.roll,
            'email': student.email
        } for student in students]

        return jsonify({
            'success': True,
            'data': students_data
        })

    except Exception as e:
        current_app.logger.exception("get_students error")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@attendance_bp.route('/mark', methods=['POST'])
def mark_attendance():
    try:
        data = request.json
        student_id = data.get('student_id')
        subject_id = data.get('subject_id')
        status = data.get('status')

        result = mark_student_attendance(student_id, subject_id, status)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        current_app.logger.exception("mark_attendance error")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@attendance_bp.route('/mark_from_face', methods=['POST'])
def mark_attendance_from_face():
    """
    Expects multipart/form-data with:
      - image (file)
      - subject_id (form field)
    Returns annotated image URL (annotated_url) and attendance result if recognized.
    """
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No image provided'
            }), 400

        image_file = request.files['image']
        subject_id = request.form.get('subject_id')

        if not subject_id:
            return jsonify({
                'success': False,
                'message': 'Subject ID is required'
            }), 400

        recognition_result = recognize_face_from_image(image_file)

        # Build annotated_url if present
        annotated_url = None
        if recognition_result.get('annotated_image_path'):
            try:
                # temp_file route defined in app.py as 'temp_file'
                annotated_url = url_for('temp_file', filename=recognition_result['annotated_image_path'], _external=True)
            except Exception:
                # fallback: construct using request.host_url and path
                annotated_url = None

        if not recognition_result.get('success'):
            # return the annotated_url for debugging if available, and best_distance if present
            return jsonify({
                'success': False,
                'message': recognition_result.get('message', 'Face not recognized'),
                'best_distance': recognition_result.get('best_distance'),
                'annotated_url': annotated_url
            }), 200

        student_id = recognition_result.get('student_id')
        confidence = recognition_result.get('confidence')
        student_name = recognition_result.get('student_name')

        if student_id is None:
            # recognized but unable to parse ID — still return annotated preview
            return jsonify({
                'success': False,
                'message': 'Face matched but student id could not be determined',
                'annotated_url': annotated_url
            }), 200

        # fetch student for human-readable name (optional)
        student = Student.query.get(student_id)

        attendance_result = mark_student_attendance(
            int(student_id),
            int(subject_id),
            'Present',
            confidence
        )

        if attendance_result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Attendance marked using face recognition',
                'data': {
                    'student_id': student_id,
                    'student_name': student.name if student else student_name,
                    'confidence': confidence,
                    'attendance': attendance_result,
                    'annotated_url': annotated_url
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': attendance_result.get('message', 'Failed to mark attendance'),
                'annotated_url': annotated_url
            }), 400

    except Exception as e:
        current_app.logger.exception("mark_attendance_from_face error")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
