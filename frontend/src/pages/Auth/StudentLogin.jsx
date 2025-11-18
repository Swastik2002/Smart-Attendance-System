import React from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../../components/LoginForm';
import { studentLogin } from '../../services/authService';

function StudentLogin() {
  const navigate = useNavigate();

  const handleLogin = async (formData) => {
    const result = await studentLogin(formData);
    if (result.success) {
      localStorage.setItem('userType', 'student');
      localStorage.setItem('studentId', result.data.id);
      localStorage.setItem('studentName', result.data.name);
      navigate('/student/dashboard');
    } else {
      throw new Error(result.message);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <LoginForm
        title="Student Login"
        onSubmit={handleLogin}
        fields={[
          { name: 'username', label: 'Username', type: 'text', placeholder: 'Enter username' },
          { name: 'password', label: 'Password', type: 'password', placeholder: 'Enter password' }
        ]}
      />
    </div>
  );
}

export default StudentLogin;
