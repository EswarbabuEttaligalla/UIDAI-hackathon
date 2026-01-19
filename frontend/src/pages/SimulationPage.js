import React, { useEffect, useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  PlayCircle as PlayIcon,
  CheckCircle as CheckIcon,
  DevicesOther as DeviceIcon,
  LocationOn as LocationIcon,
  Sms as OtpIcon,
  NightlightRound as NightIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useSimulationStore, useDashboardStore, useAlertsStore } from '../store';

const scenarioIcons = {
  DEVICE_SPIKE: <DeviceIcon />,
  REGIONAL_ANOMALY: <LocationIcon />,
  OTP_ABUSE: <OtpIcon />,
  OFF_HOURS_SPIKE: <NightIcon />,
  SERVICE_PROVIDER_ANOMALY: <BusinessIcon />,
};

const scenarioDescriptions = {
  DEVICE_SPIKE: 'Generates a high volume of authentication events from a single device, simulating potential device compromise or automated attacks.',
  REGIONAL_ANOMALY: 'Creates unusual authentication patterns in a specific region, including off-hours activity and high retry rates.',
  OTP_ABUSE: 'Simulates excessive OTP fallback usage with high failure rates, indicating potential biometric bypass attempts.',
  OFF_HOURS_SPIKE: 'Generates authentication activity during unusual hours (2 AM - 5 AM), suggesting automated or fraudulent behavior.',
  SERVICE_PROVIDER_ANOMALY: 'Creates anomalous behavior from a service provider, including excessive retries and long session durations.',
};

const REGIONS = [
  { code: 'MH', name: 'Maharashtra' },
  { code: 'DL', name: 'Delhi' },
  { code: 'KA', name: 'Karnataka' },
  { code: 'TN', name: 'Tamil Nadu' },
  { code: 'UP', name: 'Uttar Pradesh' },
  { code: 'GJ', name: 'Gujarat' },
  { code: 'RJ', name: 'Rajasthan' },
  { code: 'WB', name: 'West Bengal' },
  { code: 'TS', name: 'Telangana' },
  { code: 'KL', name: 'Kerala' },
];

