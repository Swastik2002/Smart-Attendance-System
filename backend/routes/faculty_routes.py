# backend/routes/faculty_routes.py
from flask import Blueprint, request, jsonify, url_for, current_app, make_response
from models import Subject, Student, Enrollment, Attendance
from db import db
from services.face_service import recognize_face_from_image
from datetime import datetime, date
import traceback
import io
import csv

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@faculty_bp.route('/subjects', methods=['GET'])
def get_subjects():
    try:
        subjects = Subject.query.all()
        subjects_data = []
        for subject in subjects:
            subjects_data.append({
                'id': getattr(subject, 'id', None),
                'name': getattr(subject, 'name', None),
                'code': getattr(subject, 'code', None)
            })
        return jsonify({'success': True, 'data': subjects_data})
    except Exception as e:
        current_app.logger.exception("get_subjects error")
        return jsonify({'success': False, 'message': str(e)}), 500

@faculty_bp.route('/students', methods=['GET'])
def get_students():
    try:
        subject_id = request.args.get('subject_id')
        if not subject_id:
            return jsonify({'success': False, 'message': 'Subject ID is required'}), 400

        enrollments = Enrollment.query.filter_by(subject_id=subject_id).all()
        student_ids = [e.student_id for e in enrollments]

        if not student_ids:
            return jsonify({'success': True, 'data': []})

        students = Student.query.filter(Student.id.in_(student_ids)).all()

        students_data = []
        for s in students:
            name = getattr(s, 'name', None) or (getattr(getattr(s, 'user', None), 'name', None))
            roll = getattr(s, 'roll', None) or getattr(s, 'roll_no', None) or ''
            email = getattr(s, 'email', None) or getattr(getattr(s, 'user', None), 'email', None) or ''
            students_data.append({
                'id': getattr(s, 'id', None),
                'name': name or f"Student {getattr(s, 'id', '')}",
                'roll': roll or '',
                'email': email
            })

        return jsonify({'success': True, 'data': students_data})
    except Exception as e:
        current_app.logger.exception("get_students error")
        return jsonify({'success': False, 'message': str(e)}), 500

@attendance_bp.route('/mark', methods=['POST'])
def mark_attendance():
    try:
        data = request.get_json() or {}
        student_id = data.get('student_id')
        subject_id = data.get('subject_id')
        status = data.get('status', 'Present')
        mark_date = data.get('date')
        mark_time = data.get('time')

        if student_id is None or subject_id is None:
            return jsonify({'success': False, 'message': 'student_id and subject_id are required'}), 400

        from services.attendance_service import mark_student_attendance
        result = mark_student_attendance(student_id, subject_id, status, None, mark_date, mark_time)
        return jsonify(result)
    except Exception as e:
        current_app.logger.exception("mark_attendance error")
        return jsonify({'success': False, 'message': str(e)}), 500

