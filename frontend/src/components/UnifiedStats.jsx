import React from 'react';
import { ShieldAlert, CheckCircle, DollarSign, Activity, FileText } from 'lucide-react';

export default function UnifiedStats({ metrics }) {
  if (!metrics) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="glass-panel p-4 rounded-2xl border border-slate-800 bg-slate-950/80 h-24"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Metric 1 */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 bg-slate-950/80">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Transactions Protected</span>
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <FileText className="w-4 h-4" />
          </div>
        </div>
        <p className="text-2xl font-bold text-slate-100 mt-2 font-mono">{metrics.transactions_protected}</p>
        <p className="text-[11px] text-slate-500 mt-1">Total transactions monitored</p>
      </div>

      {/* Metric 2 */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 bg-slate-950/80">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Fraud Attempts Blocked</span>
          <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400">
            <ShieldAlert className="w-4 h-4" />
          </div>
        </div>
        <p className="text-2xl font-bold text-rose-400 mt-2 font-mono">{metrics.fraud_blocked}</p>
        <p className="text-[11px] text-slate-500 mt-1">{metrics.transactions_escalated} escalated for review</p>
      </div>

      {/* Metric 3 */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 bg-slate-950/80">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Potential Loss Prevented</span>
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <DollarSign className="w-4 h-4" />
          </div>
        </div>
        <p className="text-2xl font-bold text-emerald-300 mt-2 font-mono">
          ${metrics.potential_loss_prevented.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </p>
        <p className="text-[10px] text-slate-400 mt-1 flex justify-between">
          <span>Money-Out: ${metrics.money_out_prevented.toLocaleString()}</span>
          <span>Goods-Out: ${metrics.goods_out_prevented.toLocaleString()}</span>
        </p>
      </div>

      {/* Metric 4 */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 bg-slate-950/80">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Approval Rate</span>
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <CheckCircle className="w-4 h-4" />
          </div>
        </div>
        <p className="text-2xl font-bold text-cyan-300 mt-2 font-mono">{metrics.approval_rate.toFixed(0)}%</p>
        <p className="text-[11px] text-slate-500 mt-1">Clean transactions approved</p>
      </div>
    </div>
  );
}
