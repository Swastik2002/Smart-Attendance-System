// frontend/src/pages/Student/StudentDashboard.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getStudentAttendance } from '../../services/apiClient'; // ensure this calls /student/attendance?student_id=...
import './StudentDashboard.css'; // small CSS file below

function StudentDashboard() {
  const navigate = useNavigate();
  const studentName = localStorage.getItem('studentName') || 'Student';
  const studentId = localStorage.getItem('studentId');

  const [attendance, setAttendance] = useState([]); // data from backend
  const [loading, setLoading] = useState(true);

  // calendar UI state
  const [calendarOpen, setCalendarOpen] = useState(false);
  const [activeSubject, setActiveSubject] = useState(null); // subject object with dates
  const [viewYear, setViewYear] = useState(null);
  const [viewMonth, setViewMonth] = useState(null); // 0..11
  const [selectedDateDetails, setSelectedDateDetails] = useState(null);

  useEffect(() => {
    loadAttendance();
    // eslint-disable-next-line
  }, []);

  const loadAttendance = async () => {
    setLoading(true);
    try {
      const result = await getStudentAttendance(studentId);
      if (result.success) {
        // result.data is an array of subjects
        setAttendance(result.data || []);
      } else {
        setAttendance([]);
      }
    } catch (err) {
      setAttendance([]);
    }
    setLoading(false);
  };

  // compute percentage helper (safe)
  const calculatePercentage = (present, total) => {
    if (!total || total === 0) return '0.00';
    return ((present / total) * 100).toFixed(2);
  };

  // open calendar for subject (subject is {subject_id, subject_name, dates: [{date,status}]})
  const openCalendar = (subject) => {
    setActiveSubject(subject);
    setCalendarOpen(true);
    setSelectedDateDetails(null);

    // default view month/year to newest class date if available, else today
    if (subject && subject.dates && subject.dates.length > 0) {
      const newest = subject.dates[0]; // backend returns newest-first
      const dt = new Date(newest.date + 'T00:00:00');
      setViewYear(dt.getFullYear());
      setViewMonth(dt.getMonth());
    } else {
      const now = new Date();
      setViewYear(now.getFullYear());
      setViewMonth(now.getMonth());
    }
  };

  const closeCalendar = () => {
    setCalendarOpen(false);
    setActiveSubject(null);
    setSelectedDateDetails(null);
  };

  // returns map of YYYY-MM-DD -> status for the active subject
  const buildDateMap = () => {
    const map = {};
    if (!activeSubject || !activeSubject.dates) return map;
    for (const d of activeSubject.dates) {
      map[d.date] = d.status; // status 'Present'/'Absent'
    }
    return map;
  };

  const dateMap = buildDateMap();

  // calendar navigation
  const prevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear(viewYear - 1);
    } else {
      setViewMonth(viewMonth - 1);
    }
  };
  const nextMonth = () => {
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear(viewYear + 1);
    } else {
      setViewMonth(viewMonth + 1);
    }
  };

  // create a month grid for viewYear/viewMonth
  const monthGrid = () => {
    if (viewYear == null || viewMonth == null) return [];
    const firstDay = new Date(viewYear, viewMonth, 1);
    const startDow = firstDay.getDay(); // 0..6 Sun..Sat
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
    const weeks = [];
    let week = new Array(7).fill(null);
    let dayCounter = 1;

    // fill first week
    for (let i = startDow; i < 7; i++) {
      week[i] = new Date(viewYear, viewMonth, dayCounter++);
    }
    weeks.push(week);

    while (dayCounter <= daysInMonth) {
      week = new Array(7).fill(null);
      for (let i = 0; i < 7 && dayCounter <= daysInMonth; i++) {
        week[i] = new Date(viewYear, viewMonth, dayCounter++);
      }
      weeks.push(week);
    }
    return weeks;
  };

  const onClickDate = (dt) => {
    if (!dt) return;
    const key = dt.toISOString().slice(0, 10);
    const status = dateMap[key] || 'No class';
    setSelectedDateDetails({ date: key, status });
  };

  return (
    <div>
      <div className="header">
        <div className="header-content">
          <h2>Student Dashboard - {studentName}</h2>
          <button className="btn btn-danger" onClick={() => navigate('/')}>Logout</button>
        </div>
      </div>

      <div className="container">
        <h2 style={{ marginBottom: '20px', color: '#fff', textAlign: 'center' }}>My Attendance</h2>

        {loading ? (
          <div className="card" style={{ textAlign: 'center' }}>
            <p>Loading attendance data...</p>
          </div>
        ) : attendance.length === 0 ? (
          <div className="card" style={{ textAlign: 'center' }}>
            <p>No attendance records found</p>
          </div>
        ) : (
          <div className="stats-grid">
            {attendance.map((record) => (
              <div key={record.subject_id} className="stat-card">
                <h3>{record.subject_name}</h3>
                <div className="stat-value">
                  {calculatePercentage(record.present_count, record.total_classes)}%
                </div>
                <p style={{ marginTop: '10px', opacity: 0.9 }}>
                  {record.present_count} / {record.total_classes} classes attended
                </p>
                <button className="btn btn-primary" onClick={() => openCalendar(record)}>View Calendar</button>
              </div>
            ))}
          </div>
        )}

        {/* Calendar modal */}
        {calendarOpen && activeSubject && (
          <div className="calendar-overlay" onClick={closeCalendar}>
            <div className="calendar-modal" onClick={(e) => e.stopPropagation()}>
              <div className="calendar-header">
                <h3>{activeSubject.subject_name} — Class dates</h3>
                <button className="btn" onClick={closeCalendar}>Close</button>
              </div>

              <div className="calendar-body">
                <div className="cal-panel">
                  <div className="cal-nav">
                    <button onClick={prevMonth} className="nav-btn">&lt;</button>
                    <div className="cal-title">{new Date(viewYear, viewMonth, 1).toLocaleString(undefined, { month: 'long', year: 'numeric' })}</div>
                    <button onClick={nextMonth} className="nav-btn">&gt;</button>
                  </div>

                  <table className="cal-table">
                    <thead>
                      <tr>
                        <th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th>
                      </tr>
                    </thead>
                    <tbody>
                      {monthGrid().map((week, wi) => (
                        <tr key={wi}>
                          {week.map((d, di) => {
                            if (!d) return <td key={di} className="cal-cell empty" />;
                            const key = d.toISOString().slice(0,10);
                            const status = dateMap[key]; // present/absent/undefined
                            let cls = 'cal-cell';
                            if (status === 'Present') cls += ' present';
                            else if (status === 'Absent') cls += ' absent';
                            return (
                              <td key={di} className={cls} onClick={() => onClickDate(d)}>
                                <div className="cal-day">{d.getDate()}</div>
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="cal-detail">
                  <h4>Details</h4>
                  {selectedDateDetails ? (
                    <div>
                      <p><strong>{selectedDateDetails.date}</strong></p>
                      <p>Status: <span style={{ color: selectedDateDetails.status === 'Present' ? 'green' : (selectedDateDetails.status === 'Absent' ? 'red' : '#444') }}>{selectedDateDetails.status}</span></p>
                      <div style={{ marginTop: 10 }}>
                        <button className="btn btn-primary" onClick={loadAttendance}>Refresh</button>
                      </div>
                    </div>
                  ) : (
                    <p>Select a highlighted date to see details</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default StudentDashboard;
