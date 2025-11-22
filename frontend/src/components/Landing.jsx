import React from 'react';
import { useNavigate } from 'react-router-dom';

function Landing() {
  const navigate = useNavigate();

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div className="card" style={{ maxWidth: '500px', width: '100%', textAlign: 'center' }}>
        <h1 style={{
          fontSize: '32px',
          marginBottom: '10px',
          color: '#2d3748',
          fontWeight: 'bold'
        }}>
          Smart Attendance System
        </h1>
        <p style={{
          color: '#718096',
          marginBottom: '40px',
          fontSize: '16px'
        }}>
          AI-Powered Face Recognition Attendance
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/admin/login')}
            style={{ width: '100%', fontSize: '18px' }}
          >
            Admin Login
          </button>

          <button
            className="btn btn-primary"
            onClick={() => navigate('/faculty/login')}
            style={{ width: '100%', fontSize: '18px' }}
          >
            Faculty Login
          </button>

          <button
            className="btn btn-primary"
            onClick={() => navigate('/student/login')}
            style={{ width: '100%', fontSize: '18px' }}
          >
            Student Login
          </button>
        </div>
      </div>
    </div>
  );
}

export default Landing;
