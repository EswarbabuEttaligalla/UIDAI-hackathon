import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  CircularProgress,
  Tooltip,
  LinearProgress,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Rating,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckIcon,
  ThumbDown as ThumbDownIcon,
  ThumbUp as ThumbUpIcon,
} from '@mui/icons-material';
import { useAlertsStore } from '../store';
import { format } from 'date-fns';
import api from '../services/api';

const getActionTierColor = (tier) => {
  switch (tier) {
    case 'IMMEDIATE_RESPONSE':
      return 'error';
    case 'DEVICE_BLACKLIST':
      return 'error';
    case 'ESCALATE_REGIONAL':
      return 'warning';
    case 'ENHANCED_REVIEW':
      return 'info';
    case 'MONITOR_ONLY':
      return 'success';
    default:
      return 'default';
  }
};

const getActionTierLabel = (tier) => {
  switch (tier) {
    case 'IMMEDIATE_RESPONSE':
      return 'Immediate Response';
    case 'DEVICE_BLACKLIST':
      return 'Device Blacklist';
    case 'ESCALATE_REGIONAL':
      return 'Escalate Regional';
    case 'ENHANCED_REVIEW':
      return 'Enhanced Review';
    case 'MONITOR_ONLY':
      return 'Monitor Only';
    default:
      return tier || 'Unknown';
  }
};

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return 'success';
  if (confidence >= 0.6) return 'warning';
  if (confidence >= 0.4) return 'info';
  return 'error';
};

const getSeverityIcon = (severity) => {
  switch (severity) {
    case 'CRITICAL':
      return <ErrorIcon />;
    case 'HIGH':
      return <WarningIcon />;
    case 'MEDIUM':
      return <InfoIcon />;
    default:
      return <CheckIcon />;
  }
};

const getSeverityColor = (severity) => {
  switch (severity) {
    case 'CRITICAL':
      return 'error';
    case 'HIGH':
      return 'warning';
    case 'MEDIUM':
      return 'info';
    default:
      return 'success';
  }
};

const getStatusColor = (status) => {
  switch (status) {
    case 'ACTIVE':
      return 'error';
    case 'ACKNOWLEDGED':
      return 'warning';
    case 'RESOLVED':
      return 'success';
    default:
      return 'default';
  }
};

