import React from 'react';
import { History, Trash2, FileText, CreditCard, Building2 } from 'lucide-react';

export default function InvoiceHistory({ invoices, selectedId, onSelectInvoice, onDeleteInvoice }) {
  if (!invoices || invoices.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-500">
        No records found for current workflow filter.
      </div>
    );
  }

  const getWorkflowBadge = (type) => {
    switch (type) {
      case 'expense_approval':
        return { label: 'Expense', icon: CreditCard, color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' };
      case 'vendor_onboarding':
        return { label: 'Vendor', icon: Building2, color: 'bg-purple-500/10 text-purple-400 border-purple-500/30' };
      default:
        return { label: 'Invoice', icon: FileText, color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' };
    }
  };

  return (
    <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-cyan-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Analysis History ({invoices.length})
          </h3>
        </div>
      </div>

      <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
        {invoices.map((inv) => {
          const isSelected = selectedId === inv.id;
          const statusBadge = {
            APPROVE: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
            APPROVED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
            RELEASE: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
            ESCALATE: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
            ESCALATED: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
            HOLD: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
            REJECT: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
            REJECTED: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
            PENDING: 'bg-slate-800 text-slate-400 border-slate-700',
            ANALYZING: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30 animate-pulse',
          }[inv.status] || 'bg-slate-800 text-slate-400 border-slate-700';

          const wfBadge = getWorkflowBadge(inv.workflow_type);
          const WfIcon = wfBadge.icon;

          return (
            <div
              key={inv.id}
              onClick={() => onSelectInvoice(inv)}
              className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between text-xs ${
                isSelected
                  ? 'bg-slate-800/90 border-cyan-500/50 shadow-md shadow-cyan-500/5'
                  : 'bg-slate-900/50 border-slate-800/80 hover:bg-slate-800/50'
              }`}
            >
              <div className="min-w-0 flex-1 pr-2">
                <div className="flex items-center gap-2">
                  <span className={`px-1.5 py-0.2 text-[9px] font-bold rounded border flex items-center gap-1 ${wfBadge.color}`}>
                    <WfIcon className="w-2.5 h-2.5" />
                    <span>{wfBadge.label}</span>
                  </span>
                  <span className="font-bold text-slate-200 truncate">{inv.vendor_name || 'Vendor'}</span>
                  <span className={`px-2 py-0.2 text-[9px] font-bold rounded-full border ml-auto ${statusBadge}`}>
                    {inv.status}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-1 font-mono">
                  <span>#{inv.invoice_number}</span>
                  <span>${inv.amount?.toFixed(2)}</span>
                  {inv.risk_score > 0 && <span className="text-cyan-400">Risk: {inv.risk_score.toFixed(0)}/100</span>}
                </div>
              </div>

              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteInvoice(inv.id);
                  }}
                  className="p-1 rounded hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 transition-colors"
                  title="Delete Record"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
