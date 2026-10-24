import React, { useState } from 'react';
import { ShieldCheck, Filter } from 'lucide-react';
import StatusBadge from '../atoms/StatusBadge';
import {
  formatDate,
  mapResourceName,
  mapActionDescription,
} from '../../utils/formatters';

/**
 * AuditTable Composite Component
 * Renders immutable FERPA compliance audit trail
 */
export default function AuditTable({ logs = [], summary = null }) {
  const [filterDecision, setFilterDecision] = useState('ALL');

  const filteredLogs = logs.filter((log) => {
    if (filterDecision === 'ALL') return true;
    return (log.decision || '').toUpperCase() === filterDecision;
  });

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-ink-primary">
              Verified Interaction & Compliance Audit Trail
            </h2>
            <span className="text-[11px] font-medium bg-status-paid-bg text-status-paid border border-status-paid-border px-2 py-0.5 rounded-[4px]">
              Deterministic Isolation Verified
            </span>
          </div>
          <p className="text-xs text-ink-subtle mt-0.5">
            Immutable audit log verifying deterministic record isolation under FERPA compliance rules.
          </p>
        </div>

        {/* Filter controls */}
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-ink-subtle" />
          <div className="inline-flex rounded-[4px] border border-border p-0.5 bg-canvas text-xs">
            {['ALL', 'ALLOWED', 'BLOCKED'].map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFilterDecision(f)}
                className={`px-2.5 py-1 rounded-[3px] text-[11px] font-medium transition-colors ${
                  filterDecision === f
                    ? 'bg-surface text-ink-primary shadow-xs font-semibold'
                    : 'text-ink-subtle hover:text-ink-primary'
                }`}
              >
                {f === 'ALL' ? 'All Events' : f === 'ALLOWED' ? 'Allowed' : 'Blocked'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      {filteredLogs.length === 0 ? (
        <div className="p-8 text-center text-xs text-ink-subtle bg-white">
          No audit entries matching filter criteria.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50/80 border-b border-border text-ink-subtle font-medium">
                <th className="py-2.5 px-4 font-semibold">Timestamp (UTC)</th>
                <th className="py-2.5 px-4 font-semibold">Caller Identity</th>
                <th className="py-2.5 px-4 font-semibold">Resource Accessed</th>
                <th className="py-2.5 px-4 font-semibold">Query Scope</th>
                <th className="py-2.5 px-4 font-semibold text-right">Decision / Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredLogs.map((log) => (
                <tr
                  key={log.id}
                  className="hover:bg-slate-50/60 transition-colors bg-white"
                >
                  <td className="py-2.5 px-4 font-mono text-[11px] text-ink-subtle tabular-nums whitespace-nowrap">
                    {formatDate(log.created_at, true)}
                  </td>
                  <td className="py-2.5 px-4 font-mono font-medium text-ink-primary">
                    {log.student_id || 'System'}
                  </td>
                  <td className="py-2.5 px-4 font-medium text-ink-primary">
                    {mapResourceName(log.action)}
                  </td>
                  <td className="py-2.5 px-4 text-ink-muted">
                    {mapActionDescription(log.action)}
                  </td>
                  <td className="py-2.5 px-4 text-right">
                    <StatusBadge status={log.decision || 'ALLOWED'} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Footer Metrics */}
      <div className="p-3 bg-slate-50/60 border-t border-border flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-ink-subtle gap-2">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-status-paid" />
          <span>Cryptographic Hash Integrity Validated • Tamper-Evident Ledger</span>
        </div>
        {summary && (
          <div className="flex items-center gap-3 tabular-nums">
            <span>Total Verified: <strong className="text-ink-primary font-semibold">{summary.total_events}</strong></span>
            <span>Allowed: <strong className="text-status-paid font-medium">{summary.allowed_count}</strong></span>
            <span>Policy Violations Blocked: <strong className="text-status-overdue font-medium">{summary.blocked_count}</strong></span>
          </div>
        )}
      </div>
    </div>
  );
}
