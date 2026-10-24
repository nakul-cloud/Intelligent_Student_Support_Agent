import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusCircle, MessageSquare, LifeBuoy } from 'lucide-react';
import StatusBadge from '../atoms/StatusBadge';
import Button from '../atoms/Button';
import { formatDate } from '../../utils/formatters';

/**
 * TicketList Composite Component
 * Renders support tickets & formal requests matching Stitch records screen
 */
export default function TicketList({ tickets = [] }) {
  const navigate = useNavigate();

  const handleFileNewTicket = () => {
    navigate('/chat', {
      state: {
        preloadedPrompt: 'I would like to submit a formal support ticket regarding an administrative issue.',
      },
    });
  };

  const handleViewThread = (ticket) => {
    navigate('/chat', {
      state: {
        preloadedPrompt: `Please show me the current status and update for support ticket #${ticket.id || ticket.ticket_id || 'TK-9021'}.`,
      },
    });
  };

  const activeCount = tickets.filter(
    (t) => (t.status || '').toLowerCase() === 'open' || (t.status || '').toLowerCase() === 'in review'
  ).length;
  const resolvedCount = tickets.length - activeCount;

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      {/* Header with counter and File New button */}
      <div className="p-4 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-ink-primary">
              Support Tickets & Formal Requests
            </h2>
            <span className="text-[11px] font-medium bg-canvas text-ink-subtle px-2 py-0.5 rounded-[4px] border border-border tabular-nums">
              {activeCount} active • {resolvedCount} resolved
            </span>
          </div>
          <p className="text-xs text-ink-subtle mt-0.5">
            Student inquiry tickets and escalation logs managed by academic affairs.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={handleFileNewTicket}
          icon={PlusCircle}
        >
          File New Request
        </Button>
      </div>

      {/* Tickets Table / List */}
      {tickets.length === 0 ? (
        <div className="p-8 text-center bg-white flex flex-col items-center justify-center gap-2">
          <LifeBuoy className="w-8 h-8 text-slate-300" />
          <p className="text-xs font-medium text-ink-muted">
            No active support tickets or grievances filed.
          </p>
          <p className="text-[11px] text-ink-subtle max-w-sm">
            If you need assistance with tuition payments, grade corrections, or academic policy clarification, you can create a ticket directly with the AI advisor.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50/80 border-b border-border text-ink-subtle font-medium">
                <th className="py-2.5 px-4 font-semibold">Ticket Identifier</th>
                <th className="py-2.5 px-4 font-semibold">Topic & Issue Description</th>
                <th className="py-2.5 px-4 font-semibold">Assigned Unit</th>
                <th className="py-2.5 px-4 font-semibold">Submitted Date</th>
                <th className="py-2.5 px-4 font-semibold">Status</th>
                <th className="py-2.5 px-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {tickets.map((t, idx) => {
                const ticketId = t.ticket_id || t.id || `TK-${9000 + idx}`;
                const category = t.category || 'Academic Services';
                return (
                  <tr
                    key={ticketId}
                    className="hover:bg-slate-50/60 transition-colors bg-white"
                  >
                    <td className="py-3 px-4 font-mono font-semibold text-accent">
                      #{ticketId.slice(0, 10)}
                    </td>
                    <td className="py-3 px-4">
                      <p className="font-medium text-ink-primary">
                        {t.description || 'Support Request'}
                      </p>
                      <span className="text-[10px] text-ink-subtle">
                        Category: {category}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-ink-muted">
                      {category === 'fee' ? 'Bursar & Accounts' : 'Registrar Advisory'}
                    </td>
                    <td className="py-3 px-4 tabular-nums text-ink-subtle">
                      {formatDate(t.created_at)}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={t.status || 'Open'} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewThread(t)}
                        icon={MessageSquare}
                      >
                        View Thread
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
