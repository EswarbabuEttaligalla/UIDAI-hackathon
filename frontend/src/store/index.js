import { create } from 'zustand';
import { authAPI, dashboardAPI, alertAPI, simulationAPI, governanceAPI } from '../services/api';

// Auth Store
export const useAuthStore = create((set, get) => ({
  user: JSON.parse(localStorage.getItem('user')) || null,
  token: localStorage.getItem('token') || null,
  isAuthenticated: !!localStorage.getItem('token'),
  loading: false,
  error: null,

  // Set user directly (for OTP login)
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  
  // Set token directly (for OTP login)
  setToken: (token) => set({ token }),

  login: async (username, password) => {
    set({ loading: true, error: null });
    try {
      const data = await authAPI.login(username, password);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      set({
        user: data.user,
        token: data.access_token,
        isAuthenticated: true,
        loading: false,
      });
      return true;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Login failed',
        loading: false,
      });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    });
  },

  clearError: () => set({ error: null }),
}));

// Dashboard Store
export const useDashboardStore = create((set, get) => ({
  metrics: null,
  trends: null,
  regions: null,
  loading: false,
  error: null,
  lastUpdated: null,

  fetchMetrics: async () => {
    set({ loading: true });
    try {
      const data = await dashboardAPI.getMetrics();
      set({ metrics: data, loading: false, lastUpdated: new Date() });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  fetchTrends: async (days = 7) => {
    try {
      const data = await dashboardAPI.getTrends(days);
      set({ trends: data });
    } catch (error) {
      console.error('Failed to fetch trends:', error);
    }
  },

  fetchRegions: async () => {
    try {
      const data = await dashboardAPI.getRegions();
      set({ regions: data.regions });
    } catch (error) {
      console.error('Failed to fetch regions:', error);
    }
  },

  refreshAll: async () => {
    const { fetchMetrics, fetchTrends, fetchRegions } = get();
    await Promise.all([fetchMetrics(), fetchTrends(), fetchRegions()]);
  },
}));

// Alerts Store
export const useAlertsStore = create((set, get) => ({
  alerts: [],
  selectedAlert: null,
  statistics: null,
  totalCount: 0,
  loading: false,
  error: null,
  filters: {
    status: null,
    severity: null,
  },

  fetchAlerts: async (params = {}) => {
    set({ loading: true });
    try {
      const { filters } = get();
      const data = await alertAPI.getAlerts({
        ...filters,
        ...params,
      });
      set({
        alerts: data.alerts,
        totalCount: data.total_count,
        loading: false,
      });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  fetchAlertById: async (alertId) => {
    set({ loading: true });
    try {
      const data = await alertAPI.getAlertById(alertId);
      set({ selectedAlert: data, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  updateAlertStatus: async (alertId, status) => {
    try {
      await alertAPI.updateAlert(alertId, { status });
      // Refresh alerts
      get().fetchAlerts();
    } catch (error) {
      console.error('Failed to update alert:', error);
    }
  },

  fetchStatistics: async () => {
    try {
      const data = await alertAPI.getStatistics();
      set({ statistics: data });
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
    }
  },

  setFilters: (filters) => {
    set({ filters });
    get().fetchAlerts();
  },

  clearSelectedAlert: () => set({ selectedAlert: null }),
}));

// Simulation Store
export const useSimulationStore = create((set, get) => ({
  scenarios: [],
  activeSimulation: null,
  history: [],
  loading: false,
  error: null,

  fetchScenarios: async () => {
    try {
      const data = await simulationAPI.getScenarios();
      set({ scenarios: data.scenarios });
    } catch (error) {
      console.error('Failed to fetch scenarios:', error);
    }
  },

  runSimulation: async (scenario, intensity, duration, region) => {
    set({ loading: true, error: null });
    try {
      const data = await simulationAPI.runSimulation(scenario, intensity, duration, region);
      set((state) => ({
        activeSimulation: data,
        history: [data, ...state.history],
        loading: false,
      }));
      return data;
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Simulation failed', loading: false });
      return null;
    }
  },

  clearActiveSimulation: () => set({ activeSimulation: null }),
}));

// Governance Store
export const useGovernanceStore = create((set, get) => ({
  privacyInfo: null,
  auditLogs: [],
  loading: false,
  error: null,

  fetchPrivacyInfo: async () => {
    try {
      const data = await governanceAPI.getPrivacyInfo();
      set({ privacyInfo: data });
    } catch (error) {
      console.error('Failed to fetch privacy info:', error);
    }
  },

  fetchAuditLogs: async (limit = 100) => {
    set({ loading: true });
    try {
      const data = await governanceAPI.getAuditLogs(limit);
      set({ auditLogs: data.logs, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },
}));
