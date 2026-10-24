import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

/**
 * AppShell Component
 * Clean layout shell. For /chat, provides a full-bleed seamless ChatGPT/Claude workspace.
 * For other pages (overview, requests), provides comfortable centered reading padding.
 */
export default function AppShell() {
  const location = useLocation();
  const isChat = location.pathname === '/chat';

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans antialiased overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        <Topbar />
        <main
          className={`flex-1 min-w-0 ${
            isChat
              ? 'h-[calc(100vh-4rem)] overflow-hidden'
              : 'overflow-y-auto p-6 lg:p-8 max-w-7xl w-full mx-auto'
          }`}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
