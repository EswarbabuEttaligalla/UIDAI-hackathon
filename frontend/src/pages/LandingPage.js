import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Stack,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Chip,
} from '@mui/material';
import {
  Shield as ShieldIcon,
  Speed as SpeedIcon,
  Analytics as AnalyticsIcon,
  Security as SecurityIcon,
  CheckCircle as CheckCircleIcon,
  Block as BlockIcon,
  ArrowForward as ArrowForwardIcon,
  Dashboard as DashboardIcon,
  Warning as WarningIcon,
  Policy as PolicyIcon,
  PlayCircle as PlayCircleIcon,
  TrendingUp as TrendingUpIcon,
  LocationOn as LocationIcon,
  PhonelinkLock as PhonelinkLockIcon,
  Schedule as ScheduleIcon,
  Business as BusinessIcon,
  Fingerprint as FingerprintIcon,
  Verified as VerifiedIcon,
} from '@mui/icons-material';

const monitoringPatterns = [
  { icon: <SpeedIcon />, label: 'Velocity Attacks', description: 'Excessive authentications from single device' },
  { icon: <LocationIcon />, label: 'Geographic Anomalies', description: 'Impossible travel patterns across states' },
  { icon: <PhonelinkLockIcon />, label: 'OTP Fallback Abuse', description: 'Biometric bypass through excessive OTP usage' },
  { icon: <ScheduleIcon />, label: 'Off-Hours Spikes', description: 'Automated attacks during non-business hours' },
  { icon: <BusinessIcon />, label: 'Service Provider Anomalies', description: 'Suspicious patterns from AUA/KUA entities' },
];

const systemFlow = [
  { step: '1', title: 'Data Ingestion', description: 'Anonymized authentication metadata from service providers' },
  { step: '2', title: 'Baseline Learning', description: '14-day learning phase to establish normal behavior patterns' },
  { step: '3', title: 'Hybrid Analysis', description: 'Rule-based detection + ML anomaly scoring with confidence metrics' },
  { step: '4', title: 'Risk Scoring', description: 'Composite risk score with equity guardrails and action tiers' },
  { step: '5', title: 'Alert Generation', description: 'Automated alerts with recommended actions for analysts' },
];

const privacyPrinciples = [
  'No access to Aadhaar numbers (UID)',
  'No biometric data collection',
  'No personal demographic information',
  'No exact addresses or contact details',
  'Device identifiers are one-way hashed (SHA-256)',
  'Location limited to state/district aggregation',
  'Separation from UIDAI core authentication systems',
];

