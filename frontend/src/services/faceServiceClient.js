import axios from 'axios';

const API_BASE_URL = '/api';

export const trainFaceRecognition = async (studentId) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/face/train`, { student_id: studentId });
    return response.data;
  } catch (error) {
    return { success: false, message: error.message };
  }
};

export const recognizeFace = async (imageFile) => {
  try {
    const formData = new FormData();
    formData.append('image', imageFile);

    const response = await axios.post(`${API_BASE_URL}/face/recognize`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  } catch (error) {
    return { success: false, message: error.message };
  }
};
