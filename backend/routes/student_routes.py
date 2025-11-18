from flask import Blueprint, request, jsonify
from models import Student, Attendance, Subject
from db import db
from sqlalchemy import func

student_bp = Blueprint('student', __name__)

@student_bp.route('/attendance', methods=['GET'])
def get_student_attendance():
    try:
        student_id = request.args.get('student_id')

        if not student_id:
            return jsonify({
                'success': False,
                'message': 'Student ID is required'
            }), 400

        attendance_query = db.session.query(
            Subject.id.label('subject_id'),
            Subject.name.label('subject_name'),
            func.count(Attendance.id).label('total_classes'),
            func.sum(db.case((Attendance.status == 'Present', 1), else_=0)).label('present_count')
        ).join(
            Attendance, Attendance.subject_id == Subject.id
        ).filter(
            Attendance.student_id == student_id
        ).group_by(
            Subject.id, Subject.name
        ).all()

        attendance_data = [{
            'subject_id': row.subject_id,
            'subject_name': row.subject_name,
            'total_classes': row.total_classes or 0,
            'present_count': row.present_count or 0
        } for row in attendance_query]

        return jsonify({
            'success': True,
            'data': attendance_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
