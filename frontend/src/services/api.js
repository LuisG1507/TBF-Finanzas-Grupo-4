import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});


export const loginUser = async (credentials) => {
  const response = await api.post('/login', credentials);
  return response.data;
};

export default api;