import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ImageCapture from '../../components/ImageCapture';
import { addStudent } from '../../services/apiClient';

function AddStudent() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    roll: '',
    email: '',
    username: '',
    password: ''
  });
  const [images, setImages] = useState([]);
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

    if (images.length < 2) {
      setMessage('Please upload at least 2 photos for face recognition');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const data = new FormData();
      Object.keys(formData).forEach(key => {
        data.append(key, formData[key]);
      });

      images.forEach((image, index) => {
        data.append('images', image);
      });

      const result = await addStudent(data);

      if (result.success) {
        setMessage('Student added successfully!');
        setFormData({ name: '', roll: '', email: '', username: '', password: '' });
        setImages([]);
      } else {
        setMessage(result.message || 'Failed to add student');
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
            <button className="btn btn-primary" onClick={() => navigate('/admin/add-faculty')}>
              Add Faculty
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
        <div className="card" style={{ maxWidth: '700px', margin: '0 auto' }}>
          <h2 style={{ marginBottom: '30px', color: '#2d3748' }}>Add Student</h2>

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
                placeholder="Enter student name"
              />
            </div>

            <div className="form-group">
              <label>Roll Number</label>
              <input
                type="text"
                name="roll"
                value={formData.roll}
                onChange={handleChange}
                required
                placeholder="Enter roll number"
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

            <div className="form-group">
              <label>Upload Photos (2-3 images required)</label>
              <ImageCapture onCapture={setImages} multiple={true} />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={loading}
            >
              {loading ? 'Adding Student...' : 'Add Student'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default AddStudent;
