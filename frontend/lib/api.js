import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 5000, // Reduced timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor with better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.message);
    return Promise.reject(error);
  }
);

// Simple strategy API calls
export const strategyAPI = {
  getAll: () => api.get('/strategies'),
  getById: (id) => api.get(`/strategies/${id}`),
  run: (id, params) => api.post(`/strategies/${id}/run`, params),
  stop: (id) => api.post(`/strategies/${id}/stop`),
  getStatus: (id) => api.get(`/strategies/${id}/status`),
};

export default api;