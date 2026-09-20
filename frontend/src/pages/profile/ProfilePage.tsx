import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  TextField,
  Button,
  Avatar,
  Chip,
  Stack,
  Divider,
  Alert,
  Snackbar,
  Paper,
} from '@mui/material';
import { Person, Lock, Badge, Email, School, Work } from '@mui/icons-material';
import { PageContainer } from '@/components/layout/PageContainer';
import { useAuth } from '@/context/AuthContext';
import { authService } from '@/services/authService';

export const ProfilePage: React.FC = () => {
  const { user, userRole, updateProfile } = useAuth();

  // Profile Edit State
  const [firstName, setFirstName] = useState(user?.first_name || '');
  const [lastName, setLastName] = useState(user?.last_name || '');
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);

  // Password Change State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPass, setIsChangingPass] = useState(false);

  // Feedback
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!firstName.trim() || !lastName.trim()) {
      setSnackbar({ open: true, message: 'First name and last name cannot be empty', severity: 'error' });
      return;
    }
    setIsUpdatingProfile(true);
    try {
      await updateProfile({ first_name: firstName, last_name: lastName });
      setSnackbar({ open: true, message: 'Profile updated successfully!', severity: 'success' });
    } catch (err: any) {
      setSnackbar({ open: true, message: err.message || 'Failed to update profile', severity: 'error' });
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword || !newPassword) {
      setSnackbar({ open: true, message: 'Please complete all password fields', severity: 'error' });
      return;
    }
    if (newPassword.length < 8) {
      setSnackbar({ open: true, message: 'New password must be at least 8 characters', severity: 'error' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setSnackbar({ open: true, message: 'New passwords do not match', severity: 'error' });
      return;
    }

    setIsChangingPass(true);
    try {
      await authService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSnackbar({ open: true, message: 'Password changed successfully!', severity: 'success' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setSnackbar({ open: true, message: err.message || 'Failed to change password', severity: 'error' });
    } finally {
      setIsChangingPass(false);
    }
  };

  const initials = user ? `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase() : 'U';

  return (
    <PageContainer
      title="User Profile & Security Settings"
      subtitle="View account identity details, edit personal information, and update authentication password"
    >
      <Grid container spacing={4}>
        {/* Left Column: Account Identity Card */}
        <Grid item xs={12} md={4}>
          <Card elevation={0} sx={{ border: '1px solid #e2e8f0', borderRadius: 3, p: 3, textAlign: 'center' }}>
            <Avatar
              sx={{
                width: 84,
                height: 84,
                mx: 'auto',
                mb: 2,
                bgcolor: '#2563eb',
                fontSize: '2.2rem',
                fontWeight: 800,
                boxShadow: '0 10px 25px -5px rgba(37, 99, 235, 0.4)',
              }}
            >
              {initials}
            </Avatar>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#0f172a' }}>
              {user?.first_name} {user?.last_name}
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748b', mb: 2 }}>
              {user?.email}
            </Typography>

            <Chip
              label={userRole || 'USER'}
              color={userRole === 'ADMIN' ? 'error' : userRole === 'FACULTY' ? 'primary' : 'success'}
              sx={{ fontWeight: 800, px: 1, mb: 3 }}
            />

            <Divider sx={{ my: 2 }} />

            <Stack spacing={2} textAlign="left">
              <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2 }}>
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Email sx={{ color: '#2563eb' }} />
                  <Box>
                    <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 600, display: 'block' }}>
                      Email Address
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 700, color: '#0f172a' }}>
                      {user?.email}
                    </Typography>
                  </Box>
                </Stack>
              </Paper>

              {user?.registration_number && (
                <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2 }}>
                  <Stack direction="row" spacing={1.5} alignItems="center">
                    <Badge sx={{ color: '#16a34a' }} />
                    <Box>
                      <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 600, display: 'block' }}>
                        Registration Number
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 700, color: '#0f172a', fontFamily: 'monospace' }}>
                        {user.registration_number}
                      </Typography>
                    </Box>
                  </Stack>
                </Paper>
              )}

              {user?.employee_id && (
                <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2 }}>
                  <Stack direction="row" spacing={1.5} alignItems="center">
                    <Work sx={{ color: '#7c3aed' }} />
                    <Box>
                      <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 600, display: 'block' }}>
                        Employee ID
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 700, color: '#0f172a', fontFamily: 'monospace' }}>
                        {user.employee_id}
                      </Typography>
                    </Box>
                  </Stack>
                </Paper>
              )}
            </Stack>
          </Card>
        </Grid>

        {/* Right Column: Edit Forms */}
        <Grid item xs={12} md={8}>
          <Stack spacing={4}>
            {/* Profile Information Form */}
            <Card elevation={0} sx={{ border: '1px solid #e2e8f0', borderRadius: 3, p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1, color: '#0f172a' }}>
                Personal Information
              </Typography>
              <Typography variant="body2" sx={{ color: '#64748b', mb: 3 }}>
                Update your display name. Email and administrative permissions are managed by system administrators.
              </Typography>

              <form onSubmit={handleProfileSubmit}>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="First Name"
                      fullWidth
                      required
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Last Name"
                      fullWidth
                      required
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                    />
                  </Grid>
                </Grid>

                <Box sx={{ mt: 3, textAlign: 'right' }}>
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={isUpdatingProfile}
                    sx={{ fontWeight: 700, px: 3, borderRadius: 2 }}
                  >
                    Save Profile Changes
                  </Button>
                </Box>
              </form>
            </Card>

            {/* Change Password Form */}
            <Card elevation={0} sx={{ border: '1px solid #e2e8f0', borderRadius: 3, p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1, color: '#0f172a' }}>
                Security & Password Change
              </Typography>
              <Typography variant="body2" sx={{ color: '#64748b', mb: 3 }}>
                Ensure your account is using a strong password of at least 8 characters.
              </Typography>

              <form onSubmit={handlePasswordSubmit}>
                <Stack spacing={2.5}>
                  <TextField
                    label="Current Password"
                    type="password"
                    fullWidth
                    required
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                  />
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        label="New Password"
                        type="password"
                        fullWidth
                        required
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        helperText="Minimum 8 characters"
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        label="Confirm New Password"
                        type="password"
                        fullWidth
                        required
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                      />
                    </Grid>
                  </Grid>

                  <Box sx={{ textAlign: 'right' }}>
                    <Button
                      type="submit"
                      variant="contained"
                      color="secondary"
                      disabled={isChangingPass}
                      sx={{ fontWeight: 700, px: 3, borderRadius: 2 }}
                    >
                      Update Password
                    </Button>
                  </Box>
                </Stack>
              </form>
            </Card>
          </Stack>
        </Grid>
      </Grid>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} sx={{ borderRadius: 2 }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </PageContainer>
  );
};
