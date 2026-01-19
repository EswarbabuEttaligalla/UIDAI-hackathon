import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  login: async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },
  
  // OTP-based authentication
  sendOTP: async (phone) => {
    const response = await api.post('/api/auth/otp/send', { phone });
    return response.data;
  },
  
  verifyOTP: async (phone, otp) => {
    const response = await api.post('/api/auth/otp/verify', { phone, otp });
    return response.data;
  },
  
  resendOTP: async (phone) => {
    const response = await api.post('/api/auth/otp/resend', { phone });
    return response.data;
  },
  
  getDemoUsers: async () => {
    const response = await api.get('/api/auth/demo-users');
    return response.data;
  },
  
  getMe: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },
};

// Dashboard APIs
export const dashboardAPI = {
  getMetrics: async () => {
    const response = await api.get('/api/dashboard/metrics');
    return response.data;
  },
  
  getTrends: async (days = 7) => {
    const response = await api.get(`/api/dashboard/trends?days=${days}`);
    return response.data;
  },
  
  getRegions: async () => {
    const response = await api.get('/api/dashboard/regions');
    return response.data;
  },
};

// Alert APIs
export const alertAPI = {
  getAlerts: async (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.status) queryParams.append('status', params.status);
    if (params.severity) queryParams.append('severity', params.severity);
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.offset) queryParams.append('offset', params.offset);
    
    const response = await api.get(`/api/alerts?${queryParams.toString()}`);
    return response.data;
  },
  
  getAlertById: async (alertId) => {
    const response = await api.get(`/api/alerts/${alertId}`);
    return response.data;
  },
  
  updateAlert: async (alertId, update) => {
    const response = await api.patch(`/api/alerts/${alertId}`, update);
    return response.data;
  },
  
  getStatistics: async () => {
    const response = await api.get('/api/alerts/statistics/summary');
    return response.data;
  },
};

// Risk APIs
export const riskAPI = {
  analyzeRisk: async (entityType, entityId, timeWindowHours = 24) => {
    const response = await api.post('/api/risk/analyze', {
      entity_type: entityType,
      entity_id: entityId,
      time_window_hours: timeWindowHours,
    });
    return response.data;
  },
  
  getOverview: async () => {
    const response = await api.get('/api/risk/overview');
    return response.data;
  },
};

// Simulation APIs
export const simulationAPI = {
  getScenarios: async () => {
    const response = await api.get('/api/simulation/scenarios');
    return response.data;
  },
  
  runSimulation: async (scenario, intensity = 1.0, durationMinutes = 5, targetRegion = null) => {
    const response = await api.post('/api/simulation/run', {
      scenario,
      intensity,
      duration_minutes: durationMinutes,
      target_region: targetRegion,
    });
    return response.data;
  },
};

// Governance APIs
export const governanceAPI = {
  getPrivacyInfo: async () => {
    const response = await api.get('/api/governance/privacy');
    return response.data;
  },
  
  getAuditLogs: async (limit = 100) => {
    const response = await api.get(`/api/governance/audit-logs?limit=${limit}`);
    return response.data;
  },
};

// Dataset APIs
export const datasetAPI = {
  getInfo: async () => {
    const response = await api.get('/api/dataset/info');
    return response.data;
  },
  
  getStates: async () => {
    const response = await api.get('/api/dataset/states');
    return response.data;
  },
};

// Admin APIs
export const adminAPI = {
  generateData: async (days = 7, eventsPerDay = 200) => {
    const response = await api.post(`/api/admin/generate-data?days=${days}&events_per_day=${eventsPerDay}`);
    return response.data;
  },
  
  trainModel: async () => {
    const response = await api.post('/api/admin/train-model');
    return response.data;
  },
};

// Health check
export const healthAPI = {
  check: async () => {
    const response = await api.get('/api/health');
    return response.data;
  },
};

export default api;
