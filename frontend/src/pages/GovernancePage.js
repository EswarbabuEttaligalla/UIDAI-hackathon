import React, { useEffect, useCallback, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Divider,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Security as SecurityIcon,
  VerifiedUser as VerifiedIcon,
  Policy as PolicyIcon,
  Lock as LockIcon,
  Storage as StorageIcon,
  Visibility as VisibilityIcon,
  Shield as ShieldIcon,
  FolderOpen as FolderIcon,
  Public as PublicIcon,
} from '@mui/icons-material';
import { useGovernanceStore, useAuthStore } from '../store';
import { datasetAPI } from '../services/api';
import { format } from 'date-fns';

const GovernancePage = () => {
  const { privacyInfo, auditLogs, loading, fetchPrivacyInfo, fetchAuditLogs } = useGovernanceStore();
  const { user } = useAuthStore();
  const [datasetInfo, setDatasetInfo] = useState(null);
  const [loadingDataset, setLoadingDataset] = useState(false);

  const loadData = useCallback(() => {
    fetchPrivacyInfo();
    if (user?.role === 'ADMIN') {
      fetchAuditLogs(50);
    }
    
    // Load dataset information
    setLoadingDataset(true);
    datasetAPI.getInfo()
      .then(data => {
        setDatasetInfo(data);
      })
      .catch(err => {
        console.error('Error loading dataset info:', err);
      })
      .finally(() => {
        setLoadingDataset(false);
      });
  }, [fetchPrivacyInfo, fetchAuditLogs, user]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading && !privacyInfo) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>
          Privacy & Governance
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Transparency in data handling and system operations
        </Typography>
      </Box>

      {/* Privacy Statement */}
      <Alert
        severity="success"
        icon={<ShieldIcon />}
        sx={{ mb: 3 }}
      >
        <Typography variant="body1" fontWeight={500}>
          AMEWS operates on the principle of Privacy by Design
        </Typography>
        <Typography variant="body2">
          This system processes only synthetic authentication metadata. No real Aadhaar numbers,
          biometrics, or personally identifiable information is collected, stored, or processed.
        </Typography>
      </Alert>

      <Grid container spacing={3}>
        {/* Data Not Collected */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <CancelIcon color="error" />
                <Typography variant="h6" fontWeight={600}>
                  Data NOT Collected
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                The following sensitive data is explicitly excluded from this system:
              </Typography>
              <List dense>
                {privacyInfo?.data_not_collected?.map((item, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <CancelIcon color="error" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={item} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Anonymization Methods */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <LockIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Anonymization Methods
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                How we protect data identity:
              </Typography>
              <List dense>
                {privacyInfo?.anonymization_methods?.map((method, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <CheckIcon color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={method} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Aggregation Rules */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <VisibilityIcon color="info" />
                <Typography variant="h6" fontWeight={600}>
                  Aggregation Rules
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Data is presented only in aggregate form:
              </Typography>
              <List dense>
                {privacyInfo?.aggregation_rules?.map((rule, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <CheckIcon color="info" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={rule} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Compliance Standards */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <VerifiedIcon color="success" />
                <Typography variant="h6" fontWeight={600}>
                  Compliance Standards
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                This system adheres to:
              </Typography>
              <List dense>
                {privacyInfo?.compliance_standards?.map((standard, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <VerifiedIcon color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={standard} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Dataset Information */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <FolderIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Training Dataset Information
                </Typography>
                {datasetInfo?.loaded && (
                  <Chip label="Loaded" size="small" color="success" />
                )}
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                AMEWS is trained on synthetically generated datasets based on realistic Indian 
                demographic and enrolment patterns. This ensures accurate pattern recognition 
                without compromising real citizen data.
              </Typography>
              
              {loadingDataset ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              ) : datasetInfo ? (
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <Box sx={{ p: 3, bgcolor: 'rgba(59, 130, 246, 0.05)', borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700} color="primary">
                        {datasetInfo.demographic_records?.toLocaleString() || '0'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        Demographic Records
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        State, district, age, gender distribution patterns
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Box sx={{ p: 3, bgcolor: 'rgba(139, 92, 246, 0.05)', borderRadius: 2, textAlign: 'center' }}>
                      <Typography variant="h4" fontWeight={700} color="secondary">
                        {datasetInfo.enrolment_records?.toLocaleString() || '0'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        Enrolment Records
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Authentication patterns, device info, regional trends
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Box sx={{ p: 3, bgcolor: 'rgba(16, 185, 129, 0.05)', borderRadius: 2, textAlign: 'center' }}>
                      <PublicIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                      <Typography variant="h4" fontWeight={700} color="success.main">
                        {datasetInfo.stats?.unique_states || '36'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        States & UTs Covered
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Pan-India coverage including all regions
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12}>
                    <Divider sx={{ my: 2 }} />
                    <Alert severity="info" icon={<FolderIcon />}>
                      <Typography variant="body2" fontWeight={500} gutterBottom>
                        Dataset Source Files
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        • <strong>api_data_aadhar_demographic.zip</strong> - Synthetic demographic distribution data (2M+ records)<br />
                        • <strong>api_data_aadhar_enrolment.zip</strong> - Synthetic enrolment and authentication patterns (1M+ records)<br />
                        • <strong>api_data_aadhar_biometric.zip</strong> - Biometric fallback analysis patterns<br />
                        <br />
                        All datasets are synthetically generated and contain <strong>NO real Aadhaar numbers, biometrics, or PII</strong>.
                        These files serve as proof of realistic training data for ML model accuracy.
                      </Typography>
                    </Alert>
                  </Grid>
                </Grid>
              ) : (
                <Alert severity="warning">
                  Dataset information not available
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Data Retention Policy */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <StorageIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  Data Retention Policy
                </Typography>
              </Box>
              <Typography variant="body1">
                {privacyInfo?.data_retention_policy}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* System Architecture Info */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <SecurityIcon color="primary" />
                <Typography variant="h6" fontWeight={600}>
                  System Architecture & Trust
                </Typography>
              </Box>
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Box sx={{ p: 2, bgcolor: 'rgba(59, 130, 246, 0.1)', borderRadius: 2 }}>
                    <Typography variant="subtitle2" color="primary" gutterBottom>
                      Post-Authentication Layer
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      AMEWS operates at the behavior analysis layer, completely separate from
                      UIDAI core authentication systems. It has no access to authentication
                      infrastructure or biometric data.
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Box sx={{ p: 2, bgcolor: 'rgba(16, 185, 129, 0.1)', borderRadius: 2 }}>
                    <Typography variant="subtitle2" color="success.main" gutterBottom>
                      Synthetic Data Only
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      All data used in this system is synthetically generated for testing purposes.
                      No real Aadhaar transaction data is used. Models are trained on realistic
                      Indian demographic and enrolment patterns.
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Box sx={{ p: 2, bgcolor: 'rgba(139, 92, 246, 0.1)', borderRadius: 2 }}>
                    <Typography variant="subtitle2" color="secondary" gutterBottom>
                      Complementary System
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      AMEWS is designed to complement UIDAI's existing security measures by
                      providing an additional layer of behavioral pattern analysis.
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Audit Logs (Admin Only) */}
        {user?.role === 'ADMIN' && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <PolicyIcon color="primary" />
                  <Typography variant="h6" fontWeight={600}>
                    Audit Logs
                  </Typography>
                  <Chip label="Admin Only" size="small" color="primary" />
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  All system actions are logged for accountability and transparency.
                </Typography>
                {auditLogs.length > 0 ? (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Timestamp</TableCell>
                          <TableCell>Action</TableCell>
                          <TableCell>Endpoint</TableCell>
                          <TableCell>User</TableCell>
                          <TableCell>Status</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {auditLogs.slice(0, 10).map((log) => (
                          <TableRow key={log.log_id}>
                            <TableCell>
                              <Typography variant="caption">
                                {format(new Date(log.timestamp), 'MMM dd, HH:mm:ss')}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip label={log.action} size="small" variant="outlined" />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                                {log.endpoint}
                              </Typography>
                            </TableCell>
                            <TableCell>{log.user_id}</TableCell>
                            <TableCell>
                              <Chip
                                label={log.response_status}
                                size="small"
                                color={log.response_status === 200 ? 'success' : 'error'}
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No audit logs available.
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default GovernancePage;
