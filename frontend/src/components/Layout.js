import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  Chip,
  Alert,
  AlertTitle,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Warning as AlertIcon,
  Security as SecurityIcon,
  PlayCircle as SimulationIcon,
  Policy as GovernanceIcon,
  Assessment as AnalysisIcon,
  Menu as MenuIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  Shield as ShieldIcon,
  School as SchoolIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useAuthStore } from '../store';
import api from '../services/api';

const drawerWidth = 280;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/app/dashboard' },
  { text: 'Alerts', icon: <AlertIcon />, path: '/app/alerts' },
  { text: 'Risk Analysis', icon: <AnalysisIcon />, path: '/app/risk-analysis' },
  { text: 'Simulation', icon: <SimulationIcon />, path: '/app/simulation' },
  { text: 'Governance', icon: <GovernanceIcon />, path: '/app/governance' },
];

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [baselineStatus, setBaselineStatus] = useState(null);

  // Fetch baseline status
  useEffect(() => {
    const fetchBaselineStatus = async () => {
      try {
        const response = await api.get('/api/baseline/status');
        setBaselineStatus(response.data);
      } catch (error) {
        console.error('Failed to fetch baseline status:', error);
      }
    };
    
    fetchBaselineStatus();
    // Refresh baseline status every 30 seconds
    const interval = setInterval(fetchBaselineStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Logo Section */}
      <Box
        sx={{
          p: 3,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
        }}
      >
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: 2,
            background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <ShieldIcon sx={{ color: 'white', fontSize: 28 }} />
        </Box>
        <Box>
          <Typography variant="h6" fontWeight={700} color="white">
            AMEWS
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Early Warning System
          </Typography>
        </Box>
      </Box>

      {/* System Status Banner */}
      {baselineStatus && (
        <Box sx={{ p: 2 }}>
          <Alert 
            severity={baselineStatus.system_mode === 'BASELINE_LEARNING' ? 'info' : 'success'}
            icon={baselineStatus.system_mode === 'BASELINE_LEARNING' ? <SchoolIcon /> : <CheckCircleIcon />}
            sx={{ 
              borderRadius: 2,
              fontSize: '0.8rem',
              '& .MuiAlert-message': { 
                overflow: 'hidden' 
              }
            }}
          >
            <AlertTitle sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
              {baselineStatus.system_mode === 'BASELINE_LEARNING' ? 'Baseline Mode' : 'Active Monitoring'}
            </AlertTitle>
            {baselineStatus.system_mode === 'BASELINE_LEARNING' ? (
              <>
                Learning patterns: {Math.round(baselineStatus.completion_percentage)}% complete
                <br />
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  Alerts disabled during learning phase
                </Typography>
              </>
            ) : (
              <>
                Live monitoring active
                <br />
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  Baseline established • {baselineStatus.regions_covered?.length || 0} regions covered
                </Typography>
              </>
            )}
          </Alert>
        </Box>
      )}

      {/* Navigation */}
      <List sx={{ flex: 1, px: 2, py: 3 }}>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path || 
                          (item.path !== '/dashboard' && location.pathname.startsWith(item.path));
          return (
            <ListItem key={item.text} disablePadding sx={{ mb: 1 }}>
              <ListItemButton
                onClick={() => {
                  navigate(item.path);
                  setMobileOpen(false);
                }}
                sx={{
                  borderRadius: 2,
                  py: 1.5,
                  backgroundColor: isActive ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                  borderLeft: isActive ? '3px solid #3b82f6' : '3px solid transparent',
                  '&:hover': {
                    backgroundColor: isActive 
                      ? 'rgba(59, 130, 246, 0.2)' 
                      : 'rgba(148, 163, 184, 0.08)',
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    color: isActive ? '#3b82f6' : 'text.secondary',
                    minWidth: 44,
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.text}
                  primaryTypographyProps={{
                    fontWeight: isActive ? 600 : 400,
                    color: isActive ? '#3b82f6' : 'text.primary',
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      {/* User Info */}
      <Box sx={{ p: 2, borderTop: '1px solid rgba(148, 163, 184, 0.1)' }}>
        <Box
          sx={{
            p: 2,
            borderRadius: 2,
            backgroundColor: 'rgba(148, 163, 184, 0.05)',
            display: 'flex',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <Avatar
            sx={{
              width: 40,
              height: 40,
              bgcolor: 'primary.main',
            }}
          >
            {user?.full_name?.charAt(0) || 'U'}
          </Avatar>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="body2" fontWeight={500} noWrap>
              {user?.full_name || 'User'}
            </Typography>
            <Chip
              label={user?.role || 'VIEWER'}
              size="small"
              sx={{
                height: 20,
                fontSize: '0.65rem',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                color: '#3b82f6',
              }}
            />
          </Box>
        </Box>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* AppBar */}
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          bgcolor: 'background.paper',
          borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
          boxShadow: 'none',
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton
              color="inherit"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ display: { md: 'none' } }}
            >
              <MenuIcon />
            </IconButton>
            <Box>
              <Typography variant="h6" color="text.primary" fontWeight={600}>
                {menuItems.find(item => 
                  location.pathname === item.path || 
                  (item.path !== '/dashboard' && location.pathname.startsWith(item.path))
                )?.text || 'Dashboard'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                UIDAI Authority Console
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip
              icon={<SecurityIcon sx={{ fontSize: 16 }} />}
              label="Secure Session"
              size="small"
              sx={{
                backgroundColor: 'rgba(16, 185, 129, 0.15)',
                color: '#10b981',
                '& .MuiChip-icon': { color: '#10b981' },
              }}
            />
            <IconButton onClick={handleMenuClick}>
              <Avatar sx={{ width: 36, height: 36, bgcolor: 'primary.main' }}>
                {user?.full_name?.charAt(0) || 'U'}
              </Avatar>
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
              PaperProps={{
                sx: {
                  mt: 1.5,
                  minWidth: 200,
                  bgcolor: 'background.paper',
                  border: '1px solid rgba(148, 163, 184, 0.1)',
                },
              }}
            >
              <Box sx={{ px: 2, py: 1.5 }}>
                <Typography variant="subtitle2">{user?.full_name}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {user?.department}
                </Typography>
              </Box>
              <Divider />
              <MenuItem onClick={handleMenuClose}>
                <ListItemIcon>
                  <PersonIcon fontSize="small" />
                </ListItemIcon>
                Profile
              </MenuItem>
              <MenuItem onClick={handleLogout}>
                <ListItemIcon>
                  <LogoutIcon fontSize="small" />
                </ListItemIcon>
                Logout
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Drawer */}
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              bgcolor: 'background.paper',
              borderRight: '1px solid rgba(148, 163, 184, 0.1)',
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              bgcolor: 'background.paper',
              borderRight: '1px solid rgba(148, 163, 184, 0.1)',
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
          minHeight: 'calc(100vh - 64px)',
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
};

export default Layout;
