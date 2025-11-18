import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import Student, Faculty, Subject, Enrollment
from db import db
from services.student_service import save_student_images, enroll_student_in_all_subjects
from services.face_service import train_student_face

admin_bp = Blueprint('admin', __name__)
face_bp = Blueprint('face', __name__)

@admin_bp.route('/student', methods=['POST'])
def add_student():
    try:
        name = request.form.get('name')
        roll = request.form.get('roll')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        images = request.files.getlist('images')

        if not images or len(images) < 2:
            return jsonify({
                'success': False,
                'message': 'At least 2 images are required'
            }), 400

        existing_student = Student.query.filter(
            (Student.roll == roll) | (Student.email == email) | (Student.username == username)
        ).first()

        if existing_student:
            return jsonify({
                'success': False,
                'message': 'Student with same roll, email, or username already exists'
            }), 400

        student = Student(
            name=name,
            roll=roll,
            email=email,
            username=username,
            password=password
        )

        db.session.add(student)
        db.session.commit()

        save_student_images(student.id, images)

        train_student_face(student.id)

        enroll_student_in_all_subjects(student.id)

        return jsonify({
            'success': True,
            'message': 'Student added successfully',
            'data': {'id': student.id}
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/faculty', methods=['POST'])
def add_faculty():
    try:
        data = request.json

        existing_faculty = Faculty.query.filter(
            (Faculty.email == data['email']) | (Faculty.username == data['username'])
        ).first()

        if existing_faculty:
            return jsonify({
                'success': False,
                'message': 'Faculty with same email or username already exists'
            }), 400

        faculty = Faculty(
            name=data['name'],
            email=data['email'],
            username=data['username'],
            password=data['password']
        )

        db.session.add(faculty)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Faculty added successfully',
            'data': {'id': faculty.id}
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@admin_bp.route('/subject', methods=['POST'])
def add_subject():
    try:
        data = request.json

        existing_subject = Subject.query.filter_by(code=data['code']).first()

        if existing_subject:
            return jsonify({
                'success': False,
                'message': 'Subject with same code already exists'
            }), 400

        subject = Subject(
            name=data['name'],
            code=data['code']
        )

        db.session.add(subject)
        db.session.commit()

        students = Student.query.all()
        for student in students:
            enrollment = Enrollment(
                student_id=student.id,
                subject_id=subject.id
            )
            db.session.add(enrollment)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Subject added successfully and all students enrolled',
            'data': {'id': subject.id}
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@face_bp.route('/train', methods=['POST'])
def train_face():
    try:
        data = request.json
        student_id = data.get('student_id')

        if not student_id:
            return jsonify({
                'success': False,
                'message': 'Student ID is required'
            }), 400

        train_student_face(student_id)

        return jsonify({
            'success': True,
            'message': 'Face training completed successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
