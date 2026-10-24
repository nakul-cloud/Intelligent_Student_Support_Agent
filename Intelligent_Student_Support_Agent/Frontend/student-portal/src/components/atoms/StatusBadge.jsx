import React from 'react';

/**
 * StatusBadge Component
 * Pill status indicator with high-contrast borders and bold typography.
 */
export default function StatusBadge({ status, className = '' }) {
  if (!status) return null;

  const raw = String(status).trim();
  const normalized = raw.toLowerCase();

  let theme = {
    bg: 'bg-slate-100',
    text: 'text-slate-800',
    border: 'border-slate-300',
  };

  if (
    normalized.includes('paid in full') ||
    normalized === 'paid' ||
    normalized === 'cleared' ||
    normalized === 'resolved' ||
    normalized === 'approved' ||
    normalized === 'good standing' ||
    normalized === 'active' ||
    normalized === 'enrolled'
  ) {
    theme = {
      bg: 'bg-emerald-50',
      text: 'text-emerald-800',
      border: 'border-emerald-300',
    };
  } else if (
    normalized.includes('partial') ||
    normalized.includes('pending') ||
    normalized === 'open' ||
    normalized === 'in review'
  ) {
    theme = {
      bg: 'bg-amber-50',
      text: 'text-amber-900',
      border: 'border-amber-300',
    };
  } else if (
    normalized.includes('overdue') ||
    normalized === 'blocked' ||
    normalized === 'rejected' ||
    normalized.includes('hold')
  ) {
    theme = {
      bg: 'bg-rose-50',
      text: 'text-rose-900',
      border: 'border-rose-300',
    };
  }

  // Friendly human labels
  let displayLabel = raw;
  if (normalized === 'allowed') displayLabel = 'Approved';
  if (normalized === 'blocked') displayLabel = 'Hold on account';

  return (
    <span
      className={`inline-flex items-center px-3 py-0.5 rounded-full text-xs font-bold border leading-tight tabular-nums whitespace-nowrap select-none shadow-xs ${theme.bg} ${theme.text} ${theme.border} ${className}`}
    >
      {displayLabel}
    </span>
  );
}
