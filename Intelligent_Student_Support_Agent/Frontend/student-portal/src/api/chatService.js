import axiosInstance from './axiosInstance';

/**
 * Chat Service
 * Adheres to Single Responsibility Principle (SRP):
 * Manages conversational turns, sessions, and chat history retrieval.
 */
export const chatService = {
  /**
   * Submit query to agent
   * @param {string} message
   * @param {string|null} conversationId
   */
  async sendMessage(message, conversationId = null) {
    const payload = { message };
    if (conversationId) {
      payload.conversation_id = conversationId;
    }
    const response = await axiosInstance.post('/chat', payload);
    return response.data.data;
  },

  /**
   * List all conversation sessions for the authenticated student
   */
  async listConversations() {
    const response = await axiosInstance.get('/chat/conversations');
    return response.data.data;
  },

  /**
   * Retrieve full turn history of a given session
   * @param {string} conversationId
   */
  async getMessages(conversationId) {
    const response = await axiosInstance.get(`/chat/conversations/${conversationId}/messages`);
    return response.data.data;
  },

  /**
   * Delete an existing conversation session and its messages
   * @param {string} conversationId
   */
  async deleteConversation(conversationId) {
    const response = await axiosInstance.delete(`/chat/conversations/${conversationId}`);
    return response.data.data;
  },
};

