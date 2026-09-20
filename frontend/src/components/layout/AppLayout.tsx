import React, { useState } from 'react';
import { Box } from '@mui/material';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: '#f8fafc' }}>
      <TopBar onToggleSidebar={handleDrawerToggle} />
      
      <Box sx={{ display: 'flex', flexGrow: 1 }}>
        {/* Desktop Sidebar */}
        <Box sx={{ display: { xs: 'none', md: 'block' } }}>
          <Sidebar variant="permanent" open />
        </Box>

        {/* Mobile Temporary Sidebar */}
        <Box sx={{ display: { xs: 'block', md: 'none' } }}>
          <Sidebar variant="temporary" open={mobileOpen} onClose={handleDrawerToggle} />
        </Box>

        {/* Main Content Area */}
        <Box component="main" sx={{ flexGrow: 1, minWidth: 0, pb: 6 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};
