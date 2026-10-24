import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Plus, Send, Sparkles, MessageSquare, Trash2 } from 'lucide-react';
import { useConversation } from '../hooks/useConversation';
import { useAuthStore } from '../store/useAuthStore';
import MessageBubble from '../components/shared/MessageBubble';
import SuggestedChips from '../components/shared/SuggestedChips';
import { formatDate } from '../utils/formatters';

/**
 * ChatPage – ChatGPT / Claude style conversational workspace.
 * Seamless, full-bleed layout directly integrated into the portal.
 */
export default function ChatPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { name } = useAuthStore();

  const {
    conversations,
    activeConvId,
    messages,
    loading,
    sending,
    startNewConversation,
    selectConversation,
    deleteConversation,
    sendMessage,
  } = useConversation();

  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const handledPromptRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  // Handle preloaded prompt from other views (with strict guard against duplicate execution)
  useEffect(() => {
    const prompt = location.state?.preloadedPrompt;
    if (prompt && handledPromptRef.current !== prompt) {
      handledPromptRef.current = prompt;
      sendMessage(prompt);
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state, navigate, sendMessage]);

  const handleSend = (e) => {
    e?.preventDefault();
    if (!inputMessage.trim() || sending) return;
    const text = inputMessage;
    setInputMessage('');
    sendMessage(text);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const displayName = name ? name.split(' ')[0] : 'there';
  const recentConversations = conversations.slice(0, 20);

  return (
    <div className="flex h-full w-full bg-white overflow-hidden">

      {/* ── Left Sidebar: Past Chats Drawer (ChatGPT/Claude style) ── */}
      <aside className="w-64 bg-slate-50 border-r border-slate-200 flex flex-col shrink-0 hidden md:flex">
        <div className="p-3.5 border-b border-slate-200 bg-slate-50">
          <button
            type="button"
            onClick={startNewConversation}
            className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 active:scale-[0.97] text-white text-xs font-bold shadow-xs transition-[transform,background-color] duration-160 ease-out"
          >
            <Plus className="w-4 h-4" />
            <span>New chat</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {recentConversations.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-400">
              No previous chats yet.
            </div>
          ) : (
            recentConversations.map((c) => {
              const isActive = activeConvId === c.id;
              return (
                <div
                  key={c.id}
                  className={`group relative w-full rounded-xl text-xs transition-[background-color,border-color,color] duration-150 ease-out flex items-center justify-between ${
                    isActive
                      ? 'bg-white text-indigo-900 font-bold border border-indigo-200 shadow-xs'
                      : 'text-slate-600 hover:bg-white hover:text-slate-900'
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => selectConversation(c.id)}
                    className="flex-1 text-left px-3 py-2.5 flex items-start gap-2.5 min-w-0"
                  >
                    <MessageSquare
                      className={`w-4 h-4 mt-0.5 shrink-0 ${
                        isActive ? 'text-indigo-600' : 'text-slate-400'
                      }`}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate leading-snug">{c.title || 'Conversation'}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">{formatDate(c.created_at)}</p>
                    </div>
                  </button>

                  <button
                    type="button"
                    title="Delete chat"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteConversation(c.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1.5 mr-2 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-[opacity,background-color,color] duration-150 ease-out shrink-0"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </aside>


      {/* ── Main Chat Area ── */}
      <div className="flex-1 flex flex-col min-w-0 bg-white h-full relative">

        {/* Minimal Sub-Header */}
        <div className="px-6 py-3 border-b border-slate-100 flex items-center justify-between shrink-0 bg-white">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-slate-900 text-white flex items-center justify-center shadow-xs">
              <Sparkles className="w-4 h-4 text-slate-200" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 leading-tight">AI Student Assistant</h2>
              <p className="text-[11px] text-slate-500">Official University Handbook & Student Records</p>
            </div>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
            <span>Ready</span>
          </div>
        </div>

        {/* Messages Stream (Centered max-w-3xl like ChatGPT/Claude) */}
        <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 bg-slate-50/40">
          <div className="max-w-3xl mx-auto w-full">

            {/* Empty State Welcome */}
            {messages.length === 0 && !loading && (
              <div className="flex flex-col items-center justify-center min-h-[22rem] text-center px-4 py-8">
                <div className="w-14 h-14 rounded-2xl bg-slate-900 text-white flex items-center justify-center mb-4 shadow-sm">
                  <Sparkles className="w-7 h-7 text-slate-200" />
                </div>

                <h3 className="text-2xl font-bold text-slate-900 tracking-tight">
                  How can I help you today, {displayName}?
                </h3>
                <p className="text-sm text-slate-500 mt-2 max-w-lg leading-relaxed font-medium">
                  Ask me anything about fees, scholarships, grading, attendance rules, or university policies. All answers are verified against your official records.
                </p>

                {/* Suggested starter cards */}
                <div className="mt-8 w-full">
                  <SuggestedChips onSelect={(text) => sendMessage(text)} />
                </div>
              </div>
            )}

            {/* Conversation Messages */}
            {messages.map((msg, idx) => (
              <MessageBubble
                key={msg.id || idx}
                role={msg.role}
                content={msg.content}
                timestamp={msg.created_at}
                trace={msg.meta_data?.trace}
              />
            ))}

            {/* Assistant typing indicator */}
            {sending && (
              <div className="flex items-start gap-3 mb-6">
                <div className="w-7 h-7 rounded-lg bg-slate-900 text-white flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                  <Sparkles className="w-4 h-4 text-slate-200" />
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-xs flex items-center gap-2">
                  <span className="w-2 h-2 bg-slate-900 rounded-full animate-bounce" />
                  <span className="w-2 h-2 bg-slate-900 rounded-full animate-bounce [animation-delay:0.15s]" />
                  <span className="w-2 h-2 bg-slate-900 rounded-full animate-bounce [animation-delay:0.3s]" />
                  <span className="text-xs text-slate-500 ml-1 font-medium">Checking university records...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Floating Input Bar (ChatGPT/Claude style) */}
        <div className="p-4 md:p-5 border-t border-slate-100 bg-white shrink-0">
          <div className="max-w-3xl mx-auto w-full">
            <form onSubmit={handleSend} className="relative flex items-center">
              <textarea
                ref={textareaRef}
                rows={1}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about fees, scholarships, policies, or grades..."
                disabled={sending}
                className="w-full text-sm pl-4 pr-12 py-3.5 rounded-2xl border border-slate-300 focus:border-slate-900 focus:ring-2 focus:ring-slate-100 outline-none resize-none leading-relaxed text-slate-900 placeholder:text-slate-400 bg-white transition-[border-color,box-shadow] duration-150 ease-out shadow-sm font-medium"
              />
              <button
                type="submit"
                disabled={!inputMessage.trim() || sending}
                className="absolute right-2.5 w-8 h-8 rounded-xl bg-slate-900 hover:bg-slate-800 active:scale-[0.97] text-white flex items-center justify-center shrink-0 disabled:opacity-30 disabled:cursor-not-allowed transition-[transform,background-color] duration-160 ease-out shadow-xs"
                aria-label="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
            <p className="mt-2 text-xs text-slate-400 text-center font-medium">
              Responses are verified against official university records and the Student Handbook.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
