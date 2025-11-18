import apiClient from './apiClient';

export const adminLogin = async (credentials) => {
  try {
    const response = await apiClient.post('/auth/admin_login', credentials);
    return response.data;
  } catch (error) {
    return { success: false, message: error.response?.data?.message || error.message };
  }
};

export const facultyLogin = async (credentials) => {
  try {
    const response = await apiClient.post('/auth/faculty_login', credentials);
    return response.data;
  } catch (error) {
    return { success: false, message: error.response?.data?.message || error.message };
  }
};

export const studentLogin = async (credentials) => {
  try {
    const response = await apiClient.post('/auth/student_login', credentials);
    return response.data;
  } catch (error) {
    return { success: false, message: error.response?.data?.message || error.message };
  }
};
