import React from 'react';
import { FileText, ShoppingBag, ShieldCheck } from 'lucide-react';

export const WORKFLOW_CONFIG = {
  invoice_fraud: {
    key: 'invoice_fraud',
    label: 'MONEY OUT PROTECTION (Supplier Fraud)',
    shortLabel: 'Money Out',
    icon: FileText,
    badge: 'Core Demo',
    statusTag: 'Active',
    color: 'from-cyan-500/20 to-blue-500/20 text-cyan-400 border-cyan-500/40',
    activeColor: 'bg-cyan-500/20 border-cyan-400 text-cyan-200 shadow-[0_0_15px_rgba(6,182,212,0.3)]',
    queueTitle: 'Accounts Department Queue',
    queueSubtitle: 'Invoices approved for payment, ready for accounts review.',
    queueBadge: 'Ready for Payment',
    isPrimary: true,
  },
  customer_order: {
    key: 'customer_order',
    label: 'GOODS OUT PROTECTION (Customer Fraud)',
    shortLabel: 'Goods Out',
    icon: ShoppingBag,
    badge: 'New Feature',
    statusTag: 'Active',
    color: 'from-emerald-500/20 to-teal-500/20 text-emerald-400 border-emerald-500/40',
    activeColor: 'bg-emerald-500/20 border-emerald-400 text-emerald-200 shadow-[0_0_15px_rgba(16,185,129,0.3)]',
    queueTitle: 'Dispatch Department Queue',
    queueSubtitle: 'Orders verified against actual ledger payments, ready for dispatch.',
    queueBadge: 'Ready for Dispatch',
    isPrimary: false,
  },
};

export default function WorkflowSelector({ activeWorkflow, onChange }) {
  return (
    <div className="glass-panel p-2 rounded-2xl border border-slate-800 bg-slate-950/70 flex flex-wrap gap-2 items-center">
      <div className="flex-1 flex gap-2">
        {Object.values(WORKFLOW_CONFIG).map((config) => {
          const Icon = config.icon;
          const isActive = activeWorkflow === config.key;

          return (
            <button
              key={config.key}
              onClick={() => onChange(config.key)}
              className={`flex-1 sm:flex-none flex items-center gap-3 px-4 py-3 rounded-xl border transition-all duration-300 relative overflow-hidden group ${
                isActive 
                  ? config.activeColor + ' scale-[1.02]' 
                  : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:bg-slate-800/80 hover:text-slate-300'
              }`}
            >
              <div className={`p-1.5 rounded-lg ${isActive ? 'bg-black/20' : 'bg-slate-800'}`}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="text-left hidden sm:block">
                <div className="text-sm font-bold truncate leading-tight">
                  {config.label}
                </div>
                {isActive && (
                  <div className="text-[10px] uppercase font-bold tracking-wider opacity-80 mt-0.5">
                    {config.badge}
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>
      
      <div className="hidden md:flex items-center gap-2 text-xs text-emerald-400 font-semibold px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 ml-auto mr-2">
        <ShieldCheck className="w-4 h-4" />
        <span>System Operational</span>
      </div>
    </div>
  );
}
