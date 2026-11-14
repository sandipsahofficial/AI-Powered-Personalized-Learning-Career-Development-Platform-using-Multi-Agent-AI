import axios from 'axios';

// Resolve base API URL from environment or fallback to relative /api/v1 (proxied via Vite)
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT access token to outbound requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor with automatic 401 token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token: newRefresh } = res.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefresh);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        } catch {
          // Token refresh failed - clean up tokens
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
        }
      }
    }

    const customError = {
      message: error.response?.data?.detail || error.response?.data?.message || error.message || 'Request failed',
      status: error.response?.status,
      data: error.response?.data,
    };
    return Promise.reject(customError);
  }
);
