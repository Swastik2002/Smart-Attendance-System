from flask import Blueprint, request, jsonify
from models import Subject, Student, Enrollment, Attendance
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
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@attendance_bp.route('/mark_from_face', methods=['POST'])
def mark_attendance_from_face():
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

        if not recognition_result['success']:
            return jsonify(recognition_result), 404

        student_id = recognition_result['student_id']
        confidence = recognition_result['confidence']

        student = Student.query.get(student_id)

        attendance_result = mark_student_attendance(
            student_id,
            subject_id,
            'Present',
            confidence
        )

        if attendance_result['success']:
            return jsonify({
                'success': True,
                'message': 'Attendance marked using face recognition',
                'data': {
                    'student_id': student_id,
                    'student_name': student.name,
                    'confidence': confidence
                }
            })
        else:
            return jsonify(attendance_result), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
