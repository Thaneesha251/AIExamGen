import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Typography,
  Divider,
} from '@mui/material';
import {
  Dashboard,
  People,
  Business,
  School,
  HistoryEdu,
  MenuBook,
  Quiz,
  AssignmentTurnedIn,
  Grade,
  Person,
  FolderOpen,
  AutoAwesome,
  Compare,
  Analytics,
  Assessment,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

interface SidebarProps {
  open?: boolean;
  onClose?: () => void;
  variant?: 'permanent' | 'temporary';
}

export const Sidebar: React.FC<SidebarProps> = ({
  open = true,
  onClose,
  variant = 'permanent',
}) => {
  const { userRole } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const getMenuItems = () => {
    switch (userRole) {
      case 'ADMIN':
        return [
          { text: 'Dashboard', icon: <Dashboard />, path: '/admin/dashboard' },
          { text: 'User Management', icon: <People />, path: '/admin/users' },
          { text: 'Departments', icon: <Business />, path: '/admin/departments' },
          { text: 'Courses & Academics', icon: <School />, path: '/admin/academics' },
          { text: 'Audit Logs', icon: <HistoryEdu />, path: '/admin/audit-logs' },
          { text: 'My Profile', icon: <Person />, path: '/profile' },
        ];
      case 'FACULTY':
        return [
          { text: 'Dashboard', icon: <Dashboard />, path: '/faculty/dashboard' },
          { text: 'My Subjects', icon: <MenuBook />, path: '/faculty/subjects' },
          { text: 'Syllabus & LOs', icon: <FolderOpen />, path: '/faculty/syllabus' },
          { text: 'Question Bank', icon: <Quiz />, path: '/faculty/question-bank' },
          { text: 'AI Generation', icon: <AutoAwesome />, path: '/faculty/question-generation' },
          { text: 'Exam Blueprints', icon: <HistoryEdu />, path: '/faculty/blueprints' },
          { text: 'Question Papers', icon: <AssignmentTurnedIn />, path: '/faculty/question-papers' },
          { text: 'Evaluation Rubrics', icon: <Grade />, path: '/faculty/rubrics' },
          { text: 'Plagiarism Analysis', icon: <Compare />, path: '/faculty/similarity' },
          { text: 'Performance Analytics', icon: <Analytics />, path: '/faculty/analytics' },
          { text: 'Exam Quality', icon: <Assessment />, path: '/faculty/exam-quality' },
          { text: 'My Profile', icon: <Person />, path: '/profile' },
        ];

      case 'STUDENT':
        return [
          { text: 'Dashboard', icon: <Dashboard />, path: '/student/dashboard' },
          { text: 'My Examinations', icon: <AssignmentTurnedIn />, path: '/student/exams' },
          { text: 'My Results', icon: <Grade />, path: '/student/results' },
          { text: 'My Profile', icon: <Person />, path: '/profile' },
        ];
      default:
        return [
          { text: 'My Profile', icon: <Person />, path: '/profile' },
        ];
    }
  };

  const menuItems = getMenuItems();

  const drawerContent = (
    <Box sx={{ width: 260, height: '100%', display: 'flex', flexDirection: 'column', bgcolor: '#1e293b', color: '#fff' }}>
      <Box sx={{ p: 2.5 }}>
        <Typography variant="overline" sx={{ color: '#94a3b8', fontWeight: 700, letterSpacing: '0.1em' }}>
          {userRole} WORKSPACE
        </Typography>
      </Box>

      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.08)' }} />

      <List sx={{ px: 1.5, py: 2, flexGrow: 1 }}>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem disablePadding key={item.text} sx={{ mb: 0.8 }}>
              <ListItemButton
                onClick={() => {
                  navigate(item.path);
                  if (onClose) onClose();
                }}
                sx={{
                  borderRadius: 2.5,
                  py: 1.2,
                  px: 2,
                  backgroundColor: isActive ? '#2563eb' : 'transparent',
                  color: isActive ? '#ffffff' : '#94a3b8',
                  '&:hover': {
                    backgroundColor: isActive ? '#1d4ed8' : 'rgba(255, 255, 255, 0.05)',
                    color: '#ffffff',
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 38,
                    color: isActive ? '#ffffff' : '#64748b',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.text}
                  primaryTypographyProps={{
                    fontSize: '0.92rem',
                    fontWeight: isActive ? 700 : 500,
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Box sx={{ p: 2, borderTop: '1px solid rgba(255, 255, 255, 0.08)', color: '#64748b' }}>
        <Typography variant="caption" display="block" align="center">
          AI ExamGen v1.0.0 &copy; 2026
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Drawer
      variant={variant}
      open={open}
      onClose={onClose}
      sx={{
        width: 260,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: 260,
          boxSizing: 'border-box',
          borderRight: '1px solid rgba(255, 255, 255, 0.08)',
          backgroundColor: '#1e293b',
        },
      }}
    >
      {drawerContent}
    </Drawer>
  );
};
