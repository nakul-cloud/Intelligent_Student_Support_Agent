import axiosInstance from './axiosInstance';

/**
 * Audit Service
 * Adheres to Single Responsibility Principle (SRP):
 * Manages security audit log retrieval and compliance metrics queries.
 */
export const auditService = {
  /**
   * Fetch immutable security audit logs
   * @param {number} limit
   * @param {string|null} decision
   */
  async getLogs(limit = 50, decision = null) {
    const params = { limit };
    if (decision) params.decision = decision;
    const response = await axiosInstance.get('/audit/logs', { params });
    return response.data.data;
  },

  /**
   * Fetch aggregate compliance and evaluation metrics
   */
  async getSummary() {
    const response = await axiosInstance.get('/audit/summary');
    return response.data.data;
  },

  /**
   * Fetch system health status
   */
  async getHealth() {
    const response = await axiosInstance.get('/health');
    return response.data;
  },
};
