import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { addSubject } from '../../services/apiClient';

function AddSubject() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    code: ''
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
      const result = await addSubject(formData);

      if (result.success) {
        setMessage('Subject added successfully!');
        setFormData({ name: '', code: '' });
      } else {
        setMessage(result.message || 'Failed to add subject');
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
            <button className="btn btn-primary" onClick={() => navigate('/admin/add-faculty')}>
              Add Faculty
            </button>
            <button className="btn btn-danger" onClick={() => navigate('/')}>
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="container">
        <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
          <h2 style={{ marginBottom: '30px', color: '#2d3748' }}>Add Subject</h2>

          {message && (
            <div className={`alert ${message.includes('success') ? 'alert-success' : 'alert-error'}`}>
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Subject Name</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="Enter subject name"
              />
            </div>

            <div className="form-group">
              <label>Subject Code</label>
              <input
                type="text"
                name="code"
                value={formData.code}
                onChange={handleChange}
                required
                placeholder="Enter subject code"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={loading}
            >
              {loading ? 'Adding Subject...' : 'Add Subject'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default AddSubject;