@attendance_bp.route('/mark_from_face', methods=['POST'])
def mark_attendance_from_face():
    """
    Accepts multipart/form-data:
      - image (file)
      - subject_id
      - date (optional)
      - time (optional)

    Returns:
      { success: True, results: [ { student_id, student_name, confidence, bbox, status, already_marked } ... ], annotated_base64 }
    """
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image provided'}), 400

        image_file = request.files['image']
        subject_id = request.form.get('subject_id') or request.args.get('subject_id')
        mark_date = request.form.get('date') or request.args.get('date') or None

        try:
            if mark_date:
                parsed_date = datetime.strptime(mark_date, "%Y-%m-%d").date()
            else:
                parsed_date = date.today()
        except Exception:
            parsed_date = date.today()

        if not subject_id:
            return jsonify({'success': False, 'message': 'subject_id is required'}), 400

        recognition_result = recognize_face_from_image(image_file)

        if not recognition_result.get('success'):
            return jsonify({
                'success': False,
                'message': recognition_result.get('message', 'Face recognition failed'),
                'annotated_base64': recognition_result.get('annotated_base64')
            }), 200

        results = recognition_result.get('results', [])

        # For every result, check DB if this student already has attendance for parsed_date
        for r in results:
            sid = r.get('student_id')
            r['already_marked'] = False
            # if matched and we have a student id, look up official name from DB
            if sid is not None:
                try:
                    student = Student.query.get(int(sid))
                    if student:
                        # prefer student.name from DB
                        r['student_name'] = getattr(student, 'name', r.get('student_name') or str(sid))
                    # check existing attendance for parsed_date
                    existing = Attendance.query.filter_by(student_id=sid, subject_id=subject_id, date=parsed_date).first()
                    if existing:
                        r['already_marked'] = True
                except Exception:
                    current_app.logger.exception("error looking up student for id %s", sid)

            # ensure student_name exists for unknown faces
            if not r.get('student_name'):
                r['student_name'] = 'UNKNOWN'

        return jsonify({
            'success': True,
            'results': results,
            'annotated_base64': recognition_result.get('annotated_base64')
        }), 200

    except Exception as e:
        current_app.logger.exception("mark_attendance_from_face error: %s", str(e))
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@faculty_bp.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    try:
        data = request.get_json() or {}
        subject_id = data.get('subject_id')
        mark_date = data.get('date')
        mark_time = data.get('time')
        entries = data.get('entries', [])

        if not subject_id or not mark_date:
            return jsonify({'success': False, 'message': 'subject_id and date are required'}), 400

        from services.attendance_service import mark_student_attendance
        results = []
        for e in entries:
            sid = e.get('student_id')
            status = e.get('status', 'Absent')
            confidence = e.get('confidence')
            res = mark_student_attendance(sid, subject_id, status, confidence, mark_date=mark_date, mark_time=mark_time)
            results.append({'student_id': sid, 'result': res})

        return jsonify({'success': True, 'marked': results, 'marked_count': len(results)})
    except Exception as e:
        current_app.logger.exception("submit_attendance error")
        return jsonify({'success': False, 'message': str(e)}), 500

@faculty_bp.route('/download_attendance', methods=['GET'])
def download_attendance():
    """
    Query params:
      - subject_id (required)
    Response: CSV attachment with columns: Roll, Name, <dates...>, Percentage
    """
    try:
        subject_id = request.args.get('subject_id')
        if not subject_id:
            return jsonify({'success': False, 'message': 'subject_id is required'}), 400

        enrollments = Enrollment.query.filter_by(subject_id=subject_id).all()
        student_ids = [e.student_id for e in enrollments]
        students = Student.query.filter(Student.id.in_(student_ids)).all()

        date_rows = db.session.query(Attendance.date).filter_by(subject_id=subject_id).distinct().order_by(Attendance.date).all()
        dates = [r[0] for r in date_rows]

        headers = ['Student Roll', 'Student Name'] + [d.strftime('%Y-%m-%d') for d in dates] + ['Percentage']

        rows = []
        for s in students:
            row = [getattr(s, 'roll', '') or getattr(s, 'roll_no', ''), getattr(s, 'name', '') or getattr(getattr(s, 'user', None), 'name', '')]
            present_count = 0
            total = len(dates)
            for d in dates:
                att = Attendance.query.filter_by(student_id=s.id, subject_id=subject_id, date=d).first()
                if att and getattr(att, 'status', '').lower().startswith('p'):
                    row.append('P')
                    present_count += 1
                else:
                    row.append('A')
            pct = round((present_count / total) * 100, 2) if total > 0 else 0.0
            row.append(str(pct))
            rows.append(row)

        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(headers)
        for r in rows:
            cw.writerow(r)
        output = si.getvalue()
        si.close()

        response = make_response(output)
        response.headers["Content-Disposition"] = f"attachment; filename=attendance_subject_{subject_id}.csv"
        response.headers["Content-type"] = "text/csv"
        return response

    except Exception as e:
        current_app.logger.exception("download_attendance error")
        return jsonify({'success': False, 'message': str(e)}), 500
