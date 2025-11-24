import axios from 'axios';
import { io } from 'socket.io-client';

// API URL is set at build time via VITE_API_URL environment variable
// Falls back to default development URL if not set
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5002';

// Axios instance for HTTP requests
export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // Important for Flask sessions
  headers: {
    'Content-Type': 'application/json',
  },
});

// Socket.IO client
export const socket = io(API_URL, {
  withCredentials: true,
  autoConnect: false,
});

export const authAPI = {
  login: (email, password) => api.post('/login', { email, password }),
  register: (email, password, name) => api.post('/api/register', { email, password, name }),
  logout: () => api.get('/logout'),
  checkStatus: () => api.get('/api/auth/status'),
  verifyEmail: (token) => api.get(`/api/verify-email?token=${token}`),
  resendVerification: (email) => api.post('/api/resend-verification', { email }),
  forgotPassword: (email) => api.post('/api/forgot-password', { email }),
  resetPassword: (token, newPassword) => api.post('/api/reset-password', { token, new_password: newPassword }),
};

export const botAPI = {
  start: () => api.post('/api/start'),
  stop: () => api.post('/api/stop'),
  getDashboardData: () => api.get('/api/dashboard/data'),
  getStatus: () => api.get('/api/status'),
  getHistory: () => api.get('/api/history'),
  getSettings: () => api.get('/api/settings'),
  updateSettings: (settings) => api.post('/api/settings', settings)
};

export const accountAPI = {
  getProfile: () => api.get('/api/account/profile'),
  updateProfile: (data) => api.put('/api/account/profile', data),
  updatePassword: (currentPassword, newPassword) => api.put('/api/account/password', {
    current_password: currentPassword,
    new_password: newPassword
  }),
  getCredentials: () => api.get('/api/account/credentials'),
  saveCredentials: (apiKey, secretKey, tradingMode) => api.post('/api/account/credentials', {
    alpaca_api_key: apiKey,
    alpaca_secret_key: secretKey,
    trading_mode: tradingMode
  }),
  testCredentials: (apiKey, secretKey, tradingMode) => api.post('/api/account/credentials/test', {
    alpaca_api_key: apiKey,
    alpaca_secret_key: secretKey,
    trading_mode: tradingMode
  }),
  deleteCredentials: () => api.delete('/api/account/credentials'),
};
