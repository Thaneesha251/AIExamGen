import React, { useEffect, useState, useCallback } from 'react';
import {
  Box,
  Card,
  Grid,
  Table,
  TableBody,

  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  MenuItem,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  Typography,
  Stack,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  Paper,
} from '@mui/material';
import {
  Add,
  Search,
  Edit,
  PersonOff,
  PersonAdd,
  AdminPanelSettings,
  Refresh,
} from '@mui/icons-material';
import { PageContainer } from '@/components/layout/PageContainer';
import { userService } from '@/services/userService';
import { User, UserRole } from '@/types/auth';
import { UserCreateData, UserUpdateData } from '@/types/user';

export const UserManagementPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Snackbar feedback
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  // Dialog States
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [roleDialogOpen, setRoleDialogOpen] = useState(false);
  const [statusDialogOpen, setStatusDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // Form States
  const [createForm, setCreateForm] = useState<UserCreateData>({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'STUDENT',
    registration_number: '',
    employee_id: '',
    is_active: true,
  });

  const [editForm, setEditForm] = useState<UserUpdateData>({
    first_name: '',
    last_name: '',
    registration_number: '',
    employee_id: '',
  });

  const [selectedRole, setSelectedRole] = useState<UserRole>('STUDENT');

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await userService.getUsers({
        search: search.trim() || undefined,
        role: roleFilter !== 'ALL' ? (roleFilter as UserRole) : undefined,
        is_active: statusFilter !== 'ALL' ? statusFilter === 'ACTIVE' : undefined,
        page: page + 1,
        page_size: pageSize,
      });

      if (res && res.success && res.data) {
        setUsers(res.data.items);
        setTotal(res.data.total);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load user list');
    } finally {
      setIsLoading(false);
    }
  }, [search, roleFilter, statusFilter, page, pageSize]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await userService.createUser(createForm);
      setSnackbar({ open: true, message: 'User created successfully!', severity: 'success' });
      setCreateDialogOpen(false);
      setCreateForm({
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        role: 'STUDENT',
        registration_number: '',
        employee_id: '',
        is_active: true,
      });
      fetchUsers();
    } catch (err: any) {
      setSnackbar({ open: true, message: err.message || 'Failed to create user', severity: 'error' });
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    try {
      await userService.updateUser(selectedUser.id, editForm);
      setSnackbar({ open: true, message: 'User details updated successfully!', severity: 'success' });
      setEditDialogOpen(false);
      fetchUsers();
    } catch (err: any) {
      setSnackbar({ open: true, message: err.message || 'Failed to update user', severity: 'error' });
    }
  };

  const handleChangeRoleSubmit = async () => {
    if (!selectedUser) return;
    try {
      await userService.updateUserRole(selectedUser.id, selectedRole);
      setSnackbar({ open: true, message: `Role changed to ${selectedRole}!`, severity: 'success' });
      setRoleDialogOpen(false);
      fetchUsers();
    } catch (err: any) {
      setSnackbar({ open: true, message: err.message || 'Failed to change role', severity: 'error' });
    }
  };

  const handleToggleStatusConfirm = async () => {
    if (!selectedUser) return;
    try {
      const newStatus = !selectedUser.is_active;
      await userService.updateUserStatus(selectedUser.id, newStatus);
      setSnackbar({
        open: true,
        message: `User ${newStatus ? 'activated' : 'deactivated'} successfully!`,
        severity: 'success',
      });
      setStatusDialogOpen(false);
      fetchUsers();
    } catch (err: any) {
      setSnackbar({ open: true, message: err.message || 'Failed to update user status', severity: 'error' });
    }
  };

  const openEditModal = (user: User) => {
    setSelectedUser(user);
    setEditForm({
      first_name: user.first_name,
      last_name: user.last_name,
      registration_number: user.registration_number || '',
      employee_id: user.employee_id || '',
    });
    setEditDialogOpen(true);
  };

  const openRoleModal = (user: User) => {
    setSelectedUser(user);
    setSelectedRole((user.role?.name || (user as any).role || 'STUDENT') as UserRole);
    setRoleDialogOpen(true);
  };

  const openStatusModal = (user: User) => {
    setSelectedUser(user);
    setStatusDialogOpen(true);
  };

  const getRoleBadge = (roleName: string) => {
    switch (roleName) {
      case 'ADMIN':
        return <Chip label="ADMIN" size="small" color="error" variant="outlined" sx={{ fontWeight: 700 }} />;
      case 'FACULTY':
        return <Chip label="FACULTY" size="small" color="primary" variant="outlined" sx={{ fontWeight: 700 }} />;
      default:
        return <Chip label="STUDENT" size="small" color="success" variant="outlined" sx={{ fontWeight: 700 }} />;
    }
  };

  return (
    <PageContainer
      title="User Management"
      subtitle="Manage system administrators, faculty members, and student user accounts"
      action={
        <Stack direction="row" spacing={1.5}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => fetchUsers()}
            sx={{ borderRadius: 2 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialogOpen(true)}
            sx={{
              borderRadius: 2,
              background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
              fontWeight: 700,
            }}
          >
            Create New User
          </Button>
        </Stack>
      }
    >
      <Stack spacing={3}>
        {errorMsg && <Alert severity="error">{errorMsg}</Alert>}

        {/* Filter Toolbar Card */}
        <Card elevation={0} sx={{ p: 2, border: '1px solid #e2e8f0', borderRadius: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={5}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search by name, email, registration no, or employee ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                InputProps={{
                  startAdornment: <Search sx={{ color: '#94a3b8', mr: 1 }} />,
                }}
              />
            </Grid>
            <Grid item xs={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Filter Role</InputLabel>
                <Select
                  value={roleFilter}
                  label="Filter Role"
                  onChange={(e) => setRoleFilter(e.target.value)}
                >
                  <MenuItem value="ALL">All Roles</MenuItem>
                  <MenuItem value="ADMIN">ADMIN</MenuItem>
                  <MenuItem value="FACULTY">FACULTY</MenuItem>
                  <MenuItem value="STUDENT">STUDENT</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Filter Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Filter Status"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="ALL">All Statuses</MenuItem>
                  <MenuItem value="ACTIVE">Active Only</MenuItem>
                  <MenuItem value="INACTIVE">Inactive Only</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Card>

        {/* User Table Card */}
        <Card elevation={0} sx={{ border: '1px solid #e2e8f0', borderRadius: 3, overflow: 'hidden' }}>
          <TableContainer>
            <Table>
              <TableHead sx={{ backgroundColor: '#f8fafc' }}>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700, color: '#475569' }}>User Name</TableCell>
                  <TableCell sx={{ fontWeight: 700, color: '#475569' }}>Email</TableCell>
                  <TableCell sx={{ fontWeight: 700, color: '#475569' }}>Role</TableCell>
                  <TableCell sx={{ fontWeight: 700, color: '#475569' }}>Identifier</TableCell>
                  <TableCell sx={{ fontWeight: 700, color: '#475569' }}>Status</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 700, color: '#475569' }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                      <CircularProgress size={32} />
                      <Typography variant="body2" sx={{ color: '#64748b', mt: 1 }}>
                        Loading user accounts...
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                      <Typography variant="body1" sx={{ color: '#64748b', fontWeight: 600 }}>
                        No user accounts match current filters.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((u) => {
                    const roleName = u.role?.name || (u as any).role || 'STUDENT';
                    return (
                      <TableRow key={u.id} hover>
                        <TableCell>
                          <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0f172a' }}>
                            {u.first_name} {u.last_name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ color: '#475569' }}>
                            {u.email}
                          </Typography>
                        </TableCell>
                        <TableCell>{getRoleBadge(roleName)}</TableCell>
                        <TableCell>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace', color: '#64748b' }}>
                            {u.registration_number ? `REG: ${u.registration_number}` : u.employee_id ? `EMP: ${u.employee_id}` : '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={u.is_active ? 'Active' : 'Inactive'}
                            size="small"
                            color={u.is_active ? 'success' : 'default'}
                            sx={{ fontWeight: 600 }}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Stack direction="row" spacing={1} justifyContent="flex-end">
                            <Tooltip title="Edit Details">
                              <IconButton size="small" onClick={() => openEditModal(u)}>
                                <Edit fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Change Role">
                              <IconButton size="small" onClick={() => openRoleModal(u)}>
                                <AdminPanelSettings fontSize="small" sx={{ color: '#7c3aed' }} />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title={u.is_active ? 'Deactivate User' : 'Activate User'}>
                              <IconButton size="small" onClick={() => openStatusModal(u)}>
                                {u.is_active ? (
                                  <PersonOff fontSize="small" sx={{ color: '#dc2626' }} />
                                ) : (
                                  <PersonAdd fontSize="small" sx={{ color: '#16a34a' }} />
                                )}
                              </IconButton>
                            </Tooltip>
                          </Stack>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            component="div"
            count={total}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            rowsPerPage={pageSize}
            onRowsPerPageChange={(e) => {
              setPageSize(parseInt(e.target.value, 10));
              setPage(0);
            }}
          />
        </Card>
      </Stack>

      {/* CREATE USER DIALOG */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <form onSubmit={handleCreateSubmit}>
          <DialogTitle sx={{ fontWeight: 700 }}>Create New User Account</DialogTitle>
          <DialogContent dividers>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    label="First Name"
                    fullWidth
                    required
                    value={createForm.first_name}
                    onChange={(e) => setCreateForm({ ...createForm, first_name: e.target.value })}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    label="Last Name"
                    fullWidth
                    required
                    value={createForm.last_name}
                    onChange={(e) => setCreateForm({ ...createForm, last_name: e.target.value })}
                  />
                </Grid>
              </Grid>
              <TextField
                label="Email Address"
                type="email"
                fullWidth
                required
                value={createForm.email}
                onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
              />
              <TextField
                label="Password (min 8 chars)"
                type="password"
                fullWidth
                required
                value={createForm.password}
                onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
              />
              <FormControl fullWidth required>
                <InputLabel>Assigned Role</InputLabel>
                <Select
                  value={createForm.role}
                  label="Assigned Role"
                  onChange={(e) => setCreateForm({ ...createForm, role: e.target.value as UserRole })}
                >
                  <MenuItem value="STUDENT">STUDENT</MenuItem>
                  <MenuItem value="FACULTY">FACULTY</MenuItem>
                  <MenuItem value="ADMIN">ADMIN</MenuItem>
                </Select>
              </FormControl>
              {createForm.role === 'STUDENT' ? (
                <TextField
                  label="Registration Number"
                  fullWidth
                  placeholder="e.g. REG20260010"
                  value={createForm.registration_number || ''}
                  onChange={(e) => setCreateForm({ ...createForm, registration_number: e.target.value })}
                />
              ) : (
                <TextField
                  label="Employee ID"
                  fullWidth
                  placeholder="e.g. FAC-099"
                  value={createForm.employee_id || ''}
                  onChange={(e) => setCreateForm({ ...createForm, employee_id: e.target.value })}
                />
              )}
            </Stack>
          </DialogContent>
          <DialogActions sx={{ px: 3, py: 2 }}>
            <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" sx={{ fontWeight: 700 }}>
              Create Account
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* EDIT USER DIALOG */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <form onSubmit={handleEditSubmit}>
          <DialogTitle sx={{ fontWeight: 700 }}>Edit User Details</DialogTitle>
          <DialogContent dividers>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    label="First Name"
                    fullWidth
                    required
                    value={editForm.first_name}
                    onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    label="Last Name"
                    fullWidth
                    required
                    value={editForm.last_name}
                    onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                  />
                </Grid>
              </Grid>
              <TextField
                label="Registration Number"
                fullWidth
                value={editForm.registration_number}
                onChange={(e) => setEditForm({ ...editForm, registration_number: e.target.value })}
              />
              <TextField
                label="Employee ID"
                fullWidth
                value={editForm.employee_id}
                onChange={(e) => setEditForm({ ...editForm, employee_id: e.target.value })}
              />
            </Stack>
          </DialogContent>
          <DialogActions sx={{ px: 3, py: 2 }}>
            <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" sx={{ fontWeight: 700 }}>
              Save Changes
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* CHANGE ROLE DIALOG */}
      <Dialog open={roleDialogOpen} onClose={() => setRoleDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>Change User Role</DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" sx={{ mb: 2, color: '#64748b' }}>
            Modify role privileges for <strong>{selectedUser?.first_name} {selectedUser?.last_name}</strong>:
          </Typography>
          <FormControl fullWidth>
            <InputLabel>New Role</InputLabel>
            <Select
              value={selectedRole}
              label="New Role"
              onChange={(e) => setSelectedRole(e.target.value as UserRole)}
            >
              <MenuItem value="STUDENT">STUDENT</MenuItem>
              <MenuItem value="FACULTY">FACULTY</MenuItem>
              <MenuItem value="ADMIN">ADMIN</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button onClick={() => setRoleDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleChangeRoleSubmit} variant="contained" color="secondary" sx={{ fontWeight: 700 }}>
            Update Role
          </Button>
        </DialogActions>
      </Dialog>

      {/* TOGGLE STATUS DIALOG */}
      <Dialog open={statusDialogOpen} onClose={() => setStatusDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700 }}>
          {selectedUser?.is_active ? 'Deactivate User Account' : 'Reactivate User Account'}
        </DialogTitle>
        <DialogContent dividers>
          <Typography variant="body1">
            Are you sure you want to {selectedUser?.is_active ? 'deactivate' : 'activate'}{' '}
            <strong>{selectedUser?.first_name} {selectedUser?.last_name}</strong> ({selectedUser?.email})?
          </Typography>
          {selectedUser?.is_active && (
            <Typography variant="caption" sx={{ display: 'block', color: '#dc2626', mt: 1 }}>
              Deactivated users will not be able to log in or access protected APIs.
            </Typography>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button onClick={() => setStatusDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleToggleStatusConfirm}
            variant="contained"
            color={selectedUser?.is_active ? 'error' : 'success'}
            sx={{ fontWeight: 700 }}
          >
            Confirm {selectedUser?.is_active ? 'Deactivation' : 'Activation'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* FEEDBACK SNACKBAR */}
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
