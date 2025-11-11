import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const authAPI = axios.create({
  baseURL: API_URL,
});

export const register = async (email, password, role = 'user', adminKey = null) => {
  const endpoint = role === 'admin' ? '/auth/register-admin' : '/auth/register';
  const payload = { email, password };
  
  if (role === 'admin' && adminKey) {
    payload.admin_key = adminKey;
  }
  
  const response = await authAPI.post(endpoint, payload);
  return response.data;
};

export const login = async (email, password) => {
  const formData = new FormData();
  formData.append('username', email);
  formData.append('password', password);
  
  const response = await authAPI.post('/auth/login', formData);
  return response.data;
};

export const getMe = async (token) => {
  const response = await authAPI.get('/me', {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export default authAPI;