const operationalValue = [
  { title: 'Early Detection', description: 'Identify misuse patterns in minutes instead of weeks' },
  { title: 'Reduced False Positives', description: 'Baseline learning and confidence scoring eliminate noise' },
  { title: 'Actionable Intelligence', description: 'Clear action tiers from Monitor to Immediate Response' },
  { title: 'Continuous Improvement', description: 'Analyst feedback loop enhances detection accuracy' },
  { title: 'Algorithmic Fairness', description: 'Equity guardrails prevent bias against underserved regions' },
  { title: 'Governance Oversight', description: 'Cross-regional and service-provider pattern visibility' },
];

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Hero Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #1e293b 0%, #334155 50%, #475569 100%)',
          color: 'white',
          py: 8,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            opacity: 0.1,
            backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)',
            backgroundSize: '30px 30px',
          }}
        />
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Stack alignItems="center" spacing={4}>
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: 3,
                background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 8px 32px rgba(59, 130, 246, 0.3)',
              }}
            >
              <ShieldIcon sx={{ fontSize: 48 }} />
            </Box>

            <Stack alignItems="center" spacing={2}>
              <Typography variant="h3" fontWeight={700} textAlign="center">
                AMEWS
              </Typography>
              <Typography variant="h5" fontWeight={400} sx={{ opacity: 0.9 }} textAlign="center">
                Aadhaar Misuse Early-Warning System
              </Typography>
              <Chip
                label="Internal UIDAI Monitoring Tool"
                sx={{
                  bgcolor: 'rgba(255, 255, 255, 0.2)',
                  color: 'white',
                  fontWeight: 600,
                  px: 2,
                  py: 0.5,
                }}
              />
            </Stack>

            <Typography
              variant="h6"
              fontWeight={500}
              textAlign="center"
              sx={{ maxWidth: 800, opacity: 0.95, lineHeight: 1.6 }}
            >
              Early Warning Before Damage: Monitoring Aadhaar Usage Patterns at National Scale
            </Typography>

            <Typography
              variant="body1"
              textAlign="center"
              sx={{ maxWidth: 900, opacity: 0.85, lineHeight: 1.8 }}
            >
              AMEWS is a privacy-preserving intelligence system that continuously analyzes authentication
              behavior across regions, services, devices, and time bands to identify anomalies and generate
              actionable alerts for UIDAI analysts. Operating automatically on post-authentication behavioral
              metadata, the system detects misuse patterns before large-scale damage occurs—without accessing
              Aadhaar numbers, biometrics, or personal information.
            </Typography>

            <Button
              variant="contained"
              size="large"
              endIcon={<ArrowForwardIcon />}
              onClick={() => navigate('/login')}
              sx={{
                mt: 2,
                px: 4,
                py: 1.5,
                fontSize: '1.1rem',
                bgcolor: 'white',
                color: 'primary.main',
                '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.9)' },
              }}
            >
              Access System
            </Button>
          </Stack>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ py: 8 }}>
        {/* Project Glimpse */}
        <Stack spacing={6}>
          <Box>
            <Typography variant="h4" fontWeight={700} gutterBottom textAlign="center">
              Project Glimpse: End-to-End Flow
            </Typography>
            <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ mb: 4 }}>
              Automated behavioral analysis pipeline—from ingestion to actionable intelligence
            </Typography>

            <Grid container spacing={3}>
              {systemFlow.map((item, index) => (
                <Grid item xs={12} md={2.4} key={index}>
                  <Card
                    sx={{
                      height: '100%',
                      textAlign: 'center',
                      position: 'relative',
                      border: '2px solid',
                      borderColor: 'primary.main',
                      bgcolor: index === 0 || index === 4 ? 'rgba(59, 130, 246, 0.05)' : 'background.paper',
                    }}
                  >
                    <CardContent>
                      <Box
                        sx={{
                          width: 48,
                          height: 48,
                          borderRadius: '50%',
                          bgcolor: 'primary.main',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 700,
                          fontSize: '1.5rem',
                          mx: 'auto',
                          mb: 2,
                        }}
                      >
                        {item.step}
                      </Box>
                      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                        {item.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                        {item.description}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            <Paper
              sx={{
                mt: 3,
                p: 3,
                bgcolor: 'success.main',
                color: 'white',
                textAlign: 'center',
              }}
            >
              <Stack direction="row" alignItems="center" justifyContent="center" spacing={2}>
                <SecurityIcon sx={{ fontSize: 32 }} />
                <Typography variant="h6" fontWeight={600}>
                  100% Automated Detection – No Manual Complaints or User Reporting Required
                </Typography>
              </Stack>
            </Paper>
          </Box>

          <Divider />

          {/* What AMEWS Monitors */}
          <Box>
            <Typography variant="h4" fontWeight={700} gutterBottom textAlign="center">
              What AMEWS Monitors
            </Typography>
            <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ mb: 4 }}>
              Behavioral indicators of potential misuse patterns—not fraud accusations
            </Typography>

            <Grid container spacing={3}>
              {monitoringPatterns.map((pattern, index) => (
                <Grid item xs={12} md={4} key={index}>
                  <Card sx={{ height: '100%' }}>
                    <CardContent>
                      <Stack direction="row" spacing={2} alignItems="flex-start">
                        <Box
                          sx={{
                            width: 48,
                            height: 48,
                            borderRadius: 2,
                            bgcolor: 'primary.light',
                            color: 'primary.main',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          {pattern.icon}
                        </Box>
                        <Box flex={1}>
                          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                            {pattern.label}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {pattern.description}
                          </Typography>
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
              <Grid item xs={12} md={4}>
                <Card sx={{ height: '100%', bgcolor: 'rgba(59, 130, 246, 0.05)' }}>
                  <CardContent>
                    <Stack direction="row" spacing={2} alignItems="flex-start">
                      <Box
                        sx={{
                          width: 48,
                          height: 48,
                          borderRadius: 2,
                          bgcolor: 'primary.main',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <TrendingUpIcon />
                      </Box>
                      <Box flex={1}>
                        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                          Cumulative Baseline Deviation
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Low-and-slow attacks evading fixed thresholds
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>

          <Divider />

          {/* Privacy & Governance */}
          <Box>
            <Typography variant="h4" fontWeight={700} gutterBottom textAlign="center">
              Privacy & Governance at a Glance
            </Typography>
            <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ mb: 4 }}>
              Strengthening Aadhaar trust without expanding surveillance
            </Typography>

            <Grid container spacing={4}>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 4, height: '100%', bgcolor: 'error.lighter' }}>
                  <Stack spacing={2}>
                    <Stack direction="row" alignItems="center" spacing={2}>
                      <BlockIcon color="error" sx={{ fontSize: 32 }} />
                      <Typography variant="h6" fontWeight={600}>
                        What AMEWS Never Accesses
                      </Typography>
                    </Stack>
                    <List dense>
                      {privacyPrinciples.map((principle, index) => (
                        <ListItem key={index} sx={{ py: 0.5 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <BlockIcon color="error" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary={principle}
                            primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Stack>
                </Paper>
              </Grid>

              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 4, height: '100%', bgcolor: 'success.lighter' }}>
                  <Stack spacing={2}>
                    <Stack direction="row" alignItems="center" spacing={2}>
                      <CheckCircleIcon color="success" sx={{ fontSize: 32 }} />
                      <Typography variant="h6" fontWeight={600}>
                        Core Privacy Principles
                      </Typography>
                    </Stack>
                    <List dense>
                      {[
                        'Data minimization - only behavioral metadata',
                        'Purpose limitation - fraud detection only',
                        'Anonymization - one-way hashing',
                        'Aggregation - minimum 5 events for statistics',
                        'Explainable scoring - full transparency',
                        'Audit trail - all actions logged',
                        'Separation - isolated from authentication systems',
                      ].map((principle, index) => (
                        <ListItem key={index} sx={{ py: 0.5 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <CheckCircleIcon color="success" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary={principle}
                            primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Stack>
                </Paper>
              </Grid>
            </Grid>
          </Box>

          <Divider />

          {/* Why This Matters */}
          <Box>
            <Typography variant="h4" fontWeight={700} gutterBottom textAlign="center">
              Why This Matters for UIDAI
            </Typography>
            <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ mb: 4 }}>
              Operational value beyond traditional fraud detection
            </Typography>

            <Grid container spacing={3}>
              {operationalValue.map((item, index) => (
                <Grid item xs={12} md={6} key={index}>
                  <Card sx={{ height: '100%', border: '1px solid', borderColor: 'divider' }}>
                    <CardContent>
                      <Stack direction="row" spacing={2} alignItems="flex-start">
                        <AnalyticsIcon color="primary" sx={{ mt: 0.5 }} />
                        <Box>
                          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                            {item.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {item.description}
                          </Typography>
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>

          {/* Explore System */}
          <Box sx={{ mt: 6 }}>
            <Paper
              sx={{
                p: 6,
                background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
                textAlign: 'center',
              }}
            >
              <Typography variant="h4" fontWeight={700} gutterBottom>
                Explore the System
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 700, mx: 'auto' }}>
                This landing page provides a high-level orientation. Detailed analysis, alerts, simulation,
                and governance tools are available for authorized analysts and administrators.
              </Typography>

              <Grid container spacing={2} justifyContent="center">
                <Grid item>
                  <Button
                    variant="contained"
                    size="large"
                    startIcon={<DashboardIcon />}
                    onClick={() => navigate('/app/dashboard')}
                  >
                    Dashboard
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    size="large"
                    startIcon={<WarningIcon />}
                    onClick={() => navigate('/app/alerts')}
                  >
                    Alerts
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    size="large"
                    startIcon={<PlayCircleIcon />}
                    onClick={() => navigate('/app/simulation')}
                  >
                    Simulation
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    size="large"
                    startIcon={<PolicyIcon />}
                    onClick={() => navigate('/app/governance')}
                  >
                    Governance
                  </Button>
                </Grid>
              </Grid>
            </Paper>
          </Box>
        </Stack>
      </Container>

      {/* Footer */}
      <Box sx={{ bgcolor: 'background.paper', borderTop: '1px solid', borderColor: 'divider', py: 4, mt: 8 }}>
        <Container maxWidth="lg">
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="body2" color="text.secondary">
              © 2026 UIDAI. Internal Monitoring System.
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center">
              <FingerprintIcon color="primary" fontSize="small" />
              <Typography variant="body2" color="text.secondary" fontWeight={600}>
                Privacy by Design | Zero PII Collection
              </Typography>
            </Stack>
          </Stack>
        </Container>
      </Box>
    </Box>
  );
};

export default LandingPage;
