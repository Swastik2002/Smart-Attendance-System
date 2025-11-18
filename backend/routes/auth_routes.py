from flask import Blueprint, request, jsonify
from config import Config
from models import Faculty, Student
from db import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if email == Config.ADMIN_EMAIL and password == Config.ADMIN_PASSWORD:
        return jsonify({
            'success': True,
            'message': 'Admin login successful',
            'data': {'role': 'admin'}
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid admin credentials'
        }), 401

@auth_bp.route('/faculty_login', methods=['POST'])
def faculty_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    faculty = Faculty.query.filter_by(username=username, password=password).first()

    if faculty:
        return jsonify({
            'success': True,
            'message': 'Faculty login successful',
            'data': {
                'id': faculty.id,
                'name': faculty.name,
                'email': faculty.email
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid faculty credentials'
        }), 401

@auth_bp.route('/student_login', methods=['POST'])
def student_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    student = Student.query.filter_by(username=username, password=password).first()

    if student:
        return jsonify({
            'success': True,
            'message': 'Student login successful',
            'data': {
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'roll': student.roll
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid student credentials'
        }), 401