const AlertsPage = () => {
  const navigate = useNavigate();
  const {
    alerts,
    totalCount,
    loading,
    statistics,
    filters,
    fetchAlerts,
    fetchStatistics,
    setFilters,
  } = useAlertsStore();

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [feedbackDialog, setFeedbackDialog] = useState(null);
  const [feedbackForm, setFeedbackForm] = useState({
    type: '',
    notes: '',
    confidence: 3
  });
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  const loadData = useCallback(() => {
    fetchAlerts({ limit: rowsPerPage, offset: page * rowsPerPage });
    fetchStatistics();
  }, [fetchAlerts, fetchStatistics, page, rowsPerPage]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleFilterChange = (key, value) => {
    setFilters({ ...filters, [key]: value || null });
    setPage(0);
  };

  const handleOpenFeedback = (alert, type) => {
    setFeedbackDialog(alert);
    setFeedbackForm({
      type,
      notes: '',
      confidence: 3
    });
  };

  const handleCloseFeedback = () => {
    setFeedbackDialog(null);
    setFeedbackForm({ type: '', notes: '', confidence: 3 });
  };

  const handleSubmitFeedback = async () => {
    if (!feedbackDialog) return;

    try {
      await api.post(`/alerts/${feedbackDialog.alert_id}/feedback`, {
        feedback_type: feedbackForm.type,
        feedback_notes: feedbackForm.notes || null,
        analyst_confidence: feedbackForm.confidence / 5.0 // Convert to 0-1 scale
      });

      setSnackbar({
        open: true,
        message: `Feedback submitted: ${feedbackForm.type.replace('_', ' ')}`,
        severity: 'success'
      });

      handleCloseFeedback();
      loadData(); // Refresh alerts
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to submit feedback',
        severity: 'error'
      });
    }
  };

  const handleViewAlert = (alertId) => {
    navigate(`/app/alerts/${alertId}`);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Alert Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Review and manage security alerts
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => {
            fetchAlerts({ limit: rowsPerPage, offset: page * rowsPerPage });
            fetchStatistics();
          }}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="h3" fontWeight={700} color="error.main">
                {statistics?.active_alerts || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active Alerts
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="h3" fontWeight={700} color="error.main">
                {statistics?.critical_alerts || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Critical
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="h3" fontWeight={700} color="warning.main">
                {statistics?.high_alerts || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                High Severity
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 3 }}>
              <Typography variant="h3" fontWeight={700} color="text.primary">
                {totalCount || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Alerts
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={4} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={filters.status || ''}
                  label="Status"
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="ACTIVE">Active</MenuItem>
                  <MenuItem value="ACKNOWLEDGED">Acknowledged</MenuItem>
                  <MenuItem value="RESOLVED">Resolved</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Severity</InputLabel>
                <Select
                  value={filters.severity || ''}
                  label="Severity"
                  onChange={(e) => handleFilterChange('severity', e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="CRITICAL">Critical</MenuItem>
                  <MenuItem value="HIGH">High</MenuItem>
                  <MenuItem value="MEDIUM">Medium</MenuItem>
                  <MenuItem value="LOW">Low</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Alerts Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Severity</TableCell>
                <TableCell>Alert Type</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Region</TableCell>
                <TableCell>Risk Score</TableCell>
                <TableCell>Confidence</TableCell>
                <TableCell>Action Tier</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Time</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={10} align="center" sx={{ py: 4 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : alerts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">No alerts found</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                alerts.map((alert) => (
                  <TableRow
                    key={alert.alert_id}
                    hover
                    sx={{
                      cursor: 'pointer',
                      '&:hover': { bgcolor: 'rgba(148, 163, 184, 0.05)' },
                    }}
                    onClick={() => handleViewAlert(alert.alert_id)}
                  >
                    <TableCell>
                      <Chip
                        icon={getSeverityIcon(alert.severity)}
                        label={alert.severity}
                        color={getSeverityColor(alert.severity)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{alert.alert_type?.replace(/_/g, ' ')}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight={500}>
                        {alert.title}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{alert.affected_region}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        fontWeight={600}
                        color={
                          alert.risk_score >= 80
                            ? 'error.main'
                            : alert.risk_score >= 60
                            ? 'warning.main'
                            : 'text.primary'
                        }
                      >
                        {alert.risk_score?.toFixed(1)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Stack alignItems="flex-start" spacing={0.5}>
                        <LinearProgress
                          variant="determinate"
                          value={(alert.confidence_score || 0) * 100}
                          color={getConfidenceColor(alert.confidence_score || 0)}
                          sx={{ width: 60, height: 4, borderRadius: 2 }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {Math.round((alert.confidence_score || 0) * 100)}%
                        </Typography>
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getActionTierLabel(alert.action_tier)}
                        color={getActionTierColor(alert.action_tier)}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '0.7rem' }}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={alert.status}
                        color={getStatusColor(alert.status)}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption" color="text.secondary">
                        {format(new Date(alert.timestamp), 'MMM dd, HH:mm')}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={0.5}>
                        <Tooltip title="Mark as False Positive">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenFeedback(alert, 'FALSE_POSITIVE');
                            }}
                            disabled={alert.status === 'RESOLVED' || alert.feedback_type}
                          >
                            <ThumbDownIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Confirm Threat">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenFeedback(alert, 'CONFIRMED_THREAT');
                            }}
                            disabled={alert.status === 'RESOLVED' || alert.feedback_type}
                          >
                            <ThumbUpIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleViewAlert(alert.alert_id);
                            }}
                          >
                            <ViewIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={totalCount}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </Card>

      {/* Feedback Dialog */}
      <Dialog open={!!feedbackDialog} onClose={handleCloseFeedback} maxWidth="sm" fullWidth>
        <DialogTitle>
          Submit Alert Feedback
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ pt: 1 }}>
            <Alert severity="info">
              <Typography variant="body2">
                Your feedback helps improve detection accuracy. The system will learn from this input
                to adjust sensitivity for similar patterns in the future.
              </Typography>
            </Alert>
            
            {feedbackDialog && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Alert: {feedbackDialog.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Risk Score: {feedbackDialog.risk_score?.toFixed(1)} | 
                  Confidence: {Math.round((feedbackDialog.confidence_score || 0) * 100)}%
                </Typography>
              </Box>
            )}

            <FormControl fullWidth>
              <InputLabel>Feedback Type</InputLabel>
              <Select
                value={feedbackForm.type}
                label="Feedback Type"
                onChange={(e) => setFeedbackForm({ ...feedbackForm, type: e.target.value })}
              >
                <MenuItem value="FALSE_POSITIVE">False Positive</MenuItem>
                <MenuItem value="CONFIRMED_THREAT">Confirmed Threat</MenuItem>
                <MenuItem value="PARTIALLY_RELEVANT">Partially Relevant</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Additional Notes (Optional)"
              multiline
              rows={3}
              fullWidth
              value={feedbackForm.notes}
              onChange={(e) => setFeedbackForm({ ...feedbackForm, notes: e.target.value })}
              placeholder="Provide context or additional details about your assessment..."
            />

            <Box>
              <Typography component="legend" variant="body2" gutterBottom>
                Your confidence in this assessment:
              </Typography>
              <Rating
                value={feedbackForm.confidence}
                onChange={(event, newValue) => {
                  setFeedbackForm({ ...feedbackForm, confidence: newValue });
                }}
                max={5}
                size="large"
              />
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseFeedback}>Cancel</Button>
          <Button 
            onClick={handleSubmitFeedback} 
            variant="contained"
            disabled={!feedbackForm.type}
          >
            Submit Feedback
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setSnackbar({ ...snackbar, open: false })} 
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AlertsPage;
