import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { auditService } from '../../api/auditService';
import Avatar from '../atoms/Avatar';
import { useAuthStore } from '../../store/useAuthStore';

const PAGE_TITLES = {
  '/chat': 'Ask AI Assistant',
  '/dashboard': 'My Overview',
  '/records': 'My Requests',
};

/**
 * Topbar Component
 * Clean top bar with solid contrast and status indicator.
 */
export default function Topbar() {
  const { name, studentId } = useAuthStore();
  const location = useLocation();
  const [online, setOnline] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const check = async () => {
      try {
        await auditService.getHealth();
        if (isMounted) setOnline(true);
      } catch {
        if (isMounted) setOnline(false);
      }
    };
    check();
    const id = setInterval(check, 30000);
    return () => {
      isMounted = false;
      clearInterval(id);
    };
  }, []);

  const pageTitle = PAGE_TITLES[location.pathname] ?? 'Student Portal';

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 py-3.5 flex items-center justify-between sticky top-0 z-10 select-none">
      {/* Title */}
      <h2 className="text-base font-bold text-slate-900">{pageTitle}</h2>

      {/* Right controls */}
      <div className="flex items-center gap-4">
        {/* Connection status */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-700">
          <span
            className={`w-2 h-2 rounded-full ${
              online ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'
            }`}
          />
          <span className="hidden sm:inline">{online ? 'System Connected' : 'Offline'}</span>
        </div>

        {/* Student avatar monogram */}
        <div className="flex items-center gap-2.5">
          <p className="text-xs font-mono font-bold text-slate-700 hidden sm:block">{studentId}</p>
          <Avatar name={name || studentId} size="sm" />
        </div>
      </div>
    </header>
  );
}
