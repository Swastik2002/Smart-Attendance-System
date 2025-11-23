# backend/routes/student_routes.py
from flask import Blueprint, request, jsonify, current_app
from models import Student, Enrollment, Subject, Attendance
from db import db
from datetime import date
from sqlalchemy import func, distinct, and_, desc

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/attendance', methods=['GET'])
def get_student_attendance():
    """
    Query params:
      - student_id (required)
    Returns JSON:
      { success: True,
        data: [
          {
            subject_id,
            subject_name,
            present_count,
            total_classes,
            dates: [ { date: 'YYYY-MM-DD', status: 'Present'|'Absent' } ... ]
          }, ...
        ]
      }
    """
    try:
        student_id = request.args.get('student_id')
        if not student_id:
            return jsonify({'success': False, 'message': 'student_id is required'}), 400

        # find all subjects student is enrolled in
        enrollments = Enrollment.query.filter_by(student_id=student_id).all()
        subject_ids = [e.subject_id for e in enrollments]
        if not subject_ids:
            return jsonify({'success': True, 'data': []})

        subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all()
        out = []

        for subj in subjects:
            subject_id = subj.id

            # all distinct class dates for this subject (classes held) - from Attendance table
            date_rows = db.session.query(distinct(Attendance.date)).filter_by(subject_id=subject_id).order_by(desc(Attendance.date)).all()
            # produce list of dates (as date objects)
            class_dates = [r[0] for r in date_rows]  # each r is tuple (date,)

            total_classes = len(class_dates)

            # fetch student's attendance records for that subject for those dates
            att_rows = Attendance.query.filter_by(student_id=student_id, subject_id=subject_id).all()
            # map date -> status for quick lookup (pick latest if multiple)
            att_map = {}
            for a in att_rows:
                # normalize status
                status = getattr(a, 'status', '') or ''
                status_norm = 'Present' if status.lower().startswith('p') else 'Absent'
                att_map[getattr(a, 'date')] = status_norm

            # build dates list with Present/Absent (default Absent if no record)
            dates_list = []
            present_count = 0
            # keep ordering newest -> oldest to match UI expectation
            for d in class_dates:
                st = att_map.get(d, 'Absent')
                if st == 'Present':
                    present_count += 1
                dates_list.append({'date': d.strftime('%Y-%m-%d'), 'status': st})

            out.append({
                'subject_id': subject_id,
                'subject_name': getattr(subj, 'name', '') or '',
                'present_count': present_count,
                'total_classes': total_classes,
                'dates': dates_list  # newest -> oldest
            })

        return jsonify({'success': True, 'data': out})
    except Exception as e:
        current_app.logger.exception("get_student_attendance error")
        return jsonify({'success': False, 'message': str(e)}), 500
