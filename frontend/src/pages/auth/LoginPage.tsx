import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Chip,
  Container,
  Stack,
  Alert,
  CircularProgress,
  Paper,
  Grid,
  InputAdornment,
  IconButton,
} from '@mui/material';
import {
  School,
  AutoAwesome,
  Analytics,
  AssignmentTurnedIn,
  CheckCircle,
  Error as ErrorIcon,
  Visibility,
  VisibilityOff,
  Lock,
  Email,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { checkBackendHealth } from '@/services/api';

export const LoginPage: React.FC = () => {
  const { login, isAuthenticated, userRole } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('admin123');
  const [showPassword, setShowPassword] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [health, setHealth] = useState<{
    loading: boolean;
    online: boolean;
    data?: any;
    error?: string;
  }>({
    loading: true,
    online: false,
  });

  useEffect(() => {
    let isMounted = true;
    checkBackendHealth()
      .then((res) => {
        if (!isMounted) return;
        if (res && res.success) {
          setHealth({ loading: false, online: true, data: res });
        } else {
          setHealth({
            loading: false,
            online: false,
            error: res?.error?.message || 'Backend server unreachable',
          });
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        setHealth({
          loading: false,
          online: false,
          error: err.message || 'Network error connecting to API',
        });
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && userRole) {
      if (userRole === 'ADMIN') navigate('/admin/dashboard', { replace: true });
      else if (userRole === 'FACULTY') navigate('/faculty/dashboard', { replace: true });
      else if (userRole === 'STUDENT') navigate('/student/dashboard', { replace: true });
    }
  }, [isAuthenticated, userRole, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const authenticatedUser = await login({ email, password });
      const role = authenticatedUser.role?.name || (authenticatedUser as any).role;
      if (role === 'ADMIN') navigate('/admin/dashboard', { replace: true });
      else if (role === 'FACULTY') navigate('/faculty/dashboard', { replace: true });
      else navigate('/student/dashboard', { replace: true });
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please check credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectPreset = (presetEmail: string, presetPass: string) => {
    setEmail(presetEmail);
    setPassword(presetPass);
    setErrorMessage(null);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #1e1b4b 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        py: 6,
        px: 2,
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4} alignItems="center">
          {/* Hero Branding Column */}
          <Grid item xs={12} md={7}>
            <Box sx={{ color: '#ffffff', pr: { md: 4 } }}>
              <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 2 }}>
                <Box
                  sx={{
                    p: 1.2,
                    borderRadius: 3,
                    background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
                    display: 'flex',
                  }}
                >
                  <AutoAwesome sx={{ fontSize: 32, color: '#fff' }} />
                </Box>
                <Typography variant="h3" sx={{ fontWeight: 800, fontFamily: 'Outfit' }}>
                  AI ExamGen
                </Typography>
              </Stack>

              <Typography
                variant="h4"
                sx={{
                  fontWeight: 700,
                  mb: 2,
                  background: 'linear-gradient(90deg, #60a5fa 0%, #a78bfa 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Intelligent Question Paper Generation, Automated Evaluation and Examination Analytics
              </Typography>

              <Typography variant="body1" sx={{ color: '#94a3b8', mb: 4, fontSize: '1.1rem', lineHeight: 1.6 }}>
                An enterprise-grade academic platform leveraging AI, NLP, computer vision OCR, semantic similarity,
                and rule-based scoring pipelines for complete university examination lifecycle management.
              </Typography>

              <Grid container spacing={2}>
                {[
                  {
                    icon: <AutoAwesome sx={{ color: '#60a5fa' }} />,
                    title: 'AI Question Engine',
                    desc: 'Bloom taxonomy & blueprint matrix compliance',
                  },
                  {
                    icon: <AssignmentTurnedIn sx={{ color: '#34d399' }} />,
                    title: 'Multi-Layer OCR & NLP',
                    desc: 'Semantic similarity & rubric scoring',
                  },
                  {
                    icon: <Analytics sx={{ color: '#a78bfa' }} />,
                    title: 'Exam Analytics',
                    desc: 'Class, student & unit performance profiling',
                  },
                  {
                    icon: <School sx={{ color: '#fbbf24' }} />,
                    title: 'Human-in-the-Loop',
                    desc: 'Faculty mark audit & override workflow',
                  },
                ].map((feat, idx) => (
                  <Grid item xs={12} sm={6} key={idx}>
                    <Paper
                      elevation={0}
                      sx={{
                        p: 2,
                        backgroundColor: 'rgba(255, 255, 255, 0.04)',
                        backdropFilter: 'blur(10px)',
                        border: '1px solid rgba(255, 255, 255, 0.08)',
                        borderRadius: 3,
                      }}
                    >
                      <Stack direction="row" spacing={1.5} alignItems="flex-start">
                        {feat.icon}
                        <Box>
                          <Typography variant="subtitle2" sx={{ color: '#fff', fontWeight: 600 }}>
                            {feat.title}
                          </Typography>
                          <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                            {feat.desc}
                          </Typography>
                        </Box>
                      </Stack>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </Box>
          </Grid>

          {/* Login Card Column */}
          <Grid item xs={12} md={5}>
            <Card
              elevation={8}
              sx={{
                p: 2,
                borderRadius: 4,
                backgroundColor: '#ffffff',
                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
              }}
            >
              <CardContent>
                <form onSubmit={handleSubmit}>
                  <Stack spacing={2.5}>
                    <Box>
                      <Typography variant="h5" sx={{ fontWeight: 700, color: '#0f172a', mb: 0.5 }}>
                        Sign In to Platform
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Enter your academic email and password to access workspace
                      </Typography>
                    </Box>

                    {/* Backend Status Indicator */}
                    <Paper
                      variant="outlined"
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        backgroundColor: health.online ? '#f0fdf4' : '#fef2f2',
                        borderColor: health.online ? '#bbf7d0' : '#fecaca',
                      }}
                    >
                      <Stack direction="row" spacing={1.5} alignItems="center">
                        {health.loading ? (
                          <CircularProgress size={18} />
                        ) : health.online ? (
                          <CheckCircle sx={{ color: '#16a34a', fontSize: 20 }} />
                        ) : (
                          <ErrorIcon sx={{ color: '#dc2626', fontSize: 20 }} />
                        )}
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="caption" sx={{ fontWeight: 700, display: 'block', color: '#0f172a' }}>
                            Backend API Gateway
                          </Typography>
                          <Typography variant="caption" sx={{ color: health.online ? '#15803d' : '#b91c1c' }}>
                            {health.loading
                              ? 'Checking server status...'
                              : health.online
                              ? `Online (${health.data?.service || 'FastAPI'} - ${health.data?.database || 'PostgreSQL'} DB)`
                              : `Offline (${health.error || 'Server unreachable'})`}
                          </Typography>
                        </Box>
                      </Stack>
                    </Paper>

                    {errorMessage && (
                      <Alert severity="error" sx={{ borderRadius: 2 }}>
                        {errorMessage}
                      </Alert>
                    )}

                    <TextField
                      label="Academic Email Address"
                      type="email"
                      fullWidth
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <Email sx={{ color: '#94a3b8' }} />
                          </InputAdornment>
                        ),
                      }}
                    />

                    <TextField
                      label="Password"
                      type={showPassword ? 'text' : 'password'}
                      fullWidth
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <Lock sx={{ color: '#94a3b8' }} />
                          </InputAdornment>
                        ),
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              onClick={() => setShowPassword(!showPassword)}
                              edge="end"
                              size="small"
                            >
                              {showPassword ? <VisibilityOff /> : <Visibility />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />

                    <Box>
                      <Typography variant="caption" sx={{ color: '#64748b', display: 'block', mb: 1, fontWeight: 600 }}>
                        Quick Seed Credentials:
                      </Typography>
                      <Stack direction="row" spacing={1} flexWrap="wrap">
                        <Chip
                          label="Admin"
                          color="error"
                          size="small"
                          variant="outlined"
                          onClick={() => handleSelectPreset('admin@example.com', 'admin123')}
                          sx={{ cursor: 'pointer' }}
                        />
                        <Chip
                          label="Faculty"
                          color="primary"
                          size="small"
                          variant="outlined"
                          onClick={() => handleSelectPreset('faculty@example.com', 'faculty123')}
                          sx={{ cursor: 'pointer' }}
                        />
                        <Chip
                          label="Student"
                          color="success"
                          size="small"
                          variant="outlined"
                          onClick={() => handleSelectPreset('student1@example.com', 'student123')}
                          sx={{ cursor: 'pointer' }}
                        />
                      </Stack>
                    </Box>

                    <Button
                      type="submit"
                      variant="contained"
                      size="large"
                      fullWidth
                      disabled={isSubmitting || !health.online}
                      sx={{
                        py: 1.4,
                        fontSize: '1rem',
                        fontWeight: 700,
                        borderRadius: 2.5,
                        background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                      }}
                    >
                      {isSubmitting ? <CircularProgress size={24} sx={{ color: '#fff' }} /> : 'Sign In'}
                    </Button>
                  </Stack>
                </form>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};
