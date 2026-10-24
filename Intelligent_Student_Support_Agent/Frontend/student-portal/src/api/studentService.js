import axiosInstance from './axiosInstance';

/**
 * Student Records Service
 * Adheres to Single Responsibility Principle (SRP):
 * Exclusively handles student profile, ledger, scholarship, and tickets endpoints.
 */
export const studentService = {
  /**
   * Fetch profile and enrollment info for authenticated student
   */
  async getProfile() {
    const response = await axiosInstance.get('/student/profile');
    return response.data.data;
  },

  /**
   * Fetch tuition fee ledger, installment dues, and receipts
   */
  async getFees() {
    const response = await axiosInstance.get('/student/fees');
    return response.data.data;
  },

  /**
   * Fetch scholarship award record if granted
   */
  async getScholarship() {
    const response = await axiosInstance.get('/student/scholarship');
    return response.data.data;
  },

  /**
   * Fetch grievance and inquiry tickets logged by the student
   */
  async getTickets() {
    const response = await axiosInstance.get('/student/tickets');
    return response.data.data;
  },

  /**
   * Update student contact details (phone, email, address)
   */
  async updateProfile(data) {
    const response = await axiosInstance.put('/student/profile', data);
    return response.data.data;
  },
};

