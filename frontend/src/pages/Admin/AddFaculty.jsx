import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { addFaculty } from '../../services/apiClient';

function AddFaculty() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    username: '',
    password: ''
  });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const result = await addFaculty(formData);

      if (result.success) {
        setMessage('Faculty added successfully!');
        setFormData({ name: '', email: '', username: '', password: '' });
      } else {
        setMessage(result.message || 'Failed to add faculty');
      }
    } catch (err) {
      setMessage('Error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="header">
        <div className="header-content">
          <h2>Admin Dashboard</h2>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn btn-primary" onClick={() => navigate('/admin/add-student')}>
              Add Student
            </button>
            <button className="btn btn-primary" onClick={() => navigate('/admin/add-subject')}>
              Add Subject
            </button>
            <button className="btn btn-danger" onClick={() => navigate('/')}>
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="container">
        <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
          <h2 style={{ marginBottom: '30px', color: '#2d3748' }}>Add Faculty</h2>

          {message && (
            <div className={`alert ${message.includes('success') ? 'alert-success' : 'alert-error'}`}>
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Name</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="Enter faculty name"
              />
            </div>

            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="Enter email"
              />
            </div>

            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                required
                placeholder="Enter username"
              />
            </div>

            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                placeholder="Enter password"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={loading}
            >
              {loading ? 'Adding Faculty...' : 'Add Faculty'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default AddFaculty;
