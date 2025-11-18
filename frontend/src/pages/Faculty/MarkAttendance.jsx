import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import StudentList from '../../components/StudentList';
import ImageCapture from '../../components/ImageCapture';
import { getSubjects, getStudents, markAttendance, markAttendanceFromFace } from '../../services/apiClient';

function MarkAttendance() {
  const navigate = useNavigate();
  const facultyName = localStorage.getItem('facultyName');

  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [students, setStudents] = useState([]);
  const [message, setMessage] = useState('');
  const [showFaceRecognition, setShowFaceRecognition] = useState(false);

  useEffect(() => {
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    const result = await getSubjects();
    if (result.success) {
      setSubjects(result.data);
    }
  };

  const handleSubjectChange = async (e) => {
    const subjectId = e.target.value;
    setSelectedSubject(subjectId);

    if (subjectId) {
      const result = await getStudents(subjectId);
      if (result.success) {
        setStudents(result.data);
      }
    } else {
      setStudents([]);
    }
  };

  const handleMarkAttendance = async (studentId, status) => {
    const result = await markAttendance({
      student_id: studentId,
      subject_id: selectedSubject,
      status
    });

    if (result.success) {
      setMessage(`Attendance marked: ${status}`);
      setTimeout(() => setMessage(''), 3000);
    }
  };

  const handleFaceRecognition = async (images) => {
    if (!selectedSubject) {
      setMessage('Please select a subject first');
      return;
    }

    setMessage('Processing face recognition...');

    const formData = new FormData();
    formData.append('image', images[0]);
    formData.append('subject_id', selectedSubject);

    const result = await markAttendanceFromFace(formData);

    if (result.success) {
      setMessage(`Attendance marked for: ${result.data.student_name} (Confidence: ${result.data.confidence}%)`);
      setShowFaceRecognition(false);
      handleSubjectChange({ target: { value: selectedSubject } });
    } else {
      setMessage(result.message || 'Face not recognized');
    }
  };

  return (
    <div>
      <div className="header">
        <div className="header-content">
          <h2>Faculty Dashboard - {facultyName}</h2>
          <button className="btn btn-danger" onClick={() => navigate('/')}>
            Logout
          </button>
        </div>
      </div>

      <div className="container">
        <div className="card">
          <h2 style={{ marginBottom: '30px', color: '#2d3748' }}>Mark Attendance</h2>

          {message && (
            <div className={`alert ${message.includes('marked') ? 'alert-success' : 'alert-error'}`}>
              {message}
            </div>
          )}

          <div className="form-group">
            <label>Select Subject</label>
            <select
              value={selectedSubject}
              onChange={handleSubjectChange}
              style={{ padding: '12px', borderRadius: '6px', border: '2px solid #e2e8f0', width: '100%' }}
            >
              <option value="">-- Select Subject --</option>
              {subjects.map((subject) => (
                <option key={subject.id} value={subject.id}>
                  {subject.name} ({subject.code})
                </option>
              ))}
            </select>
          </div>

          {selectedSubject && (
            <div style={{ marginTop: '20px' }}>
              <button
                className="btn btn-primary"
                onClick={() => setShowFaceRecognition(!showFaceRecognition)}
                style={{ marginBottom: '20px' }}
              >
                {showFaceRecognition ? 'Hide' : 'Show'} Face Recognition
              </button>

              {showFaceRecognition && (
                <div className="card" style={{ background: '#f7fafc' }}>
                  <h3 style={{ marginBottom: '15px' }}>Face Recognition Attendance</h3>
                  <ImageCapture onCapture={handleFaceRecognition} multiple={false} />
                </div>
              )}
            </div>
          )}
        </div>

        {students.length > 0 && (
          <StudentList students={students} onMarkAttendance={handleMarkAttendance} />
        )}
      </div>
    </div>
  );
}

export default MarkAttendance;
