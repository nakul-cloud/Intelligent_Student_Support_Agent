import React, { useState, useEffect } from 'react';
import { MessageSquare, RefreshCw, CheckCircle2, Clock, AlertCircle, Plus, ArrowRight } from 'lucide-react';
import Skeleton from '../components/atoms/Skeleton';
import { studentService } from '../api/studentService';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

/**
 * RecordsPage – My Requests
 * High-contrast, clean view of student support tickets and inquiries.
 */
export default function RecordsPage() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await studentService.getTickets();
      if (Array.isArray(res)) setTickets(res);
    } catch {
      toast.error('Could not load support requests. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getStatusStyle = (status = '') => {
    const s = status.toLowerCase();
    if (s === 'open') return { bg: 'bg-amber-50', text: 'text-amber-800', border: 'border-amber-300', icon: Clock };
    if (s === 'in review') return { bg: 'bg-blue-50', text: 'text-blue-800', border: 'border-blue-300', icon: RefreshCw };
    if (s === 'resolved' || s === 'closed') return { bg: 'bg-emerald-50', text: 'text-emerald-800', border: 'border-emerald-300', icon: CheckCircle2 };
    return { bg: 'bg-slate-50', text: 'text-slate-700', border: 'border-slate-300', icon: AlertCircle };
  };

  if (loading) {
    return (
      <div className="flex flex-col gap-5 max-w-5xl mx-auto">
        <Skeleton height="h-20" rounded="rounded-2xl" />
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} height="h-24" rounded="rounded-2xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 max-w-5xl mx-auto pb-10">

      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs">
        <div>
          <h1 className="text-lg font-bold text-slate-900">My Requests</h1>
          <p className="text-xs text-slate-500 font-medium mt-1">
            Track unresolved inquiries and official service requests submitted to university departments.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={fetchData}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 shadow-xs transition-[transform,background-color,border-color] duration-160 ease-out active:scale-[0.97]"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          <button
            type="button"
            onClick={() =>
              navigate('/chat', {
                state: { preloadedPrompt: 'I need to open a formal student support request.' },
              })
            }
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold shadow-xs transition-[transform,background-color] duration-160 ease-out active:scale-[0.97]"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New request</span>
          </button>
        </div>
      </div>

      {/* Ticket List */}
      {tickets.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center flex flex-col items-center gap-4 shadow-xs">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">All caught up — no open tickets</h2>
            <p className="text-xs text-slate-500 mt-1 max-w-md">
              Need help with fees, course waivers, or grade verification? Chat with the AI Assistant to submit a ticket.
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/chat')}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-xs transition-[transform,background-color] duration-160 ease-out active:scale-[0.97]"
          >
            <MessageSquare className="w-4 h-4" />
            <span>Open AI Assistant</span>
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-3.5">
          {tickets.map((ticket) => {
            const style = getStatusStyle(ticket.status);
            const Icon = style.icon;
            return (
              <div
                key={ticket.id}
                className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-col sm:flex-row sm:items-start gap-4 hover:border-slate-300 transition-[border-color,box-shadow] duration-160 ease-out"
              >
                <div className={`w-9 h-9 rounded-xl ${style.bg} border ${style.border} flex items-center justify-center shrink-0 mt-0.5`}>
                  <Icon className={`w-4 h-4 ${style.text}`} />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <p className="text-sm font-bold text-slate-900 leading-snug">
                      {ticket.description || 'Support inquiry'}
                    </p>
                    <span
                      className={`text-xs font-bold px-3 py-1 rounded-full border ${style.bg} ${style.text} ${style.border} whitespace-nowrap`}
                    >
                      {ticket.status || 'Open'}
                    </span>
                  </div>

                  {ticket.category && (
                    <p className="text-xs font-medium text-slate-500 mt-1">
                      Department: <strong className="text-slate-700">{ticket.category}</strong>
                    </p>
                  )}

                  <div className="flex items-center gap-4 mt-3 pt-3 border-t border-slate-100 text-xs text-slate-400">
                    {ticket.created_at && (
                      <span>
                        Created:{' '}
                        {new Date(ticket.created_at).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </span>
                    )}
                    <button
                      type="button"
                      onClick={() =>
                        navigate('/chat', {
                          state: {
                            preloadedPrompt: `What is the current status and update for support ticket #${ticket.ticket_id || ticket.id || ''}?`,
                          },
                        })
                      }
                      className="inline-flex items-center gap-1 font-bold text-slate-700 hover:text-slate-950 hover:underline"
                    >
                      <span>Ask AI for updates</span>
                      <ArrowRight className="w-3 h-3 text-slate-400" />
                    </button>

                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
