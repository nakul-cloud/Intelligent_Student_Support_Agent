import React, { useState } from 'react';
import { X, Phone, Mail, MapPin, KeyRound, Check } from 'lucide-react';
import { studentService } from '../../api/studentService';
import { authService } from '../../api/authService';
import { useAuthStore } from '../../store/useAuthStore';
import toast from 'react-hot-toast';

/**
 * EditProfileModal
 * Allows students to immediately update contact information (phone, email, address)
 * and account password directly in the database.
 * Adheres strictly to Impeccable Operate design standards.
 */
export default function EditProfileModal({ isOpen, onClose, currentProfile, onUpdated }) {
  if (!isOpen) return null;

  const updateProfileInStore = useAuthStore((s) => s.updateProfile);

  const [phone, setPhone] = useState(currentProfile?.phone || '');
  const [email, setEmail] = useState(currentProfile?.email || '');
  const [address, setAddress] = useState(currentProfile?.address || '');
  const [newPassword, setNewPassword] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      // 1. Update contact profile if any field changed
      const profilePayload = {
        phone: phone.trim() || undefined,
        email: email.trim() || undefined,
        address: address.trim() || undefined,
      };

      const updated = await studentService.updateProfile(profilePayload);
      updateProfileInStore(updated);

      // 2. Update password if provided
      if (newPassword.trim()) {
        if (newPassword.trim().length < 6) {
          toast.error('Password must be at least 6 characters.');
          setSaving(false);
          return;
        }
        await authService.changePassword(newPassword.trim());
        toast.success('Password updated successfully.');
      }

      toast.success('Profile details saved to database.');
      if (onUpdated) onUpdated();
      onClose();
    } catch (err) {
      const msg = err.response?.data?.message || err.message || 'Failed to update profile.';
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs transition-opacity duration-200"
    >
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-lg shadow-xl overflow-hidden flex flex-col animate-modal">
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div>
            <h2 className="text-base font-bold text-slate-900 leading-tight">
              Edit Account & Contact Details
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Updates take effect immediately across all university records and portal sessions.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-[color,background-color] duration-150 ease-out active:scale-[0.97]"
            aria-label="Close modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Phone */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Phone Number
            </label>
            <div className="relative">
              <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 98765 43210"
                className="w-full text-sm pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 outline-none text-slate-900 placeholder:text-slate-400 transition-[border-color,box-shadow] duration-150 ease-out font-medium"
              />
            </div>
          </div>

          {/* Email */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Contact Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@university.edu"
                className="w-full text-sm pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 outline-none text-slate-900 placeholder:text-slate-400 transition-[border-color,box-shadow] duration-150 ease-out font-medium"
              />
            </div>
          </div>

          {/* Address */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Residential / Hostel Address
            </label>
            <div className="relative">
              <MapPin className="w-4 h-4 text-slate-400 absolute left-3.5 top-3 pointer-events-none" />
              <textarea
                rows={2}
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="Hostel Block, Room No., Campus"
                className="w-full text-sm pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 outline-none text-slate-900 placeholder:text-slate-400 resize-none transition-[border-color,box-shadow] duration-150 ease-out font-medium"
              />
            </div>
          </div>

          {/* New Password (Optional) */}
          <div className="pt-2 border-t border-slate-100">
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Change Account Password <span className="font-normal text-slate-400">(leave blank to keep current)</span>
            </label>
            <div className="relative">
              <KeyRound className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password (min. 6 chars)"
                className="w-full text-sm pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 outline-none text-slate-900 placeholder:text-slate-400 transition-[border-color,box-shadow] duration-150 ease-out font-medium"
              />
            </div>
          </div>

          {/* Modal Actions */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-semibold transition-[transform,background-color,border-color] duration-160 ease-out active:scale-[0.97]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 active:scale-[0.97] text-white text-xs font-bold transition-[transform,background-color,box-shadow] duration-160 ease-out shadow-xs disabled:opacity-50"
            >
              {saving ? (
                <span>Saving...</span>
              ) : (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>Save changes</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
