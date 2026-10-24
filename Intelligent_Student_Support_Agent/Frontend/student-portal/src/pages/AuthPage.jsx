import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GraduationCap, AlertCircle, ArrowRight } from 'lucide-react';
import InputField from '../components/atoms/InputField';
import Button from '../components/atoms/Button';
import { authService } from '../api/authService';
import { studentService } from '../api/studentService';
import { useAuthStore } from '../store/useAuthStore';
import toast from 'react-hot-toast';

/**
 * AuthPage Component
 * High-contrast, minimal, accessible login/registration screen.
 * Complies with strict typography, spacing, and contrast tokens.
 */
export default function AuthPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const [activeTab, setActiveTab] = useState('signin');
  const [studentId, setStudentId] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const clearError = () => setErrorMessage('');

  const handleSignIn = async (e) => {
    e.preventDefault();
    clearError();
    if (!studentId.trim() || !password) {
      setErrorMessage('Please enter your Student ID and password.');
      return;
    }

    setLoading(true);
    try {
      const tokenData = await authService.login(studentId.trim().toUpperCase(), password);
      const token = tokenData.access_token;

      setAuth({ token, studentId: studentId.trim().toUpperCase() });

      try {
        const profile = await studentService.getProfile();
        setAuth({
          token,
          studentId: profile.student_id,
          name: profile.name,
          programme: profile.programme,
          batch: profile.batch,
          status: profile.status,
        });
        toast.success(`Welcome back, ${profile.name?.split(' ')[0] || 'there'}!`);
      } catch {
        toast.success('Signed in successfully!');
      }

      navigate('/chat');
    } catch (err) {
      const msg =
        err.response?.data?.message ||
        err.response?.data?.detail ||
        (err.code === 'ERR_NETWORK' || !err.response
          ? 'Cannot connect to backend server. Please make sure backend is running on port 8000.'
          : 'Incorrect Student ID or password. Please verify your credentials.');
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    clearError();

    if (!studentId.trim() || !password) {
      setErrorMessage('Please fill in all fields.');
      return;
    }
    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await authService.signup(studentId.trim().toUpperCase(), password);
      toast.success('Account created! Signing you in...');

      const tokenData = await authService.login(studentId.trim().toUpperCase(), password);
      const token = tokenData.access_token;
      setAuth({ token, studentId: studentId.trim().toUpperCase() });

      try {
        const profile = await studentService.getProfile();
        setAuth({
          token,
          studentId: profile.student_id,
          name: profile.name,
          programme: profile.programme,
          batch: profile.batch,
          status: profile.status,
        });
      } catch {
        /* continue */
      }

      navigate('/chat');
    } catch (err) {
      const msg =
        err.response?.data?.message ||
        err.response?.data?.detail ||
        'Could not create your account. Please ensure your Student ID is registered with the university.';
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-6 selection:bg-indigo-100 selection:text-indigo-900">
      {/* Brand Header */}
      <div className="text-center mb-8">
        <div className="w-14 h-14 rounded-2xl bg-indigo-600 text-white flex items-center justify-center mx-auto mb-4 shadow-sm">
          <GraduationCap className="w-7 h-7" />
        </div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Apex University</h1>
        <p className="text-sm font-medium text-slate-500 mt-1">Institutional Student Support Portal</p>
      </div>

      {/* Auth Card */}
      <div className="w-full max-w-[420px] bg-white rounded-2xl border border-slate-200 p-8 shadow-card">
        {/* Tab switch */}
        <div className="flex bg-slate-100 rounded-xl p-1 mb-6 border border-slate-200/60">
          {[
            { id: 'signin', label: 'Sign in' },
            { id: 'register', label: 'Create account' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => {
                setActiveTab(tab.id);
                clearError();
              }}
              className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                activeTab === tab.id
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Error notice */}
        {errorMessage && (
          <div className="mb-5 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-3 text-xs font-medium">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Sign In Form */}
        {activeTab === 'signin' ? (
          <form onSubmit={handleSignIn} className="flex flex-col gap-4">
            <InputField
              label="Student ID"
              name="studentId"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="e.g. STU001"
              required
            />
            <InputField
              label="Password"
              name="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />

            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={loading}
              className="w-full mt-2 py-3 text-sm font-bold shadow-xs active:scale-[0.98]"
            >
              Sign in to Portal
            </Button>

            {/* Quick Demo Helper */}
            <div className="mt-2 p-3 rounded-xl bg-indigo-50/70 border border-indigo-200/80 flex items-center justify-between text-xs">
              <div>
                <span className="text-slate-500 font-medium">Demo Profile: </span>
                <strong className="text-indigo-950 font-mono font-bold">STU001</strong>
              </div>
              <button
                type="button"
                onClick={() => {
                  setStudentId('STU001');
                  setPassword('Student@123');
                }}
                className="font-bold text-indigo-700 hover:text-indigo-900 inline-flex items-center gap-1 hover:underline"
              >
                <span>Auto-fill</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <p className="text-center text-xs text-slate-500 mt-2 font-medium">
              Need assistance?{' '}
              <button
                type="button"
                onClick={() =>
                  toast('Please contact the university registrar or campus IT desk to reset credentials.', {
                    icon: 'ℹ️',
                  })
                }
                className="text-indigo-600 hover:text-indigo-800 font-bold hover:underline"
              >
                Help desk
              </button>
            </p>
          </form>
        ) : (
          /* Register Form */
          <form onSubmit={handleRegister} className="flex flex-col gap-4">
            <div className="p-3.5 bg-indigo-50 rounded-xl border border-indigo-200 text-xs text-indigo-900 font-medium leading-relaxed">
              Activate your account using your enrolled Student ID (<strong className="font-semibold">STU006 through STU020</strong>).
            </div>

            <InputField
              label="Student ID"
              name="studentId"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="e.g. STU006"
              required
            />
            <InputField
              label="Choose a password"
              name="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 8 characters"
              hint="Must be at least 8 characters"
              required
            />
            <InputField
              label="Confirm password"
              name="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Repeat your password"
              required
            />
            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={loading}
              className="w-full mt-2 py-3 text-sm font-bold shadow-xs active:scale-[0.98]"
            >
              Create account & sign in
            </Button>

            {/* Quick Demo Helper for Registration */}
            <div className="mt-1 p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
              <div>
                <span className="text-slate-500 font-medium">Available ID: </span>
                <strong className="text-slate-900 font-mono font-bold">STU006</strong>
              </div>
              <button
                type="button"
                onClick={() => {
                  setStudentId('STU006');
                  setPassword('Student@123');
                  setConfirmPassword('Student@123');
                }}
                className="font-bold text-indigo-700 hover:text-indigo-900 inline-flex items-center gap-1 hover:underline"
              >
                <span>Auto-fill</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </form>
        )}
      </div>

      <p className="mt-8 text-xs font-medium text-slate-400">
        Apex University Academic Management System · 2025
      </p>
    </div>
  );
}
