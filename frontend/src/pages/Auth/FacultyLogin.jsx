import React from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../../components/LoginForm';
import { facultyLogin } from '../../services/authService';

function FacultyLogin() {
  const navigate = useNavigate();

  const handleLogin = async (formData) => {
    const result = await facultyLogin(formData);
    if (result.success) {
      localStorage.setItem('userType', 'faculty');
      localStorage.setItem('facultyId', result.data.id);
      localStorage.setItem('facultyName', result.data.name);
      navigate('/faculty/mark-attendance');
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
        title="Faculty Login"
        onSubmit={handleLogin}
        fields={[
          { name: 'username', label: 'Username', type: 'text', placeholder: 'Enter username' },
          { name: 'password', label: 'Password', type: 'password', placeholder: 'Enter password' }
        ]}
      />
    </div>
  );
}

export default FacultyLogin;
