import axiosInstance from './axiosInstance';

/**
 * Authentication Service
 * Adheres to Single Responsibility Principle (SRP):
 * Manages only authentication network requests.
 */
export const authService = {
  /**
   * Log in an enrolled student
   * @param {string} studentId
   * @param {string} password
   * @returns {Promise<{ access_token: string, token_type: string, expires_in: number }>}
   */
  async login(studentId, password) {
    const response = await axiosInstance.post('/auth/login', {
      student_id: studentId.trim().toUpperCase(),
      password,
    });
    return response.data.data;
  },

  /**
   * Register credentials for an enrolled student
   * @param {string} studentId
   * @param {string} password
   * @returns {Promise<{ student_id: string, message: string }>}
   */
  async signup(studentId, password) {
    const response = await axiosInstance.post('/auth/signup', {
      student_id: studentId.trim().toUpperCase(),
      password,
    });
    return response.data.data;
  },

  /**
   * Verify token validity
   * @returns {Promise<{ student_id: string, authenticated: boolean }>}
   */
  async getMe() {
    const response = await axiosInstance.get('/auth/me');
    return response.data.data;
  },

  /**
   * Update student password immediately in database
   * @param {string} newPassword
   * @returns {Promise<{ student_id: string, message: string }>}
   */
  async changePassword(newPassword) {
    const response = await axiosInstance.post('/auth/change-password', {
      new_password: newPassword,
    });
    return response.data.data;
  },
};

