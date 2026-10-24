import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import AppShell from '../components/layout/AppShell';
import AuthPage from '../pages/AuthPage';
import DashboardPage from '../pages/DashboardPage';
import ChatPage from '../pages/ChatPage';
import RecordsPage from '../pages/RecordsPage';

/**
 * AppRouter Component
 * Maps all institutional portal routes
 */
export default function AppRouter() {
  return (
    <Routes>
      {/* Public Authentication Doorway */}
      <Route path="/login" element={<AuthPage />} />

      {/* Protected Student Workstation Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/chat" replace />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="records" element={<RecordsPage />} />
      </Route>

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/chat" replace />} />
    </Routes>
  );
}
