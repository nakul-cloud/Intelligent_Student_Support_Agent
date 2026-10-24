/**
 * Formatting utilities for currency, dates, user initials, and audit mapping.
 * Adheres to Single Responsibility Principle (SRP): pure presentation helpers.
 */

/**
 * Format numeric value as currency
 * @param {number|string} amount
 * @param {string} currency
 */
export function formatCurrency(amount, currency = 'INR') {
  if (amount === null || amount === undefined || isNaN(Number(amount))) {
    return '₹0.00';
  }
  const numeric = Number(amount);
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numeric);
}

/**
 * Format date string into human-readable representation
 * @param {string|Date} dateStr
 * @param {boolean} includeTime
 */
export function formatDate(dateStr, includeTime = false) {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return String(dateStr);

    const options = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    };

    if (includeTime) {
      options.hour = '2-digit';
      options.minute = '2-digit';
      options.second = '2-digit';
      options.hour12 = false;
      return d.toLocaleDateString('en-US', options) + ' UTC';
    }

    return d.toLocaleDateString('en-US', options);
  } catch (e) {
    return String(dateStr);
  }
}

/**
 * Calculate days remaining or overdue from a due date
 * @param {string} dueDateStr
 */
export function getDaysNotice(dueDateStr) {
  if (!dueDateStr) return null;
  const now = new Date();
  const due = new Date(dueDateStr);
  const diffTime = due.getTime() - now.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return { text: `${Math.abs(diffDays)} Days Overdue`, isOverdue: true };
  } else if (diffDays === 0) {
    return { text: 'Due Today', isOverdue: false };
  } else {
    return { text: `Next Check: in ${diffDays} Days`, isOverdue: false };
  }
}

/**
 * Extract 1-2 letter uppercase initials from name
 * @param {string} name
 */
export function getInitials(name) {
  if (!name || typeof name !== 'string') return 'ST';
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return 'ST';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * Map raw backend tool names into institutional, user-friendly labels
 * @param {string} rawTool
 */
export function mapResourceName(rawTool) {
  if (!rawTool) return 'System Gateway';
  const lower = rawTool.toLowerCase();
  if (lower.includes('fee')) return 'Fee Ledger (REC-2024-4410)';
  if (lower.includes('handbook') || lower.includes('rag') || lower.includes('policy'))
    return 'Academic Handbook & Policies';
  if (lower.includes('ticket') || lower.includes('support')) return 'Student Grievance Service';
  if (lower.includes('scholarship')) return 'Scholarship Registry';
  if (lower.includes('profile')) return 'Identity & Enrollment Records';
  return rawTool;
}

/**
 * Map audit action strings into plain English
 * @param {string} action
 */
export function mapActionDescription(action) {
  if (!action) return 'Operational query';
  const lower = action.toLowerCase();
  if (lower.includes('fee')) return 'Tuition installment & balance audit';
  if (lower.includes('handbook')) return 'Institutional policy citation query';
  if (lower.includes('ticket')) return 'Support ticket creation / lookup';
  if (lower.includes('scholarship')) return 'Merit scholarship entitlement lookup';
  return action;
}
