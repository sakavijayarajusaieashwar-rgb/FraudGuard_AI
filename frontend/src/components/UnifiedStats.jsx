import React from 'react';
import { ShieldAlert, CheckCircle, DollarSign, Activity, FileText } from 'lucide-react';

export default function UnifiedStats({ items = [] }) {
  // Filter items for invoice_fraud
  const invoiceItems = items.filter((i) => i.workflow_type === 'invoice_fraud' || !i.workflow_type);
  const totalCount = invoiceItems.length;
  const approvedCount = invoiceItems.filter((i) => i.status === 'APPROVE' || i.status === 'APPROVED').length;
  const flaggedCount = invoiceItems.filter((i) => i.status === 'REJECT' || i.status === 'REJECTED' || i.status === 'ESCALATE' || i.status === 'ESCALATED').length;
  
  const totalProtectedValue = invoiceItems
    .filter((i) => i.status === 'REJECT' || i.status === 'REJECTED' || i.status === 'ESCALATE' || i.status === 'ESCALATED')
    .reduce((sum, item) => sum + (item.amount || 0.0), 0);

  const approvalRate = totalCount > 0 ? ((approvedCount / totalCount) * 100).toFixed(0) : 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Metric 1 */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 bg-slate-950/80">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Invoices Processed</span>
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <FileText className="w-4 h-4" />
          </div>
        </div>
        <p className="text-2xl font-bold text-slate-100 mt-2 font-mono">{totalCount}</p>
        <p className="text-[11px] text-slate-500 mt-1">Total AP invoices in ledger</p>
      </div>

      {/* Metric 2 */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 bg-slate-950/80">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Fraud & Escalated</span>
          <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
            <ShieldAlert className="w-4 h-4" />
          </div>
        </div>
        <p className="text-2xl font-bold text-rose-400 mt-2 font-mono">{flaggedCount}</p>
        <p className="text-[11px] text-slate-500 mt-1">Blocked fraudulent or high-risk invoices</p>
      </div>

      {/* Metric 3 */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 bg-slate-950/80">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Prevented Loss</span>
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <DollarSign className="w-4 h-4" />
          </div>
        </div>
        <p className="text-2xl font-bold text-emerald-300 mt-2 font-mono">
          ${totalProtectedValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </p>
        <p className="text-[11px] text-slate-500 mt-1">Prevented duplicate & scam payments</p>
      </div>

      {/* Metric 4 */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 bg-slate-950/80">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Approval Rate</span>
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <CheckCircle className="w-4 h-4" />
          </div>
        </div>
        <p className="text-2xl font-bold text-cyan-300 mt-2 font-mono">{approvalRate}%</p>
        <p className="text-[11px] text-slate-500 mt-1">{approvedCount} clean invoices approved</p>
      </div>
    </div>
  );
}