const SimulationPage = () => {
  const { scenarios, history, loading, error, fetchScenarios, runSimulation } = useSimulationStore();
  const { refreshAll } = useDashboardStore();
  const { fetchAlerts, fetchStatistics } = useAlertsStore();

  const [selectedScenario, setSelectedScenario] = useState('');
  const [intensity, setIntensity] = useState(1.0);
  const [duration, setDuration] = useState(5);
  const [targetRegion, setTargetRegion] = useState('');
  const [simulationResult, setSimulationResult] = useState(null);

  const loadScenarios = useCallback(() => {
    fetchScenarios();
  }, [fetchScenarios]);

  useEffect(() => {
    loadScenarios();
  }, [loadScenarios]);

  const handleRunSimulation = async () => {
    if (!selectedScenario) return;

    const result = await runSimulation(
      selectedScenario,
      intensity,
      duration,
      targetRegion || null
    );

    if (result) {
      setSimulationResult(result);
      // Refresh dashboard and alerts after simulation
      setTimeout(() => {
        refreshAll();
        fetchAlerts();
        fetchStatistics();
      }, 1000);
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>
          Simulation Control Panel
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Generate synthetic misuse scenarios for testing and demonstration
        </Typography>
      </Box>

      {/* Warning Notice */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Simulation Mode:</strong> Simulations generate synthetic data to demonstrate the system's detection capabilities.
          This does not affect real UIDAI systems or actual Aadhaar data.
        </Typography>
      </Alert>

      <Grid container spacing={3}>
        {/* Simulation Controls */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Configure Simulation
              </Typography>

              {/* Scenario Selection */}
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Select Scenario</InputLabel>
                <Select
                  value={selectedScenario}
                  label="Select Scenario"
                  onChange={(e) => setSelectedScenario(e.target.value)}
                >
                  {scenarios.map((scenario) => (
                    <MenuItem key={scenario.id} value={scenario.id}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {scenarioIcons[scenario.id]}
                        <span>{scenario.name}</span>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {selectedScenario && (
                <Alert severity="warning" sx={{ mb: 3 }}>
                  <Typography variant="body2">
                    {scenarioDescriptions[selectedScenario]}
                  </Typography>
                </Alert>
              )}

              {/* Target Region */}
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Target Region (Optional)</InputLabel>
                <Select
                  value={targetRegion}
                  label="Target Region (Optional)"
                  onChange={(e) => setTargetRegion(e.target.value)}
                >
                  <MenuItem value="">Random</MenuItem>
                  {REGIONS.map((region) => (
                    <MenuItem key={region.code} value={region.code}>
                      {region.name} ({region.code})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Intensity Slider */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Intensity: {intensity.toFixed(1)}x
                </Typography>
                <Slider
                  value={intensity}
                  onChange={(e, value) => setIntensity(value)}
                  min={0.5}
                  max={2.0}
                  step={0.1}
                  marks={[
                    { value: 0.5, label: 'Low' },
                    { value: 1.0, label: 'Normal' },
                    { value: 1.5, label: 'High' },
                    { value: 2.0, label: 'Extreme' },
                  ]}
                />
                <Typography variant="caption" color="text.secondary">
                  Higher intensity generates more events per simulation
                </Typography>
              </Box>

              {/* Duration */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Duration: {duration} minutes
                </Typography>
                <Slider
                  value={duration}
                  onChange={(e, value) => setDuration(value)}
                  min={1}
                  max={15}
                  step={1}
                  marks={[
                    { value: 1, label: '1m' },
                    { value: 5, label: '5m' },
                    { value: 10, label: '10m' },
                    { value: 15, label: '15m' },
                  ]}
                />
              </Box>

              {/* Run Button */}
              <Button
                fullWidth
                variant="contained"
                size="large"
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <PlayIcon />}
                onClick={handleRunSimulation}
                disabled={!selectedScenario || loading}
                sx={{
                  py: 1.5,
                  background: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #d97706 0%, #dc2626 100%)',
                  },
                }}
              >
                {loading ? 'Running Simulation...' : 'Run Simulation'}
              </Button>

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Simulation Result & History */}
        <Grid item xs={12} lg={6}>
          {/* Latest Result */}
          {simulationResult && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <CheckIcon color="success" />
                  <Typography variant="h6" fontWeight={600}>
                    Simulation Complete
                  </Typography>
                </Box>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Scenario
                    </Typography>
                    <Typography variant="body1" fontWeight={500}>
                      {simulationResult.scenario}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Events Generated
                    </Typography>
                    <Typography variant="body1" fontWeight={500}>
                      {simulationResult.events_generated}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Status
                    </Typography>
                    <Chip
                      label={simulationResult.status}
                      color="success"
                      size="small"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Simulation ID
                    </Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {simulationResult.simulation_id}
                    </Typography>
                  </Grid>
                </Grid>
                <Alert severity="success" sx={{ mt: 2 }}>
                  Check the Alerts page to see any newly generated alerts from this simulation.
                </Alert>
              </CardContent>
            </Card>
          )}

          {/* Scenario Cards */}
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Available Scenarios
              </Typography>
              <List>
                {scenarios.map((scenario) => (
                  <React.Fragment key={scenario.id}>
                    <ListItem
                      button
                      selected={selectedScenario === scenario.id}
                      onClick={() => setSelectedScenario(scenario.id)}
                      sx={{ borderRadius: 1 }}
                    >
                      <ListItemIcon>
                        {scenarioIcons[scenario.id]}
                      </ListItemIcon>
                      <ListItemText
                        primary={scenario.name}
                        secondary={scenario.description}
                      />
                    </ListItem>
                    <Divider variant="inset" component="li" />
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* History */}
          {history.length > 0 && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Recent Simulations
                </Typography>
                <List dense>
                  {history.slice(0, 5).map((sim, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <CheckIcon color="success" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={sim.scenario}
                        secondary={`${sim.events_generated} events • ${sim.simulation_id}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default SimulationPage;
