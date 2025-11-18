import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getStudentAttendance } from '../../services/apiClient';

function StudentDashboard() {
  const navigate = useNavigate();
  const studentName = localStorage.getItem('studentName');
  const studentId = localStorage.getItem('studentId');

  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAttendance();
  }, []);

  const loadAttendance = async () => {
    setLoading(true);
    const result = await getStudentAttendance(studentId);
    if (result.success) {
      setAttendance(result.data);
    }
    setLoading(false);
  };

  const calculatePercentage = (present, total) => {
    if (total === 0) return 0;
    return ((present / total) * 100).toFixed(2);
  };

  return (
    <div>
      <div className="header">
        <div className="header-content">
          <h2>Student Dashboard - {studentName}</h2>
          <button className="btn btn-danger" onClick={() => navigate('/')}>
            Logout
          </button>
        </div>
      </div>

      <div className="container">
        <h2 style={{ marginBottom: '30px', color: 'white', textAlign: 'center' }}>
          My Attendance
        </h2>

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
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default StudentDashboard;
