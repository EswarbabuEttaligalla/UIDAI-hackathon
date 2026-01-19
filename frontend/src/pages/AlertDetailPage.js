import React, { useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Grid,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  IconButton,
  Alert,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckIcon,
  Rule as RuleIcon,
  Lightbulb as ActionIcon,
  Timeline as TimelineIcon,
  LocationOn as LocationIcon,
  Category as CategoryIcon,
  AccessTime as TimeIcon,
} from '@mui/icons-material';
import { useAlertsStore } from '../store';
import { format } from 'date-fns';

const getSeverityColor = (severity) => {
  switch (severity) {
    case 'CRITICAL': return 'error';
    case 'HIGH': return 'warning';
    case 'MEDIUM': return 'info';
    default: return 'success';
  }
};

const getSeverityIcon = (severity) => {
  switch (severity) {
    case 'CRITICAL': return <ErrorIcon />;
    case 'HIGH': return <WarningIcon />;
    case 'MEDIUM': return <InfoIcon />;
    default: return <CheckIcon />;
  }
};

const AlertDetailPage = () => {
  const { alertId } = useParams();
  const navigate = useNavigate();
  const { selectedAlert, loading, fetchAlertById, updateAlertStatus, clearSelectedAlert } = useAlertsStore();

  const loadAlert = useCallback(() => {
    if (alertId) {
      fetchAlertById(alertId);
    }
  }, [alertId, fetchAlertById]);

  useEffect(() => {
    loadAlert();
    return () => clearSelectedAlert();
  }, [loadAlert, clearSelectedAlert]);

  const handleStatusUpdate = async (newStatus) => {
    await updateAlertStatus(alertId, newStatus);
    fetchAlertById(alertId);
  };

  if (loading || !selectedAlert) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  const alert = selectedAlert;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, gap: 2 }}>
        <IconButton onClick={() => navigate('/app/alerts')}>
          <BackIcon />
        </IconButton>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" fontWeight={700}>
            Alert Details
          </Typography>
          <Typography variant="body2" color="text.secondary">
            ID: {alert.alert_id}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {alert.status === 'ACTIVE' && (
            <Button
              variant="outlined"
              color="warning"
              onClick={() => handleStatusUpdate('ACKNOWLEDGED')}
            >
              Acknowledge
            </Button>
          )}
          {alert.status !== 'RESOLVED' && (
            <Button
              variant="contained"
              color="success"
              onClick={() => handleStatusUpdate('RESOLVED')}
            >
              Mark Resolved
            </Button>
          )}
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Main Info */}
        <Grid item xs={12} lg={8}>
          {/* Alert Overview */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Box
                  sx={{
                    width: 56,
                    height: 56,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: `${getSeverityColor(alert.severity)}.main`,
                    opacity: 0.9,
                  }}
                >
                  {getSeverityIcon(alert.severity)}
                </Box>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h5" fontWeight={600}>
                    {alert.title}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                    <Chip
                      label={alert.severity}
                      color={getSeverityColor(alert.severity)}
                      size="small"
                    />
                    <Chip
                      label={alert.status}
                      variant="outlined"
                      size="small"
                    />
                    <Chip
                      label={alert.alert_type}
                      variant="outlined"
                      size="small"
                    />
                  </Box>
                </Box>
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="h3" fontWeight={700} color={getSeverityColor(alert.severity) + '.main'}>
                    {alert.risk_score?.toFixed(1)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Risk Score
                  </Typography>
                </Box>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                Description
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ whiteSpace: 'pre-line', fontFamily: 'monospace', bgcolor: 'rgba(0,0,0,0.2)', p: 2, borderRadius: 1 }}
              >
                {alert.description}
              </Typography>
            </CardContent>
          </Card>

          {/* Rule Analysis */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <RuleIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Rules Triggered
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                The following rule-based checks contributed to this alert:
              </Typography>
              <List>
                {alert.reason_codes?.map((code, index) => (
                  <ListItem
                    key={index}
                    sx={{
                      bgcolor: 'rgba(148, 163, 184, 0.05)',
                      borderRadius: 1,
                      mb: 1,
                    }}
                  >
                    <ListItemIcon>
                      <WarningIcon color="warning" />
                    </ListItemIcon>
                    <ListItemText
                      primary={code}
                      secondary={getRuleDescription(code)}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* Suggested Actions */}
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <ActionIcon color="success" />
                <Typography variant="h6" fontWeight={600}>
                  Suggested Actions
                </Typography>
              </Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                These recommendations are based on the detected patterns and historical analysis.
              </Alert>
              <List>
                {alert.suggested_actions?.map((action, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <CheckIcon color="success" />
                    </ListItemIcon>
                    <ListItemText primary={action} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Side Panel */}
        <Grid item xs={12} lg={4}>
          {/* Alert Metadata */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Alert Information
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <TimeIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Created"
                    secondary={format(new Date(alert.timestamp), 'PPpp')}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <LocationIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Affected Region"
                    secondary={alert.affected_region || 'Multiple'}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CategoryIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Service Category"
                    secondary={alert.service_category || 'All Categories'}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>

          {/* Risk Score Breakdown */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Risk Score Breakdown
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Composite Score
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {alert.risk_score?.toFixed(1)}
                  </Typography>
                </Box>
                <Box
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    bgcolor: 'rgba(148, 163, 184, 0.2)',
                    overflow: 'hidden',
                  }}
                >
                  <Box
                    sx={{
                      height: '100%',
                      width: `${alert.risk_score}%`,
                      bgcolor: getSeverityColor(alert.severity) + '.main',
                      borderRadius: 4,
                    }}
                  />
                </Box>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                How This Score Was Calculated
              </Typography>
              <Typography variant="body2" color="text.secondary">
                The risk score combines rule-based analysis (60% weight) and ML anomaly detection (40% weight).
                Each triggered rule contributes to the final score based on its severity and confidence.
              </Typography>
            </CardContent>
          </Card>

          {/* Status History */}
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Status Timeline
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <TimelineIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Alert Created"
                    secondary={format(new Date(alert.timestamp), 'PPpp')}
                  />
                </ListItem>
                {alert.acknowledged_at && (
                  <ListItem>
                    <ListItemIcon>
                      <TimelineIcon color="warning" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Acknowledged"
                      secondary={`${format(new Date(alert.acknowledged_at), 'PPpp')} by ${alert.acknowledged_by || 'System'}`}
                    />
                  </ListItem>
                )}
                {alert.resolved_at && (
                  <ListItem>
                    <ListItemIcon>
                      <TimelineIcon color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Resolved"
                      secondary={format(new Date(alert.resolved_at), 'PPpp')}
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

// Helper function to get rule descriptions
const getRuleDescription = (ruleCode) => {
  const descriptions = {
    'HIGH_AUTH_FREQUENCY': 'Detected unusually high number of authentication attempts from a single entity.',
    'GEOGRAPHIC_VELOCITY_ANOMALY': 'Authentication requests from multiple geographic locations in a short time period.',
    'OTP_FALLBACK_ABUSE': 'Excessive use of OTP as fallback authentication method, potentially indicating biometric bypass attempts.',
    'ABNORMAL_RETRY_PATTERN': 'Multiple failed authentication attempts followed by retries, suggesting potential brute force behavior.',
    'OFF_HOURS_ACTIVITY': 'Significant authentication activity during non-business hours (11 PM - 5 AM).',
    'HIGH_FAILURE_RATE': 'Abnormally high rate of failed authentication attempts.',
    'SESSION_DURATION_ANOMALY': 'Session durations significantly different from normal patterns.',
    'ML_ANOMALY_DETECTED': 'Machine learning model flagged this pattern as anomalous based on historical behavior.',
  };
  return descriptions[ruleCode] || 'Rule-based detection triggered for suspicious pattern.';
};

export default AlertDetailPage;
