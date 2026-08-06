import React from 'react';
import { CheckCircle2, AlertTriangle, AlertOctagon, Calculator, Sparkles } from 'lucide-react';

export default function PresetSelector({ onSelectPreset, isLoading }) {
  const presets = [
    {
      id: 'clean',
      title: 'Clean Invoice',
      vendor: 'Apex Cloud Infrastructure',
      amount: '$1,450.00',
      expected: 'APPROVE',
      icon: CheckCircle2,
      color: 'border-emerald-500/30 hover:border-emerald-500/80 bg-emerald-500/5 text-emerald-400',
      badge: 'Low Risk',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    },
    {
      id: 'duplicate',
      title: 'Duplicate Invoice #',
      vendor: 'Global Office Supplies',
      amount: '$3,200.00',
      expected: 'REJECT',
      icon: AlertOctagon,
      color: 'border-rose-500/30 hover:border-rose-500/80 bg-rose-500/5 text-rose-400',
      badge: 'Duplicate Threat',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    },
    {
      id: 'suspicious_amount',
      title: 'Inflated Amount & Urgent Wire',
      vendor: 'Vortex Marketing',
      amount: '$65,000.00',
      expected: 'ESCALATE / REJECT',
      icon: AlertTriangle,
      color: 'border-amber-500/30 hover:border-amber-500/80 bg-amber-500/5 text-amber-400',
      badge: 'High Value Anomaly',
      badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    },
    {
      id: 'suspicious_math',
      title: 'Line Item Math Mismatch',
      vendor: 'Nexus Logistics',
      amount: '$12,500.00',
      expected: 'REJECT',
      icon: Calculator,
      color: 'border-purple-500/30 hover:border-purple-500/80 bg-purple-500/5 text-purple-400',
      badge: 'Math Discrepancy',
      badgeColor: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    },
  ];

  return (
    <div className="glass-panel p-5 rounded-2xl border border-slate-800">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cyan-400 animate-spin" style={{ animationDuration: '6s' }} />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
            Hackathon Live Demo Scenarios
          </h2>
        </div>
        <span className="text-xs text-slate-400">Click any preset to trigger instant agent evaluation</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {presets.map((preset) => {
          const IconComponent = preset.icon;
          return (
            <button
              key={preset.id}
              disabled={isLoading}
              onClick={() => onSelectPreset(preset.id)}
              className={`p-4 rounded-xl border text-left transition-all duration-200 glass-card group hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed ${preset.color}`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                  <IconComponent className="w-5 h-5" />
                </div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${preset.badgeColor}`}>
                  {preset.badge}
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                {preset.title}
              </h3>
              <p className="text-xs text-slate-400 mt-1 truncate">{preset.vendor}</p>
              <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-800/80 text-xs">
                <span className="font-mono text-slate-300 font-medium">{preset.amount}</span>
                <span className="text-[10px] text-slate-400">Expected: {preset.expected}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
