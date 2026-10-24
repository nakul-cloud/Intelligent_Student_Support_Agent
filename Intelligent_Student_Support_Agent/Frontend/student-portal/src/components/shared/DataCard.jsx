import React from 'react';
import Button from '../atoms/Button';

/**
 * DataCard Composite Component
 * Used for top metric modules:
 * - Tuition Fee Balance
 * - Scholarship Coverage
 * - Active Support Inquiries
 * Conforms strictly to Stitch card rules: 1px border #E5E7EB, 8px radius, no drop-shadow
 */
export default function DataCard({
  label,
  statusBadge,
  mainValue,
  subValue,
  progressPercent = null,
  progressLabel = null,
  actions = [],
  children,
  className = '',
}) {
  return (
    <div
      className={`bg-surface border border-border rounded-lg p-5 flex flex-col justify-between shadow-none transition-colors ${className}`}
    >
      <div>
        {/* Header row: Category label + Status chip */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="text-[11px] font-semibold text-ink-subtle uppercase tracking-wider">
            {label}
          </span>
          {statusBadge}
        </div>

        {/* Primary headline figure */}
        <div className="mt-1">
          <div className="text-2xl font-bold text-ink-primary tracking-tight tabular-nums">
            {mainValue}
          </div>
          {subValue && (
            <p className="text-xs text-ink-muted mt-1 leading-normal font-normal">
              {subValue}
            </p>
          )}
        </div>

        {/* Optional Progress bar */}
        {progressPercent !== null && (
          <div className="mt-4">
            <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
              <div
                className="bg-accent h-2 rounded-full transition-all duration-500 ease-out"
                style={{
                  width: `${Math.min(100, Math.max(0, progressPercent))}%`,
                }}
              />
            </div>
            {progressLabel && (
              <div className="flex justify-between items-center text-[11px] text-ink-subtle mt-1.5 tabular-nums">
                <span>{progressLabel.left}</span>
                <span>{progressLabel.right}</span>
              </div>
            )}
          </div>
        )}

        {children}
      </div>

      {/* Action buttons footer */}
      {actions && actions.length > 0 && (
        <div className="flex items-center gap-2 mt-5 pt-3 border-t border-slate-100">
          {actions.map((act, idx) => (
            <Button
              key={idx}
              variant={act.variant || (idx === 0 ? 'primary' : 'secondary')}
              size="sm"
              onClick={act.onClick}
              disabled={act.disabled}
              className="flex-1"
            >
              {act.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
