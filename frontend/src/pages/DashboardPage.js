import React, { useEffect, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Refresh as RefreshIcon,
  Security as SecurityIcon,
  DevicesOther as DevicesIcon,
} from '@mui/icons-material';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from 'recharts';
import { useDashboardStore, useAlertsStore } from '../store';

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899'];

const StatCard = ({ title, value, subtitle, icon, trend, color = 'primary' }) => {
  const trendPositive = trend >= 0;
  
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h3" fontWeight={700} color={`${color}.main`}>
              {typeof value === 'number' ? value.toLocaleString() : value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 2,
              backgroundColor: `${color}.main`,
              opacity: 0.15,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Box
              sx={{
                position: 'absolute',
                color: `${color}.main`,
              }}
            >
              {icon}
            </Box>
          </Box>
        </Box>
        {trend !== undefined && (
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 2, gap: 0.5 }}>
            {trendPositive ? (
              <TrendingUpIcon sx={{ fontSize: 18, color: 'success.main' }} />
            ) : (
              <TrendingDownIcon sx={{ fontSize: 18, color: 'error.main' }} />
            )}
            <Typography
              variant="body2"
              color={trendPositive ? 'success.main' : 'error.main'}
              fontWeight={500}
            >
              {Math.abs(trend).toFixed(1)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              vs last period
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

const RegionHeatmap = ({ regions }) => {
  if (!regions || regions.length === 0) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography color="text.secondary">No region data available</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Grid container spacing={1}>
        {regions.slice(0, 12).map((region) => {
          const getRiskColor = (score) => {
            if (score >= 70) return '#ef4444';
            if (score >= 50) return '#f59e0b';
            if (score >= 30) return '#3b82f6';
            return '#10b981';
          };
          
          return (
            <Grid item xs={6} sm={4} md={3} key={region.state_code}>
              <Box
                sx={{
                  p: 2,
                  borderRadius: 2,
                  backgroundColor: 'rgba(148, 163, 184, 0.05)',
                  border: `2px solid ${getRiskColor(region.risk_score)}`,
                  textAlign: 'center',
                }}
              >
                <Typography variant="subtitle2" fontWeight={600}>
                  {region.state_name || region.state_code}
                </Typography>
                <Typography
                  variant="h5"
                  fontWeight={700}
                  sx={{ color: getRiskColor(region.risk_score), my: 1 }}
                >
                  {Math.round(region.risk_score)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {region.event_count} events
                </Typography>
              </Box>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
};

const DashboardPage = () => {
  const { metrics, regions, loading, refreshAll } = useDashboardStore();
  const { fetchStatistics } = useAlertsStore();

  const handleRefresh = useCallback(() => {
    refreshAll();
    fetchStatistics();
  }, [refreshAll, fetchStatistics]);

  useEffect(() => {
    handleRefresh();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      handleRefresh();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [handleRefresh]);

  if (loading && !metrics) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  const eventsByHour = metrics?.events_by_hour?.map(item => ({
    hour: `${item.hour}:00`,
    events: item.count,
  })) || [];

  const authTypeData = metrics?.auth_type_distribution?.map(item => ({
    name: item.type,
    value: item.count,
  })) || [];

  const serviceData = metrics?.events_by_service?.map(item => ({
    name: item.service,
    events: item.count,
  })) || [];

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Risk Overview
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time monitoring of authentication patterns
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip
            icon={<SecurityIcon />}
            label="System Active"
            color="success"
            variant="outlined"
          />
          <Tooltip title="Refresh Data">
            <span>
              <IconButton onClick={refreshAll} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Box>

      {/* Stats Grid */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="Events Today"
            value={metrics?.total_events_today || 0}
            subtitle="Authentication events"
            icon={<DevicesIcon />}
            trend={metrics?.trend_percentage}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="Active Alerts"
            value={metrics?.active_alerts || 0}
            subtitle="Requiring attention"
            icon={<WarningIcon />}
            color={metrics?.active_alerts > 0 ? 'warning' : 'success'}
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="High Risk Events"
            value={metrics?.high_risk_events || 0}
            subtitle="Flagged for review"
            icon={<WarningIcon />}
            color="error"
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <StatCard
            title="Critical Alerts"
            value={metrics?.critical_alerts || 0}
            subtitle="Immediate action needed"
            icon={<WarningIcon />}
            color={metrics?.critical_alerts > 0 ? 'error' : 'success'}
          />
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Events Trend */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Authentication Events (24 Hours)
              </Typography>
              <ResponsiveContainer width="100%" height={320}>
                <AreaChart data={eventsByHour}>
                  <defs>
                    <linearGradient id="colorEvents" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                  <XAxis 
                    dataKey="hour" 
                    stroke="#94a3b8"
                    fontSize={12}
                  />
                  <YAxis 
                    stroke="#94a3b8"
                    fontSize={12}
                  />
                  <ChartTooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid rgba(148, 163, 184, 0.2)',
                      borderRadius: 8,
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="events"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorEvents)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Auth Type Distribution */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Authentication Methods
              </Typography>
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie
                    data={authTypeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {authTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <ChartTooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid rgba(148, 163, 184, 0.2)',
                      borderRadius: 8,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Bottom Row */}
      <Grid container spacing={3}>
        {/* Service Category Chart */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Events by Service Category
              </Typography>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={serviceData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                  <XAxis type="number" stroke="#94a3b8" fontSize={12} />
                  <YAxis 
                    type="category" 
                    dataKey="name" 
                    stroke="#94a3b8" 
                    fontSize={12}
                    width={100}
                  />
                  <ChartTooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid rgba(148, 163, 184, 0.2)',
                      borderRadius: 8,
                    }}
                  />
                  <Bar dataKey="events" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Region Heatmap */}
        <Grid item xs={12} lg={6}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight={600}>
                  Region Risk Heatmap
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip label="Low" size="small" sx={{ bgcolor: '#10b981', color: 'white' }} />
                  <Chip label="Medium" size="small" sx={{ bgcolor: '#3b82f6', color: 'white' }} />
                  <Chip label="High" size="small" sx={{ bgcolor: '#f59e0b', color: 'white' }} />
                  <Chip label="Critical" size="small" sx={{ bgcolor: '#ef4444', color: 'white' }} />
                </Box>
              </Box>
              <RegionHeatmap regions={regions} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;
