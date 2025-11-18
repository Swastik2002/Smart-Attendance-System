import axios from 'axios';

const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const addStudent = async (formData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/admin/student`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  } catch (error) {
    return { success: false, message: error.response?.data?.message || error.message };
  }
};

export const addFaculty = async (data) => {
  try {
    const response = await apiClient.post('/admin/faculty', data);
    return response.data;
  } catch (error) {
    return { success: false, message: error.response?.data?.message || error.message };
  }
};

export const addSubject = async (data) => {
  try {
    const response = await apiClient.post('/admin/subject', data);
    return response.data;
  } catch (error) {
    return { success: false, message: error.response?.data?.message || error.message };
  }
};

export const getSubjects = async () => {
  try {
    const response = await apiClient.get('/faculty/subjects');
    return response.data;
  } catch (error) {
    return { success: false, message: error.message };
  }
};

export const getStudents = async (subjectId) => {
  try {
    const response = await apiClient.get(`/faculty/students?subject_id=${subjectId}`);
    return response.data;
  } catch (error) {
    return { success: false, message: error.message };
  }
};

export const markAttendance = async (data) => {
  try {
    const response = await apiClient.post('/attendance/mark', data);
    return response.data;
  } catch (error) {
    return { success: false, message: error.message };
  }
};

export const markAttendanceFromFace = async (formData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/attendance/mark_from_face`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  } catch (error) {
    return { success: false, message: error.response?.data?.message || error.message };
  }
};

export const getStudentAttendance = async (studentId) => {
  try {
    const response = await apiClient.get(`/student/attendance?student_id=${studentId}`);
    return response.data;
  } catch (error) {
    return { success: false, message: error.message };
  }
};

export default apiClient;
