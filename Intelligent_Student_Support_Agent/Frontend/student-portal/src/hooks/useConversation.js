import { useState, useEffect, useCallback, useRef } from 'react';
import { chatService } from '../api/chatService';
import toast from 'react-hot-toast';

/**
 * Custom Hook: useConversation
 * Adheres to SRP: Handles chat session state, message turns, and agent communication.
 */
export function useConversation(initialConversationId = null) {
  // Restore last active conversation from storage if available
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(() => {
    return initialConversationId || sessionStorage.getItem('active_conv_id') || null;
  });
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);

  // Track if we just received a live response to skip redundant refetch flash
  const justReceivedTurnRef = useRef(false);

  // Load list of past sessions
  const loadConversations = useCallback(async () => {
    try {
      const data = await chatService.listConversations();
      if (Array.isArray(data)) {
        // Ensure no duplicate IDs in list
        const seen = new Set();
        const unique = data.filter((item) => {
          if (seen.has(item.id)) return false;
          seen.add(item.id);
          return true;
        });
        setConversations(unique);
      }
    } catch (err) {
      console.warn('Could not load past conversations:', err);
    }
  }, []);

  // Load message turns for active conversation
  const loadMessages = useCallback(async (convId) => {
    if (!convId) {
      setMessages([]);
      return;
    }
    // If turn was just added locally, avoid wiping state
    if (justReceivedTurnRef.current) {
      justReceivedTurnRef.current = false;
      return;
    }

    setLoading(true);
    try {
      const msgs = await chatService.getMessages(convId);
      if (Array.isArray(msgs)) {
        setMessages(msgs);
      }
    } catch (err) {
      const msg = err.response?.data?.message || 'Failed to load conversation history.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (activeConvId) {
      sessionStorage.setItem('active_conv_id', activeConvId);
      loadMessages(activeConvId);
    } else {
      sessionStorage.removeItem('active_conv_id');
      setMessages([]);
    }
  }, [activeConvId, loadMessages]);

  // Start fresh conversation
  const startNewConversation = () => {
    setActiveConvId(null);
    sessionStorage.removeItem('active_conv_id');
    setMessages([]);
  };

  // Select an existing session
  const selectConversation = (convId) => {
    setActiveConvId(convId);
    sessionStorage.setItem('active_conv_id', convId);
  };

  // Delete an existing session
  const deleteConversation = async (convId) => {
    try {
      await chatService.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConvId === convId) {
        startNewConversation();
      }
      toast.success('Chat removed.');
    } catch (err) {
      const msg = err.response?.data?.message || 'Failed to delete chat.';
      toast.error(msg);
    }
  };

  // Send turn message
  const sendMessage = async (text) => {
    if (!text || !text.trim() || sending) return;

    const userMessageContent = text.trim();
    const optimisticUserMsg = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userMessageContent,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, optimisticUserMsg]);
    setSending(true);
    setError(null);

    try {
      const resp = await chatService.sendMessage(userMessageContent, activeConvId);

      // Backend returns ChatResponse: { conversation_id, message, trace, facts_learned, ... }
      const newConvId = resp.conversation_id;
      if (newConvId && newConvId !== activeConvId) {
        justReceivedTurnRef.current = true;
        sessionStorage.setItem('active_conv_id', newConvId);
        setActiveConvId(newConvId);
      }

      const assistantMsg = {
        id: resp.trace_id || `turn-${Date.now()}`,
        role: 'assistant',
        content: resp.message || resp.reply || '',
        created_at: new Date().toISOString(),
        meta_data: {
          trace: resp.trace,
          facts_learned: resp.facts_learned || [],
        },
      };

      setMessages((prev) => [...prev, assistantMsg]);
      // Refresh session list so the newly created or updated conversation appears
      loadConversations();
    } catch (err) {
      const msg = err.response?.data?.message || err.message || 'Error communicating with agent.';
      setError(msg);
      toast.error(msg);
    } finally {
      setSending(false);
    }
  };

  return {
    conversations,
    activeConvId,
    messages,
    loading,
    sending,
    error,
    startNewConversation,
    selectConversation,
    deleteConversation,
    sendMessage,
    refreshConversations: loadConversations,
  };
}
