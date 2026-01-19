import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  Warning as WarningIcon,
  Assessment as AssessmentIcon,
  Rule as RuleIcon,
  Psychology as MLIcon,
} from '@mui/icons-material';
import { riskAPI } from '../services/api';

const RiskAnalysisPage = () => {
  const [entityType, setEntityType] = useState('DEVICE');
  const [entityId, setEntityId] = useState('');
  const [timeWindow, setTimeWindow] = useState(24);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [overview, setOverview] = useState(null);

  useEffect(() => {
    fetchOverview();
  }, []);

  const fetchOverview = async () => {
    try {
      const data = await riskAPI.getOverview();
      setOverview(data);
    } catch (err) {
      console.error('Failed to fetch overview:', err);
    }
  };

  const handleAnalyze = async () => {
    if (!entityId.trim()) {
      setError('Please enter an entity ID');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await riskAPI.analyzeRisk(entityType, entityId, timeWindow);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'CRITICAL': return 'error';
      case 'HIGH': return 'warning';
      case 'MEDIUM': return 'info';
      default: return 'success';
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>
          Risk Analysis
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Analyze authentication patterns and risk scores for entities
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Analysis Form */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Analyze Entity
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Enter an entity identifier to analyze its risk profile
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Entity Type</InputLabel>
                <Select
                  value={entityType}
                  label="Entity Type"
                  onChange={(e) => setEntityType(e.target.value)}
                >
                  <MenuItem value="DEVICE">Device (Fingerprint Hash)</MenuItem>
                  <MenuItem value="REGION">Region (State Code)</MenuItem>
                  <MenuItem value="SERVICE_PROVIDER">Service Provider</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Entity ID"
                value={entityId}
                onChange={(e) => setEntityId(e.target.value)}
                placeholder={
                  entityType === 'DEVICE' ? 'e.g., abc123def456...' :
                  entityType === 'REGION' ? 'e.g., MH, DL, KA' :
                  'e.g., SP_SBI_abc123'
                }
                sx={{ mb: 2 }}
              />

              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Time Window</InputLabel>
                <Select
                  value={timeWindow}
                  label="Time Window"
                  onChange={(e) => setTimeWindow(e.target.value)}
                >
                  <MenuItem value={1}>Last 1 Hour</MenuItem>
                  <MenuItem value={6}>Last 6 Hours</MenuItem>
                  <MenuItem value={24}>Last 24 Hours</MenuItem>
                  <MenuItem value={72}>Last 3 Days</MenuItem>
                  <MenuItem value={168}>Last 7 Days</MenuItem>
                </Select>
              </FormControl>

              <Button
                fullWidth
                variant="contained"
                size="large"
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />}
                onClick={handleAnalyze}
                disabled={loading}
              >
                {loading ? 'Analyzing...' : 'Analyze Risk'}
              </Button>

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* High Risk Entities */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                High Risk Entities (Last 24h)
              </Typography>

              {overview?.high_risk_devices?.length > 0 && (
                <>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2, mb: 1 }}>
                    Devices
                  </Typography>
                  <List dense>
                    {overview.high_risk_devices.slice(0, 5).map((device, index) => (
                      <ListItem
                        key={index}
                        button
                        onClick={() => {
                          setEntityType('DEVICE');
                          setEntityId(device.device.replace('...', ''));
                        }}
                        sx={{ borderRadius: 1 }}
                      >
                        <ListItemText
                          primary={device.device}
                          secondary={`${device.events} events, avg retries: ${device.avg_retries}`}
                          primaryTypographyProps={{ fontFamily: 'monospace', fontSize: '0.85rem' }}
                        />
                        <Chip
                          label={`${device.events} events`}
                          size="small"
                          color="warning"
                        />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}

              {overview?.high_risk_regions?.length > 0 && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                    Regions
                  </Typography>
                  <List dense>
                    {overview.high_risk_regions.slice(0, 5).map((region, index) => (
                      <ListItem
                        key={index}
                        button
                        onClick={() => {
                          setEntityType('REGION');
                          setEntityId(region.region);
                        }}
                        sx={{ borderRadius: 1 }}
                      >
                        <ListItemText
                          primary={region.region}
                          secondary={`${region.events} events, ${region.failures} failures`}
                        />
                        <Chip
                          label={`${region.failures} failures`}
                          size="small"
                          color="error"
                        />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Analysis Results */}
        <Grid item xs={12} lg={6}>
          {result ? (
            <>
              {/* Risk Score Card */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box>
                      <Typography variant="h6" fontWeight={600}>
                        Risk Assessment Result
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {result.entity_type}: {result.entity_id.substring(0, 20)}...
                      </Typography>
                    </Box>
                    <Chip
                      label={result.risk_level}
                      color={getRiskColor(result.risk_level)}
                      sx={{ fontWeight: 600 }}
                    />
                  </Box>

                  <Box sx={{ my: 4, textAlign: 'center' }}>
                    <Typography
                      variant="h1"
                      fontWeight={700}
                      color={getRiskColor(result.risk_level) + '.main'}
                    >
                      {result.composite_score?.toFixed(1)}
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary">
                      Composite Risk Score
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <LinearProgress
                      variant="determinate"
                      value={result.composite_score}
                      sx={{
                        height: 12,
                        borderRadius: 6,
                        backgroundColor: 'rgba(148, 163, 184, 0.2)',
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 6,
                          backgroundColor: 
                            result.composite_score >= 80 ? '#ef4444' :
                            result.composite_score >= 60 ? '#f59e0b' :
                            result.composite_score >= 30 ? '#3b82f6' : '#10b981',
                        },
                      }}
                    />
                  </Box>

                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Box sx={{ p: 2, bgcolor: 'rgba(148, 163, 184, 0.05)', borderRadius: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <RuleIcon fontSize="small" color="primary" />
                          <Typography variant="caption" color="text.secondary">
                            Rule-Based Score
                          </Typography>
                        </Box>
                        <Typography variant="h5" fontWeight={600}>
                          {result.rule_score?.toFixed(1)}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6}>
                      <Box sx={{ p: 2, bgcolor: 'rgba(148, 163, 184, 0.05)', borderRadius: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <MLIcon fontSize="small" color="secondary" />
                          <Typography variant="caption" color="text.secondary">
                            ML Anomaly Score
                          </Typography>
                        </Box>
                        <Typography variant="h5" fontWeight={600}>
                          {result.ml_score?.toFixed(1)}
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>

              {/* Contributing Factors */}
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Contributing Factors
                  </Typography>
                  {result.contributing_factors?.length > 0 ? (
                    <List>
                      {result.contributing_factors.map((factor, index) => (
                        <ListItem
                          key={index}
                          sx={{
                            bgcolor: 'rgba(148, 163, 184, 0.05)',
                            borderRadius: 1,
                            mb: 1,
                            flexDirection: 'column',
                            alignItems: 'flex-start',
                          }}
                        >
                          <Box sx={{ display: 'flex', width: '100%', alignItems: 'center', mb: 1 }}>
                            <WarningIcon
                              sx={{
                                mr: 1,
                                color: 
                                  factor.severity === 'HIGH' ? 'error.main' :
                                  factor.severity === 'MEDIUM' ? 'warning.main' : 'info.main',
                              }}
                            />
                            <Typography variant="subtitle2" fontWeight={600} sx={{ flex: 1 }}>
                              {factor.rule_name}
                            </Typography>
                            <Chip
                              label={`+${factor.contribution?.toFixed(1)}`}
                              size="small"
                              color={
                                factor.severity === 'HIGH' ? 'error' :
                                factor.severity === 'MEDIUM' ? 'warning' : 'info'
                              }
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            {factor.description}
                          </Typography>
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Alert severity="success">
                      No risk factors detected for this entity.
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <Card sx={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Box sx={{ textAlign: 'center' }}>
                <AssessmentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Select an Entity to Analyze
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Enter entity details or select from high-risk entities list
                </Typography>
              </Box>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default RiskAnalysisPage;
