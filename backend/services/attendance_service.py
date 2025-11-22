# backend/services/attendance_service.py
from models import Attendance
from db import db
from datetime import datetime, date
from flask import current_app

def _normalize_date(mark_date):
    if not mark_date:
        return date.today()
    if isinstance(mark_date, date):
        return mark_date
    # assume string 'YYYY-MM-DD'
    try:
        return datetime.strptime(mark_date, "%Y-%m-%d").date()
    except Exception:
        # fallback to today if parsing fails
        current_app.logger.warning("Failed to parse mark_date '%s', using today", mark_date)
        return date.today()

def mark_student_attendance(student_id, subject_id, status, confidence=None, mark_date=None, mark_time=None, marked_by=None):
    """
    Marks attendance for given student on provided date (mark_date) and optional time (mark_time).
    mark_date can be a date object or string 'YYYY-MM-DD'. If not provided, uses today's date.
    """
    try:
        target_date = _normalize_date(mark_date)
        # optional: parse mark_time if needed; we store time as current time or provided string
        if mark_time:
            try:
                # store only hours:minutes if provided 'HH:MM'
                parsed_time = datetime.strptime(mark_time, "%H:%M").time()
            except Exception:
                parsed_time = datetime.now().time()
        else:
            parsed_time = datetime.now().time()

        # check for existing attendance for given date
        existing_attendance = Attendance.query.filter_by(
            student_id=student_id,
            subject_id=subject_id,
            date=target_date
        ).first()

        if existing_attendance:
            return {
                "success": False,
                "message": f"Attendance already marked for {target_date.isoformat()}"
            }

        attendance = Attendance(
            student_id=student_id,
            subject_id=subject_id,
            date=target_date,
            time=parsed_time,
            status=status,
            confidence=confidence
        )

        db.session.add(attendance)
        db.session.commit()

        return {
            "success": True,
            "message": "Attendance marked successfully",
            "id": attendance.id
        }

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("mark_student_attendance error")
        return {
            "success": False,
            "message": str(e)
        }

def mark_bulk_attendance(entries, subject_id, mark_date=None, marked_by=None):
    """
    entries: list of { student_id, status, confidence? }
    mark_date: 'YYYY-MM-DD' string (optional)
    Returns list of Attendance objects saved
    """
    saved = []
    try:
        target_date = _normalize_date(mark_date)
        for e in entries:
            sid = e.get("student_id")
            status = e.get("status", "Absent")
            confidence = e.get("confidence")
            existing = Attendance.query.filter_by(student_id=sid, subject_id=subject_id, date=target_date).first()
            if existing:
                # update existing
                existing.status = status
                existing.confidence = confidence
                db.session.commit()
                saved.append(existing)
                continue

            att = Attendance(
                student_id=sid,
                subject_id=subject_id,
                date=target_date,
                time=datetime.now().time(),
                status=status,
                confidence=confidence,
            )
            db.session.add(att)
            db.session.commit()
            saved.append(att)
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("mark_bulk_attendance error")
        return saved
    return saved
