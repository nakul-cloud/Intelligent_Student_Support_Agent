import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';

/**
 * ProtectedRoute Guard
 * Ensures only authenticated students with active JWT can access dashboard and records
 */
export default function ProtectedRoute({ children }) {
  const location = useLocation();
  const { isAuthenticated, token } = useAuthStore();

  if (!isAuthenticated || !token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
