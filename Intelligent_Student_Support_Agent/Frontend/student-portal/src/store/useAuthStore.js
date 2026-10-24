import { create } from 'zustand';

/**
 * Global authentication state store.
 * Adheres to Single Responsibility Principle (SRP):
 * Manages only authentication session tokens and current student metadata.
 */
export const useAuthStore = create((set) => {
  // Initialize from localStorage if present
  const storedToken = localStorage.getItem('auth_token');
  const storedStudentId = localStorage.getItem('auth_student_id');
  const storedProfile = localStorage.getItem('auth_student_profile');

  let parsedProfile = null;
  try {
    parsedProfile = storedProfile ? JSON.parse(storedProfile) : null;
  } catch (e) {
    parsedProfile = null;
  }

  return {
    token: storedToken || null,
    studentId: storedStudentId || null,
    name: parsedProfile?.name || '',
    programme: parsedProfile?.programme || '',
    batch: parsedProfile?.batch || '',
    status: parsedProfile?.status || 'Good Standing',
    phone: parsedProfile?.phone || '',
    email: parsedProfile?.email || '',
    address: parsedProfile?.address || '',
    isAuthenticated: Boolean(storedToken),

    setAuth: ({ token, studentId, name, programme, batch, status, phone, email, address }) => {
      if (token) localStorage.setItem('auth_token', token);
      if (studentId) localStorage.setItem('auth_student_id', studentId);

      const profile = {
        name: name || '',
        programme: programme || '',
        batch: batch || '',
        status: status || 'Good Standing',
        phone: phone || '',
        email: email || '',
        address: address || '',
      };
      localStorage.setItem('auth_student_profile', JSON.stringify(profile));

      set({
        token: token || null,
        studentId: studentId || null,
        name: profile.name,
        programme: profile.programme,
        batch: profile.batch,
        status: profile.status,
        phone: profile.phone,
        email: profile.email,
        address: profile.address,
        isAuthenticated: true,
      });
    },

    updateProfile: (profileData) => {
      set((state) => {
        const updated = {
          name: profileData.name ?? state.name,
          programme: profileData.programme ?? state.programme,
          batch: profileData.batch ?? state.batch,
          status: profileData.status ?? state.status,
          phone: profileData.phone ?? state.phone,
          email: profileData.email ?? state.email,
          address: profileData.address ?? state.address,
        };
        localStorage.setItem('auth_student_profile', JSON.stringify(updated));
        return updated;
      });
    },


    clearAuth: () => {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_student_id');
      localStorage.removeItem('auth_student_profile');
      set({
        token: null,
        studentId: null,
        name: '',
        programme: '',
        batch: '',
        status: '',
        isAuthenticated: false,
      });
    },
  };
});
