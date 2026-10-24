import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  Sparkles,
  CreditCard,
  Award,
  MessageCircle,
  ArrowRight,
  Phone,
  Mail,
  MapPin,
  Edit3,
} from 'lucide-react';
import { useStudentOverview } from '../hooks/useStudentOverview';
import Avatar from '../components/atoms/Avatar';
import StatusBadge from '../components/atoms/StatusBadge';
import Button from '../components/atoms/Button';
import Skeleton from '../components/atoms/Skeleton';
import FeeTable from '../components/shared/FeeTable';
import EditProfileModal from '../components/shared/EditProfileModal';
import {
  formatCurrency,
  formatDate,
  getDaysNotice,
} from '../utils/formatters';

/**
 * DashboardPage – My Overview
 * Clean, high-contrast, student-centric financial and academic overview.
 * Adheres strictly to Impeccable Operate standards.
 */
export default function DashboardPage() {
  const navigate = useNavigate();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const { profile, fees, scholarship, tickets, loading, error, refetch } =
    useStudentOverview();

  if (loading) {
    return (
      <div className="flex flex-col gap-6 max-w-6xl mx-auto">
        <Skeleton height="h-24" rounded="rounded-2xl" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <Skeleton height="h-44" rounded="rounded-2xl" />
          <Skeleton height="h-44" rounded="rounded-2xl" />
          <Skeleton height="h-44" rounded="rounded-2xl" />
        </div>
        <Skeleton height="h-64" rounded="rounded-2xl" />
      </div>
    );
  }

  if (error && !profile) {
    return (
      <div className="p-10 bg-white border border-slate-200 rounded-2xl text-center flex flex-col items-center justify-center gap-4 max-w-xl mx-auto my-12 shadow-xs">
        <div className="w-12 h-12 rounded-full bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-base font-bold text-slate-900">Could not load your records</h2>
          <p className="text-sm text-slate-500 mt-1">Please check your connection and try again.</p>
        </div>
        <Button variant="secondary" size="md" onClick={refetch}>
          Try again
        </Button>
      </div>
    );
  }

  const daysNotice = fees?.due_date ? getDaysNotice(fees.due_date) : null;
  const openTickets = tickets.filter(
    (t) =>
      (t.status || '').toLowerCase() === 'open' ||
      (t.status || '').toLowerCase() === 'in review'
  );

  return (
    <div className="flex flex-col gap-6 max-w-6xl mx-auto pb-10">

      {/* ── Student Identity Header with Contact Details ── */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col gap-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-5">
          <div className="flex items-center gap-4">
            <Avatar name={profile?.name || profile?.student_id} size="lg" />
            <div>
              <div className="flex flex-wrap items-center gap-2.5 mb-1">
                <h1 className="text-lg font-bold text-slate-900 leading-tight">
                  {profile?.name || 'Enrolled Student'}
                </h1>
                <StatusBadge status={profile?.status || 'Good Standing'} />
              </div>
              <p className="text-sm text-slate-600 font-medium">
                <span className="font-mono text-indigo-700 font-semibold">{profile?.student_id}</span>
                {' · '}
                <span>{profile?.programme || 'Post Graduate Programme'}</span>
                {' · '}
                <span className="text-slate-500">Batch {profile?.batch || '2025-27'}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 self-start sm:self-auto">
            <button
              type="button"
              onClick={() => setIsEditModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl border border-slate-200 hover:border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-[transform,background-color,border-color] duration-160 ease-out active:scale-[0.97]"
            >
              <Edit3 className="w-3.5 h-3.5 text-slate-500" />
              <span>Edit Details</span>
            </button>

            <button
              type="button"
              onClick={() => navigate('/chat')}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 active:scale-[0.97] text-white text-xs font-bold shadow-xs transition-[transform,background-color] duration-160 ease-out"
            >
              <Sparkles className="w-4 h-4 text-slate-300" />
              <span>Ask AI Assistant</span>
            </button>
          </div>
        </div>

        {/* Contact information strip */}
        <div className="pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-slate-600">
          <div className="flex items-center gap-2">
            <Phone className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="font-medium text-slate-500">Phone:</span>
            <span className="font-semibold text-slate-900 tabular-nums">
              {profile?.phone || '+91 98765 43210'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Mail className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="font-medium text-slate-500">Email:</span>
            <span className="font-semibold text-slate-900 truncate">
              {profile?.email || 'rahul.sharma@university.edu'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="font-medium text-slate-500">Campus:</span>
            <span className="font-semibold text-slate-900 truncate">
              {profile?.address || 'Hostel Block-B, Room 204'}
            </span>
          </div>
        </div>
      </div>


      {/* ── Payment Due Notice ── */}
      {fees && fees.pending > 0 && (
        <div className="bg-amber-50/90 border border-amber-300 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-amber-100 border border-amber-200 flex items-center justify-center shrink-0">
              <AlertCircle className="w-5 h-5 text-amber-800" />
            </div>
            <div>
              <p className="text-base font-bold text-amber-950">
                {formatCurrency(fees.pending)} outstanding due by {formatDate(fees.due_date)}
              </p>
              <p className="text-sm text-amber-800 mt-0.5">
                Clear pending dues to ensure continuous access to exams and campus facilities.
              </p>
            </div>
          </div>
          {daysNotice && (
            <span
              className={`text-xs font-bold px-3.5 py-1.5 rounded-full border self-start sm:self-auto whitespace-nowrap shadow-xs ${
                daysNotice.isOverdue
                  ? 'bg-rose-100 text-rose-700 border-rose-300'
                  : 'bg-white text-amber-900 border-amber-300'
              }`}
            >
              {daysNotice.text}
            </span>
          )}
        </div>
      )}

      {/* ── 3 Summary Metric Cards ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">

        {/* 1. Tuition Balance */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col justify-between hover:border-slate-300 transition-[border-color,box-shadow] duration-160 ease-out animate-card-1">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Tuition Balance</span>
              <StatusBadge status={fees?.status || (fees?.pending === 0 ? 'Paid' : 'Pending')} />
            </div>

            <p className="text-2xl font-bold text-slate-950 tabular-nums tracking-tight">
              {fees ? formatCurrency(fees.pending) : '₹0'}
            </p>
            <p className="text-xs text-slate-500 font-medium mt-1">
              {fees ? `Total assessment: ${formatCurrency(fees.total_fee)}` : 'No balance due'}
            </p>

            {/* Progress bar */}
            {fees && (
              <div className="mt-4">
                <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1.5">
                  <span>Paid so far</span>
                  <span className="font-bold text-slate-900">{formatCurrency(fees.paid)}</span>
                </div>
                <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200/50">
                  <div
                    className="h-full bg-slate-900 rounded-full transition-[width] duration-600 ease-[cubic-bezier(0.23,1,0.32,1)]"
                    style={{ width: `${Math.min(100, (fees.paid / (fees.total_fee || 1)) * 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={() =>
              navigate('/chat', {
                state: { preloadedPrompt: 'What is my current fee status and how much do I owe?' },
              })
            }
            className="mt-5 inline-flex items-center gap-1.5 text-xs font-bold text-slate-700 hover:text-slate-950 transition-colors pt-3 border-t border-slate-100"
          >
            <span>Ask AI about fees</span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
          </button>
        </div>

        {/* 2. Scholarship Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col justify-between hover:border-slate-300 transition-[border-color,box-shadow] duration-160 ease-out animate-card-2">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Scholarship</span>
              <StatusBadge status={scholarship ? 'Active' : 'None'} />
            </div>

            <p className="text-2xl font-bold text-slate-950 tabular-nums tracking-tight">
              {scholarship
                ? `${formatCurrency(scholarship.amount_per_semester)}`
                : '—'}
            </p>
            <p className="text-xs text-slate-500 font-medium mt-1">
              {scholarship
                ? `${scholarship.scholarship_type} (${scholarship.percentage}% grant)`
                : 'No institutional scholarship applied'}
            </p>

            {/* Grant Bar */}
            {scholarship && (
              <div className="mt-4">
                <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1.5">
                  <span>Semester coverage</span>
                  <span className="font-bold text-emerald-800">{scholarship.percentage}%</span>
                </div>
                <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200/50">
                  <div
                    className="h-full bg-emerald-600 rounded-full transition-[width] duration-600 ease-[cubic-bezier(0.23,1,0.32,1)]"
                    style={{ width: `${scholarship.percentage}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={() =>
              navigate('/chat', {
                state: { preloadedPrompt: 'What are the criteria and rules to maintain my scholarship?' },
              })
            }
            className="mt-5 inline-flex items-center gap-1.5 text-xs font-bold text-slate-700 hover:text-slate-950 transition-colors pt-3 border-t border-slate-100"
          >
            <span>Ask about scholarships</span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
          </button>
        </div>

        {/* 3. Open Requests Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col justify-between hover:border-slate-300 transition-[border-color,box-shadow] duration-160 ease-out animate-card-3">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Support Requests</span>
              <StatusBadge status={openTickets.length > 0 ? `${openTickets.length} Open` : 'All Clear'} />
            </div>

            <p className="text-2xl font-bold text-slate-950 tabular-nums tracking-tight">
              {openTickets.length}
            </p>
            <p className="text-xs text-slate-500 font-medium mt-1">
              {openTickets.length > 0
                ? `Latest: ${openTickets[0].description.slice(0, 48)}...`
                : 'No unresolved support requests.'}
            </p>
          </div>

          <button
            type="button"
            onClick={() => navigate('/records')}
            className="mt-5 inline-flex items-center gap-1.5 text-xs font-bold text-slate-700 hover:text-slate-950 transition-colors pt-3 border-t border-slate-100"
          >
            <span>View all requests</span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
          </button>
        </div>

      </div>

      {/* ── Fee Statement & Dues Table ── */}
      <FeeTable feeData={fees} />

      {/* ── Callout Banner ── */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-5 shadow-card">
        <div>
          <h2 className="text-base font-bold text-white">Have questions about your academic standing or fees?</h2>
          <p className="text-sm text-slate-400 mt-1">
            The AI Student Assistant is trained on the university catalog and your individual student record.
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/chat')}
          className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] text-white text-sm font-semibold shadow-xs transition-all shrink-0 self-start sm:self-auto"
        >
          <Sparkles className="w-4 h-4" />
          <span>Open AI Assistant</span>
        </button>
      </div>

      {/* ── Edit Profile Modal ── */}
      <EditProfileModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        currentProfile={profile}
        onUpdated={refetch}
      />

    </div>
  );
}
