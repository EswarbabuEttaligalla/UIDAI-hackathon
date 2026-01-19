import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  InputAdornment,
  Divider,
  Chip,
  Stack,
  IconButton,
} from '@mui/material';
import {
  Phone as PhoneIcon,
  Lock as LockIcon,
  Security as SecurityIcon,
  ArrowBack as BackIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useAuthStore } from '../store';
import { authAPI } from '../services/api';

const steps = ['Enter Phone Number', 'Verify OTP'];

// Authentication demo users - uses 9900XXXXXX reserved series
const demoUsers = [
  { phone: '1234567890', name: 'System Administrator', role: 'ADMIN' },
  { phone: '9900000001', name: 'UIDAI Administrator', role: 'ADMIN' },
  { phone: '9900000002', name: 'Priya Sharma (Analyst)', role: 'ANALYST' },
  { phone: '9900000003', name: 'Rahul Kumar (Analyst)', role: 'ANALYST' },
  { phone: '9900000004', name: 'Anjali Patel (Viewer)', role: 'VIEWER' },
];

const LoginPage = () => {
  const navigate = useNavigate();
  const { setUser, setToken } = useAuthStore();
  
  const [activeStep, setActiveStep] = useState(0);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [sentOtp, setSentOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [countdown, setCountdown] = useState(0);

  const handleSendOTP = async () => {
    if (!phone || phone.length !== 10) {
      setError('Please enter a valid 10-digit phone number');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await authAPI.sendOTP(phone);
      
      if (response.success) {
        setSuccess(response.message);
        setSentOtp(response.otp); // Testing only - shows OTP
        setActiveStep(1);
        startCountdown();
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to send OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (!otp || otp.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await authAPI.verifyOTP(phone, otp);
      
      if (response.success) {
        // Store auth data
        localStorage.setItem('token', response.access_token);
        localStorage.setItem('user', JSON.stringify(response.user));
        
        // Update store
        setUser(response.user);
        setToken(response.access_token);
        
        setSuccess('Login successful! Redirecting...');
        setTimeout(() => navigate('/app/dashboard'), 1000);
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Invalid OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    if (countdown > 0) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await authAPI.resendOTP(phone);
      
      if (response.success) {
        setSuccess(response.message);
        setSentOtp(response.otp);
        startCountdown();
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError('Failed to resend OTP');
    } finally {
      setLoading(false);
    }
  };

  const startCountdown = () => {
    setCountdown(60);
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleBack = () => {
    setActiveStep(0);
    setOtp('');
    setSentOtp('');
    setError('');
    setSuccess('');
  };

  const selectDemoUser = (userPhone) => {
    setPhone(userPhone);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        p: 2,
      }}
    >
      <Card
        sx={{
          maxWidth: 480,
          width: '100%',
          background: 'linear-gradient(135deg, rgba(30,30,50,0.95) 0%, rgba(20,20,40,0.98) 100%)',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <CardContent sx={{ p: 4 }}>
          {/* Compliance Notice */}
          <Alert 
            severity="info" 
            sx={{ 
              mb: 3, 
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.3)'
            }}
          >
            <Typography variant="caption" display="block">
              <strong>⚠️ SIMULATION NOTICE:</strong> This is a demonstration environment using synthetic phone numbers 
              (9900XXXXXX series). No real Aadhaar or UIDAI data is accessed. All data is fictional.
            </Typography>
          </Alert>

          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                mx: 'auto',
                mb: 2,
              }}
            >
              <SecurityIcon sx={{ fontSize: 40 }} />
            </Box>
            <Typography variant="h4" fontWeight={700}>
              AMEWS
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Aadhaar Misuse Early-Warning System
            </Typography>
          </Box>

          {/* Stepper */}
          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {/* Alerts */}
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
              {error}
            </Alert>
          )}
          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {success}
            </Alert>
          )}

          {/* Step 1: Phone Number */}
          {activeStep === 0 && (
            <>
              <TextField
                fullWidth
                label="Phone Number"
                placeholder="Enter 10-digit phone number"
                value={phone}
                onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <PhoneIcon color="primary" />
                      <Typography sx={{ ml: 1, mr: 0.5 }}>+91</Typography>
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 3 }}
              />

              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handleSendOTP}
                disabled={loading || phone.length !== 10}
                sx={{
                  py: 1.5,
                  background: 'linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%)',
                }}
              >
                {loading ? <CircularProgress size={24} /> : 'Send OTP'}
              </Button>

              <Divider sx={{ my: 3 }}>
                <Chip label="Test Users" size="small" />
              </Divider>

              <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                Click to auto-fill phone number:
              </Typography>
              
              <Stack spacing={1}>
                {demoUsers.map((user) => (
                  <Button
                    key={user.phone}
                    variant="outlined"
                    size="small"
                    onClick={() => selectDemoUser(user.phone)}
                    sx={{
                      justifyContent: 'flex-start',
                      textTransform: 'none',
                      borderColor: phone === user.phone ? 'primary.main' : 'divider',
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                      <span>📱 {user.phone} - {user.name}</span>
                      <Chip label={user.role} size="small" sx={{ ml: 1 }} />
                    </Box>
                  </Button>
                ))}
              </Stack>
            </>
          )}

          {/* Step 2: OTP Verification */}
          {activeStep === 1 && (
            <>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <IconButton onClick={handleBack} sx={{ mr: 1 }}>
                  <BackIcon />
                </IconButton>
                <Typography variant="body2" color="text.secondary">
                  OTP sent to +91 {phone}
                </Typography>
              </Box>

              {/* Show OTP for testing */}
              {sentOtp && (
                <Alert severity="success" sx={{ mb: 2, backgroundColor: 'rgba(34, 197, 94, 0.15)' }}>
                  <Typography variant="body2">
                    <strong>🔐 Simulated OTP Delivery:</strong> Your OTP is <strong style={{ fontSize: '1.2em', letterSpacing: '3px' }}>{sentOtp}</strong>
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    (In production, this would be sent via encrypted SMS)
                  </Typography>
                </Alert>
              )}

              <TextField
                fullWidth
                label="Enter OTP"
                placeholder="Enter 6-digit OTP"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockIcon color="primary" />
                    </InputAdornment>
                  ),
                }}
                sx={{ mb: 3 }}
              />

              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handleVerifyOTP}
                disabled={loading || otp.length !== 6}
                sx={{
                  py: 1.5,
                  mb: 2,
                  background: 'linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%)',
                }}
              >
                {loading ? <CircularProgress size={24} /> : 'Verify & Login'}
              </Button>

              <Box sx={{ textAlign: 'center' }}>
                <Button
                  startIcon={<RefreshIcon />}
                  onClick={handleResendOTP}
                  disabled={countdown > 0 || loading}
                  sx={{ textTransform: 'none' }}
                >
                  {countdown > 0 ? `Resend OTP in ${countdown}s` : 'Resend OTP'}
                </Button>
              </Box>
            </>
          )}

          {/* Back to Landing */}
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Button
              variant="text"
              onClick={() => navigate('/')}
              sx={{ textTransform: 'none' }}
            >
              ← Back to Home
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default LoginPage;
