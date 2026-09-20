import React from 'react';
import { AppBar, Toolbar, Typography, Box, Chip, IconButton } from '@mui/material';
import { AutoAwesome, Menu as MenuIcon } from '@mui/icons-material';
import { useAuth } from '@/context/AuthContext';
import { UserMenu } from './UserMenu';

interface TopBarProps {
  onToggleSidebar?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onToggleSidebar }) => {
  const { userRole, user } = useAuth();

  const getRoleChipColor = () => {
    switch (userRole) {
      case 'ADMIN':
        return { bg: '#fee2e2', color: '#991b1b', border: '#fca5a5' };
      case 'FACULTY':
        return { bg: '#dbeafe', color: '#1e40af', border: '#93c5fd' };
      case 'STUDENT':
        return { bg: '#dcfce7', color: '#166534', border: '#86efac' };
      default:
        return { bg: '#f1f5f9', color: '#475569', border: '#cbd5e1' };
    }
  };

  const chipStyle = getRoleChipColor();

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        backgroundColor: '#0f172a',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', minHeight: 64 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {onToggleSidebar && (
            <IconButton
              color="inherit"
              edge="start"
              onClick={onToggleSidebar}
              sx={{ display: { md: 'none' } }}
            >
              <MenuIcon />
            </IconButton>
          )}

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box
              sx={{
                p: 0.8,
                borderRadius: 2,
                background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                display: 'flex',
              }}
            >
              <AutoAwesome sx={{ color: '#fff', fontSize: 24 }} />
            </Box>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 800,
                fontFamily: 'Outfit',
                letterSpacing: '-0.02em',
                color: '#ffffff',
              }}
            >
              AI ExamGen
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {userRole && (
            <Chip
              label={userRole}
              size="small"
              sx={{
                fontWeight: 700,
                backgroundColor: chipStyle.bg,
                color: chipStyle.color,
                border: `1px solid ${chipStyle.border}`,
                px: 0.5,
              }}
            />
          )}

          <Typography variant="body2" sx={{ color: '#94a3b8', display: { xs: 'none', sm: 'block' } }}>
            {user ? `${user.first_name} ${user.last_name}` : ''}
          </Typography>

          <UserMenu />
        </Box>
      </Toolbar>
    </AppBar>
  );
};
