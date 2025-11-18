from models import Attendance
from db import db
from datetime import datetime, date

def mark_student_attendance(student_id, subject_id, status, confidence=None):
    try:
        today = date.today()
        current_time = datetime.now().time()

        existing_attendance = Attendance.query.filter_by(
            student_id=student_id,
            subject_id=subject_id,
            date=today
        ).first()

        if existing_attendance:
            return {
                'success': False,
                'message': 'Attendance already marked for today'
            }

        attendance = Attendance(
            student_id=student_id,
            subject_id=subject_id,
            date=today,
            time=current_time,
            status=status,
            confidence=confidence
        )

        db.session.add(attendance)
        db.session.commit()

        return {
            'success': True,
            'message': 'Attendance marked successfully'
        }

    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'message': str(e)
        }
