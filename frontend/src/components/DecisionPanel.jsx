import React from 'react';
import { CheckCircle, AlertTriangle, XCircle, ShieldCheck, Award } from 'lucide-react';

export default function DecisionPanel({ invoice }) {
  if (!invoice || !invoice.status || invoice.status === 'PENDING' || invoice.status === 'ANALYZING') {
    return (
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 text-center flex flex-col items-center justify-center min-h-[220px]">
        <Award className="w-10 h-10 text-slate-600 mb-2 animate-pulse" />
        <h4 className="text-sm font-semibold text-slate-400">Verdict Pending</h4>
        <p className="text-xs text-slate-500 max-w-xs mt-1">
          Final decision will be issued by Decision & Critic Agents upon completion.
        </p>
      </div>
    );
  }

  const status = invoice.status;
  const riskScore = invoice.risk_score || 0.0;
  const confidence = typeof invoice.confidence === 'number' ? invoice.confidence : 0.0;

  const decisionTheme = {
    APPROVE: {
      bg: 'from-emerald-500/20 via-teal-500/10 to-slate-900',
      border: 'border-emerald-500/40',
      badge: 'badge-approve',
      icon: CheckCircle,
      iconColor: 'text-emerald-400',
      title: 'APPROVED FOR PAYMENT',
      sub: 'Invoice validated with low fraud probability.'
    },
    ESCALATE: {
      bg: 'from-amber-500/20 via-yellow-500/10 to-slate-900',
      border: 'border-amber-500/40',
      badge: 'badge-escalate',
      icon: AlertTriangle,
      iconColor: 'text-amber-400',
      title: 'ESCALATED FOR COMPLIANCE REVIEW',
      sub: 'Moderate risk indicators require manual signoff.'
    },
    REJECT: {
      bg: 'from-rose-500/20 via-red-500/10 to-slate-900',
      border: 'border-rose-500/40',
      badge: 'badge-reject',
      icon: XCircle,
      iconColor: 'text-rose-400',
      title: 'REJECTED - HIGH RISK FRAUD',
      sub: 'Invoice blocked due to severe rule violations.'
    }
  };

  const theme = decisionTheme[status] || decisionTheme.ESCALATE;
  const IconComp = theme.icon;

  return (
    <div className={`p-6 rounded-2xl border bg-gradient-to-br ${theme.bg} ${theme.border} glass-panel flex flex-col gap-4 shadow-xl`}>
      
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-xl bg-slate-950/80 border ${theme.border}`}>
            <IconComp className={`w-7 h-7 ${theme.iconColor}`} />
          </div>
          <div>
            <span className={`text-[10px] font-extrabold uppercase tracking-widest px-2.5 py-0.5 rounded-full ${theme.badge}`}>
              {status}
            </span>
            <h3 className="text-lg font-extrabold text-slate-100 font-['Outfit'] mt-1">
              {theme.title}
            </h3>
          </div>
        </div>

        {/* Risk Score & Decision Confidence */}
        <div className="grid gap-3">
          <div className="text-right p-3 rounded-xl bg-slate-950/70 border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Risk Score</span>
            <div className="flex items-baseline justify-end gap-1">
              <span className={`text-2xl font-black font-mono ${theme.iconColor}`}>
                {riskScore.toFixed(0)}
              </span>
              <span className="text-xs text-slate-500 font-mono">/ 100</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
            <div className="flex items-center justify-between gap-2 mb-2">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Decision Confidence</span>
              <span className="text-[10px] text-slate-500 font-semibold">
                {invoice.confidence !== undefined ? `${Math.round(invoice.confidence * 100)}%` : '—'}
              </span>
            </div>
            <div className="h-2.5 w-full rounded-full bg-slate-800 overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  confidence >= 0.8 ? 'bg-emerald-400' : confidence >= 0.5 ? 'bg-amber-400' : 'bg-rose-400'
                }`}
                style={{ width: `${Math.min(100, Math.max(0, confidence * 100))}%` }}
              />
            </div>
            <p className="mt-2 text-[11px] text-slate-400">
              {confidence >= 0.8
                ? 'High confidence — clear-cut case.'
                : confidence >= 0.5
                ? 'Moderate confidence — recommend human review.'
                : 'Low confidence — escalate for manual review.'}
            </p>
          </div>
        </div>
      </div>

      {/* Rationale Summary */}
      {invoice.verdict_summary && (
        <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs">
          <span className="text-slate-400 font-semibold uppercase text-[10px] block mb-1">
            Decision Agent Rationale
          </span>
          <p className="text-slate-200 leading-relaxed font-medium">
            {invoice.verdict_summary}
          </p>
        </div>
      )}

      {/* Risk Signal Explanations */}
      {invoice.risk_signals && invoice.risk_signals.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 font-semibold uppercase text-[10px]">
              Risk Agent Findings
            </span>
            <span className="text-[10px] uppercase tracking-[0.18em] text-slate-500">
              {invoice.risk_signals.length} issue{invoice.risk_signals.length === 1 ? '' : 's'}
            </span>
          </div>
          <div className="space-y-2">
            {invoice.risk_signals.map((signal, index) => (
              <div key={`${signal.rule}-${index}`} className="p-3 rounded-2xl bg-slate-900/90 border border-slate-800/90">
                <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] uppercase tracking-[0.18em] font-semibold text-slate-500">
                  <span>{signal.rule.replace(/_/g, ' ')}</span>
                  <span className={`px-2 py-0.5 rounded-full ${
                    signal.severity === 'CRITICAL' ? 'bg-rose-500/15 text-rose-300' :
                    signal.severity === 'HIGH' ? 'bg-orange-500/15 text-orange-300' :
                    signal.severity === 'MEDIUM' ? 'bg-amber-500/15 text-amber-300' :
                    'bg-slate-700/80 text-slate-300'
                  }`}>
                    {signal.severity}
                  </span>
                </div>
                <p className="mt-2 text-slate-200 text-[12px] leading-relaxed">
                  {signal.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Critic Agent Verification Stamp */}
      {invoice.critic_notes && (
        <div className="flex items-start gap-2.5 p-3 rounded-xl bg-cyan-950/30 border border-cyan-500/20 text-xs">
          <ShieldCheck className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-cyan-400 font-bold text-[10px] uppercase block">
              Critic Agent Authorization Stamp
            </span>
            <p className="text-cyan-200/90 text-[11px] mt-0.5">
              {invoice.critic_notes}
            </p>
          </div>
        </div>
      )}

    </div>
  );
}
