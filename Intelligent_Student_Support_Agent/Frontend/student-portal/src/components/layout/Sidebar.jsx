import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  MessageSquare,
  LayoutGrid,
  FolderOpen,
  LogOut,
  GraduationCap,
} from 'lucide-react';
import Avatar from '../atoms/Avatar';
import { useAuthStore } from '../../store/useAuthStore';

/**
 * Sidebar Component
 * High-contrast, polished navigation compliant with frontend-design specifications.
 */
export default function Sidebar() {
  const navigate = useNavigate();
  const { studentId, name, programme, batch, clearAuth } = useAuthStore();

  const handleSignOut = () => {
    clearAuth();
    navigate('/login');
  };

  const navItems = [
    {
      label: 'Ask AI Assistant',
      to: '/chat',
      icon: MessageSquare,
    },
    {
      label: 'My Overview',
      to: '/dashboard',
      icon: LayoutGrid,
    },
    {
      label: 'My Requests',
      to: '/records',
      icon: FolderOpen,
    },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 h-screen sticky top-0 overflow-y-auto select-none">
      {/* Brand & Identity */}
      <div className="flex flex-col gap-6 p-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-slate-900 flex items-center justify-center text-white shrink-0 shadow-xs">
            <GraduationCap className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="text-base font-bold text-slate-900 leading-tight">Apex University</p>
            <p className="text-xs text-slate-500 font-medium">Student Support Portal</p>
          </div>
        </div>

        {/* Student card */}
        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex items-center gap-3.5 shadow-xs">
          <Avatar name={name || studentId} size="md" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold text-slate-900 truncate leading-snug">
              {name || 'Student'}
            </p>
            <p className="text-xs font-semibold font-mono text-slate-700 truncate mt-0.5">
              {studentId}
            </p>
            <p className="text-xs text-slate-500 font-medium truncate mt-0.5">
              {programme ? programme.split(' ').slice(0, 3).join(' ') : 'Degree Candidate'}
            </p>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="flex flex-col gap-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-[background-color,border-color,color] duration-150 ease-out ${
                    isActive
                      ? 'bg-slate-100 text-slate-950 border border-slate-200/90 shadow-2xs'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 border border-transparent'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-slate-900' : 'text-slate-400'}`} />
                    <span className="flex-1">{item.label}</span>
                    {item.to === '/chat' && (
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md transition-colors ${
                          isActive
                            ? 'bg-slate-200 text-slate-900 border border-slate-300'
                            : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        AI
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Sign out */}
      <div className="p-5 border-t border-slate-200">
        <button
          onClick={handleSignOut}
          type="button"
          className="w-full flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-600 hover:text-rose-600 hover:bg-rose-50 transition-colors text-left"
        >
          <LogOut className="w-4 h-4 shrink-0" />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
}
