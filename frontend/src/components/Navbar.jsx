import React from 'react';
import { ShieldCheck, Cpu, RefreshCw, Layers, Sun, Moon } from 'lucide-react';

export default function Navbar({ backendConnected, onResetDB, userEmail, onLogout, theme, setTheme }) {
  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <div className="relative p-2.5 rounded-xl bg-gradient-to-tr from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 text-cyan-400 shadow-lg shadow-cyan-500/10">
            <ShieldCheck className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold font-['Outfit'] tracking-tight bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent">
                FraudGuard AI
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 rounded-full">
                Multi-Agent
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous Invoice & Expense Risk Engine</p>
          </div>
        </div>

        {/* Status Indicators & Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs">
            <span className={`w-2 h-2 rounded-full ${backendConnected ? 'bg-emerald-400 animate-ping' : 'bg-rose-500'}`} />
            <span className="text-slate-300 font-medium">
              {backendConnected ? 'Backend Live' : 'Connecting to API...'}
            </span>
          </div>

          {userEmail && (
            <div className="px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-xs text-cyan-200">
              Signed in as <span className="font-semibold text-white">{userEmail}</span>
            </div>
          )}

          <div className="flex items-center gap-2">
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="flex items-center justify-center p-2 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-slate-650 text-slate-300 hover:text-white transition-all"
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400 animate-spin-slow" /> : <Moon className="w-4 h-4 text-cyan-400" />}
            </button>
            <button
              onClick={onResetDB}
              className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-slate-600 rounded-lg transition-all"
              title="Reset active invoices & demo state"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset Demo State</span>
            </button>
            {onLogout && (
              <button
                onClick={onLogout}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-rose-500/10 hover:bg-rose-500/15 border border-rose-500/20 rounded-lg transition-all"
                title="Sign out of FraudGuard AI"
              >
                <span>Logout</span>
              </button>
            )}
          </div>
        </div>

      </div>
    </header>
  );
}
