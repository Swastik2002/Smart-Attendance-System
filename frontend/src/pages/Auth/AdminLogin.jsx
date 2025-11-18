import React from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../../components/LoginForm';
import { adminLogin } from '../../services/authService';

function AdminLogin() {
  const navigate = useNavigate();

  const handleLogin = async (formData) => {
    const result = await adminLogin(formData);
    if (result.success) {
      localStorage.setItem('userType', 'admin');
      navigate('/admin/add-student');
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
        title="Admin Login"
        onSubmit={handleLogin}
        fields={[
          { name: 'email', label: 'Email', type: 'email', placeholder: 'admin@gmail.com' },
          { name: 'password', label: 'Password', type: 'password', placeholder: 'admin123' }
        ]}
      />
    </div>
  );
}

export default AdminLogin;
