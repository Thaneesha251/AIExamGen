import React, { useState } from 'react';
import {
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Typography,
  Divider,
  ListItemIcon,
  Box,
} from '@mui/material';
import { AccountCircle, Logout, Person } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

export const UserMenu: React.FC = () => {
  const { user, userRole, logout } = useAuth();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleProfile = () => {
    handleClose();
    navigate('/profile');
  };

  const handleLogout = async () => {
    handleClose();
    await logout();
    navigate('/login');
  };

  const initials = user
    ? `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
    : 'U';

  return (
    <>
      <IconButton onClick={handleOpen} size="small" sx={{ ml: 1 }}>
        <Avatar
          sx={{
            width: 40,
            height: 40,
            bgcolor: '#2563eb',
            fontSize: '1rem',
            fontWeight: 700,
            border: '2px solid rgba(255, 255, 255, 0.2)',
          }}
        >
          {initials}
        </Avatar>
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        PaperProps={{
          elevation: 4,
          sx: {
            mt: 1.5,
            width: 220,
            borderRadius: 3,
            border: '1px solid #e2e8f0',
            p: 1,
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0f172a' }}>
            {user ? `${user.first_name} ${user.last_name}` : 'User'}
          </Typography>
          <Typography variant="caption" sx={{ color: '#64748b' }}>
            {user?.email}
          </Typography>
          <Typography
            variant="caption"
            sx={{
              display: 'block',
              mt: 0.5,
              fontWeight: 700,
              color: userRole === 'ADMIN' ? '#dc2626' : userRole === 'FACULTY' ? '#2563eb' : '#16a34a',
            }}
          >
            Role: {userRole}
          </Typography>
        </Box>
        <Divider sx={{ my: 1 }} />
        <MenuItem onClick={handleProfile} sx={{ borderRadius: 2 }}>
          <ListItemIcon>
            <Person fontSize="small" sx={{ color: '#2563eb' }} />
          </ListItemIcon>
          My Profile
        </MenuItem>
        <MenuItem onClick={handleLogout} sx={{ borderRadius: 2, color: '#dc2626' }}>
          <ListItemIcon>
            <Logout fontSize="small" sx={{ color: '#dc2626' }} />
          </ListItemIcon>
          Logout
        </MenuItem>
      </Menu>
    </>
  );
};
