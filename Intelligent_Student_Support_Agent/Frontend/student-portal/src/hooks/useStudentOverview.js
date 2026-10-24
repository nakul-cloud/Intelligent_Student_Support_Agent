import { useState, useEffect, useCallback } from 'react';
import { studentService } from '../api/studentService';
import { useAuthStore } from '../store/useAuthStore';
import toast from 'react-hot-toast';

/**
 * Custom Hook: useStudentOverview
 * Adheres to SRP & DRY: Fetches and caches student profile, fees, scholarship, and tickets in parallel.
 */
export function useStudentOverview() {
  const [profile, setProfile] = useState(null);
  const [fees, setFees] = useState(null);
  const [scholarship, setScholarship] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const updateProfile = useAuthStore((s) => s.updateProfile);

  const fetchOverview = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Parallel execution via Promise.allSettled for maximum fault tolerance
      const [profRes, feeRes, scholRes, tickRes] = await Promise.allSettled([
        studentService.getProfile(),
        studentService.getFees(),
        studentService.getScholarship(),
        studentService.getTickets(),
      ]);

      if (profRes.status === 'fulfilled' && profRes.value) {
        setProfile(profRes.value);
        updateProfile(profRes.value);
      }

      if (feeRes.status === 'fulfilled') {
        setFees(feeRes.value);
      }

      if (scholRes.status === 'fulfilled') {
        setScholarship(scholRes.value);
      }

      if (tickRes.status === 'fulfilled' && Array.isArray(tickRes.value)) {
        setTickets(tickRes.value);
      }
    } catch (err) {
      const msg = err.response?.data?.message || err.message || 'Failed to load records.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [updateProfile]);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  return {
    profile,
    fees,
    scholarship,
    tickets,
    loading,
    error,
    refetch: fetchOverview,
  };
}
