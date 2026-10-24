import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Sparkles } from 'lucide-react';
import StatusBadge from '../atoms/StatusBadge';
import { formatCurrency, formatDate } from '../../utils/formatters';

/**
 * FeeTable Component
 * High-contrast, clean ledger of academic tuition and semester assessments.
 */
export default function FeeTable({ feeData }) {
  const navigate = useNavigate();
  const [filterQuery, setFilterQuery] = useState('');

  if (!feeData) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-500 text-sm shadow-xs">
        No active fee records found for the current term.
      </div>
    );
  }

  const rows = [
    {
      category: 'Academic Term Tuition & Fees',
      total: feeData.total_fee,
      paid: feeData.paid,
      pending: feeData.pending,
      dueDate: feeData.due_date,
      status: feeData.status || (feeData.pending === 0 ? 'Paid' : 'Pending'),
      receipt: feeData.receipt || 'RCP-2026-0301',
    },
  ];

  const filteredRows = rows.filter((row) =>
    row.category.toLowerCase().includes(filterQuery.toLowerCase())
  );

  const handleAskAssistant = (row) => {
    navigate('/chat', {
      state: {
        preloadedPrompt: `What is the payment status and due date for my ${row.category}?`,
      },
    });
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
      {/* Header & Search */}
      <div className="p-6 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-base font-bold text-slate-900">
              Fee Statement & Dues
            </h2>
            <span className="text-xs font-semibold bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded-full border border-slate-200">
              Current Semester
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 font-medium">
            Verified university charges and receipts for the current academic session.
          </p>
        </div>

        {/* Filter Input */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            placeholder="Filter fee statements..."
            className="w-full text-xs pl-9 pr-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-slate-900 focus:bg-white text-slate-900 placeholder:text-slate-400 transition-[border-color,background-color] duration-150 ease-out shadow-xs"
          />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
              <th className="py-3.5 px-5">Category</th>
              <th className="py-3.5 px-5 text-right">Total Assessment</th>
              <th className="py-3.5 px-5 text-right">Amount Paid</th>
              <th className="py-3.5 px-5 text-right">Remaining Due</th>
              <th className="py-3.5 px-5">Due Date</th>
              <th className="py-3.5 px-5">Status</th>
              <th className="py-3.5 px-5">Receipt No.</th>
              <th className="py-3.5 px-5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {filteredRows.map((row, idx) => (
              <tr
                key={idx}
                className="hover:bg-slate-50/70 transition-colors"
              >
                <td className="py-4 px-5 font-semibold text-slate-900 text-sm">
                  {row.category}
                </td>
                <td className="py-4 px-5 text-right tabular-nums text-slate-700 text-sm font-medium">
                  {formatCurrency(row.total)}
                </td>
                <td className="py-4 px-5 text-right tabular-nums text-emerald-700 text-sm font-bold">
                  {formatCurrency(row.paid)}
                </td>
                <td className="py-4 px-5 text-right tabular-nums text-slate-900 text-sm font-extrabold">
                  {formatCurrency(row.pending)}
                </td>
                <td className="py-4 px-5 tabular-nums text-slate-600 text-xs font-medium">
                  {formatDate(row.dueDate)}
                </td>
                <td className="py-4 px-5">
                  <StatusBadge status={row.status} />
                </td>
                <td className="py-4 px-5 font-mono text-xs text-slate-600 font-semibold">
                  {row.receipt}
                </td>
                <td className="py-4 px-5 text-right">
                  <button
                    type="button"
                    onClick={() => handleAskAssistant(row)}
                    className="inline-flex items-center gap-1.5 text-xs text-slate-700 hover:text-slate-950 font-semibold px-3 py-1.5 rounded-lg hover:bg-slate-100 border border-transparent hover:border-slate-200 transition-[background-color,border-color,color] duration-150 ease-out active:scale-[0.97]"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-slate-500" />
                    <span>Ask AI</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="p-4 px-5 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-600 gap-3">
        <span className="font-medium text-slate-500">
          Official University Bursar Record · Synchronized
        </span>
        <div className="flex items-center gap-6 tabular-nums text-sm font-semibold">
          <span>Total: <strong className="text-slate-900 font-bold">{formatCurrency(feeData.total_fee)}</strong></span>
          <span>Balance Due: <strong className="text-amber-800 font-extrabold">{formatCurrency(feeData.pending)}</strong></span>
        </div>
      </div>
    </div>
  );
}
