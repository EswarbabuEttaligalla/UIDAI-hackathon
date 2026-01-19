import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import AlertsPage from './pages/AlertsPage';
import AlertDetailPage from './pages/AlertDetailPage';
import SimulationPage from './pages/SimulationPage';
import GovernancePage from './pages/GovernancePage';
import RiskAnalysisPage from './pages/RiskAnalysisPage';
import { Box, Typography, Button } from '@mui/material';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

const SimpleLanding = () => {
  return (
    <Box sx={{ 
      minHeight: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      alignItems: 'center', 
      justifyContent: 'center',
      bgcolor: 'background.default',
      color: 'text.primary',
      gap: 3
    }}>
      <Typography variant="h2" fontWeight={700}>🛡️ AMEWS</Typography>
      <Typography variant="h5" color="text.secondary">
        Aadhaar Misuse Early-Warning System
      </Typography>
      <Button 
        variant="contained" 
        size="large"
        href="/login"
        sx={{ mt: 2 }}
      >
        Login with OTP
      </Button>
    </Box>
  );
};

function App() {
  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected routes */}
        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/app/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="alerts/:alertId" element={<AlertDetailPage />} />
          <Route path="risk-analysis" element={<RiskAnalysisPage />} />
          <Route path="simulation" element={<SimulationPage />} />
          <Route path="governance" element={<GovernancePage />} />
        </Route>
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
