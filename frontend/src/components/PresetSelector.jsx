import React from 'react';
import { CheckCircle2, AlertOctagon, ShieldAlert, Sparkles, ShoppingBag } from 'lucide-react';

export default function PresetSelector({ activeWorkflow = 'invoice_fraud', onSelectPreset, isLoading }) {
  const invoicePresets = [
    {
      id: 'clean',
      title: 'Clean Invoice',
      vendor: 'Apex Cloud Infrastructure Inc',
      amount: '$1,520.00',
      expected: 'APPROVE',
      icon: CheckCircle2,
      color: 'border-emerald-500/40 hover:border-emerald-400 bg-emerald-500/5 text-emerald-400',
      badge: 'Low Risk',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      description: 'Standard recurring cloud infrastructure billing with verified vendor identity.',
    },
    {
      id: 'typosquat',
      title: 'Typosquat / Fraud Invoice',
      vendor: 'Acme Corp.',
      amount: '$47,000.00',
      expected: 'REJECT',
      icon: ShieldAlert,
      color: 'border-rose-500/40 hover:border-rose-400 bg-rose-500/5 text-rose-400',
      badge: 'Typosquat & Wire Risk',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      description: 'Unverified vendor name match + unverified banking detail change request.',
    },
    {
      id: 'duplicate',
      title: 'Duplicate Invoice #',
      vendor: 'Apex Cloud Infrastructure Inc',
      amount: '$1,520.00',
      expected: 'REJECT',
      icon: AlertOctagon,
      color: 'border-amber-500/40 hover:border-amber-400 bg-amber-500/5 text-amber-400',
      badge: 'Duplicate Threat',
      badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      description: 'Re-submitted invoice number matching previously approved ledger item.',
    },
  ];

  const orderPresets = [
    {
      id: 'clean_order',
      title: 'Verified Customer Order',
      vendor: 'Alice Wonderland',
      amount: '$250.00',
      expected: 'APPROVE',
      icon: CheckCircle2,
      color: 'border-emerald-500/40 hover:border-emerald-400 bg-emerald-500/5 text-emerald-400',
      badge: 'Payment Verified',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      description: 'Customer order amount matches settled transaction in deterministic Payment Ledger.',
    },
    {
      id: 'fake_payment',
      title: 'Fake Payment Proof',
      vendor: 'Bob Builder',
      amount: '$5,000.00',
      expected: 'REJECT',
      icon: ShieldAlert,
      color: 'border-rose-500/40 hover:border-rose-400 bg-rose-500/5 text-rose-400',
      badge: 'Ledger Mismatch',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      description: 'Payment claim is missing from Payment Ledger. Possible screenshot fraud.',
    },
  ];

  const presets = activeWorkflow === 'customer_order' ? orderPresets : invoicePresets;
  const title = activeWorkflow === 'customer_order' ? 'Customer Order Verification Scenarios' : 'Invoice Fraud Demo Scenarios';
  const subtitle = activeWorkflow === 'customer_order' ? 'Click scenario to run payment-to-order ledger verification' : 'Click any scenario to populate raw invoice payload — then hit "Analyze Invoice" to run live trace';

  return (
    <div className="glass-panel p-5 rounded-3xl border border-slate-800 bg-slate-950/80 shadow-2xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-xl border ${activeWorkflow === 'customer_order' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'}`}>
            <Sparkles className="w-4 h-4 animate-spin" style={{ animationDuration: '6s' }} />
          </div>
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
              {title}
            </h2>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {subtitle}
            </p>
          </div>
        </div>
        <span className="text-[11px] font-semibold text-slate-400 px-3 py-1 rounded-full bg-slate-900 border border-slate-800">
          {presets.length} Preset Demos Ready
        </span>
      </div>

      <div className={`grid grid-cols-1 md:grid-cols-${Math.min(presets.length, 3)} gap-4`}>
        {presets.map((preset) => {
          const IconComponent = preset.icon;
          return (
            <button
              key={preset.id}
              disabled={isLoading}
              onClick={() => onSelectPreset(preset.id)}
              className={`p-4 rounded-2xl border text-left transition-all duration-200 glass-card group hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed flex flex-col justify-between ${preset.color}`}
            >
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 shadow-md">
                    <IconComponent className="w-5 h-5" />
                  </div>
                  <span className={`text-[10px] font-extrabold uppercase tracking-wider px-2.5 py-1 rounded-full border ${preset.badgeColor}`}>
                    {preset.badge}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                  {preset.title}
                </h3>
                <p className="text-xs font-semibold text-slate-300 mt-1">{preset.vendor}</p>
                <p className="text-[11px] text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
                  {preset.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <div>
                  <span className="text-[10px] text-slate-500 block">Amount</span>
                  <span className="font-mono text-slate-200 font-bold text-sm">{preset.amount}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 block">Expected Result</span>
                  <span className={`text-xs font-black tracking-wider uppercase ${preset.expected === 'APPROVE' ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {preset.expected}
                  </span>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
