import { CheckCircle2, AlertOctagon, ShieldAlert, Zap, TrendingUp, DollarSign, Repeat, FileMinus, AlertTriangle } from 'lucide-react';

export default function PresetSelector({ activeWorkflow = 'invoice_fraud', onSelectPreset, isLoading }) {
  const invoicePresets = [
    {
      id: 'clean',
      title: 'Clean Supplier Invoice',
      vendor: 'Apex Cloud Infrastructure',
      amount: '$1,520.00',
      expected: 'APPROVE',
      icon: CheckCircle2,
      color: 'border-emerald-500/40 hover:border-emerald-400 bg-emerald-500/5 text-emerald-400',
      badge: 'Low Risk',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      description: 'Normal trusted vendor. Normal amount. Known identity. No duplicate.',
      signals: 'None (Clean)'
    },
    {
      id: 'clean_three_way',
      title: 'Clean Three-Way Match',
      vendor: 'Apex Cloud Infrastructure',
      amount: '$1,450.00',
      expected: 'APPROVE',
      icon: CheckCircle2,
      color: 'border-emerald-500/40 hover:border-emerald-400 bg-emerald-500/5 text-emerald-400',
      badge: '3-Way Match',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      description: 'Clean invoice matches PO and GR completely with 0 discrepancy.',
      signals: 'None (Clean)'
    },
    {
      id: 'procurement_overbilling',
      title: 'Procurement Overbilling Attack',
      vendor: 'Apex Cloud Infrastructure',
      amount: '$100,000.00',
      expected: 'REJECT',
      icon: AlertTriangle,
      color: 'border-rose-500/40 hover:border-rose-400 bg-rose-500/5 text-rose-400',
      badge: 'Quantity Discrepancy',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      description: 'Invoice charges for 100 units, but Goods Receipt records only 80 units received.',
      signals: 'GOODS_RECEIPT_AMOUNT_MISMATCH'
    },
    {
      id: 'price_manipulation',
      title: 'Price Manipulation Attack',
      vendor: 'Apex Cloud Infrastructure',
      amount: '$120,000.00',
      expected: 'REJECT',
      icon: AlertTriangle,
      color: 'border-rose-500/40 hover:border-rose-400 bg-rose-500/5 text-rose-400',
      badge: 'Price Inflated',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      description: 'Unit price raised from PO ($1,000) to Invoice ($1,200) without approval.',
      signals: 'PO_AMOUNT_MISMATCH'
    },
    {
      id: 'payment_tampering',
      title: 'Payment Instruction Tampering',
      vendor: 'Apex Cloud Infrastructure',
      amount: '$1,450.00',
      expected: 'REJECT',
      icon: ShieldAlert,
      color: 'border-rose-500/40 hover:border-rose-400 bg-rose-500/5 text-rose-400 shadow-[0_0_20px_rgba(244,63,94,0.15)] border-rose-400/60',
      badge: 'Hero Scenario',
      badgeColor: 'bg-rose-500/20 text-rose-300 border-rose-500/50',
      description: 'Clean vendor, PO, and GR. But invoice bank (****4418) is changed and matches rejected entity (****4418).',
      signals: 'INVOICE_BANK_ACCOUNT_MISMATCH, ENTITY_LINK_TO_PREVIOUS_RISK'
    },
    {
      id: 'typosquat',
      title: 'Vendor Impersonation / Wire Fraud',
      vendor: 'Acme Corp.',
      amount: '$47,000.00',
      expected: 'REJECT',
      icon: ShieldAlert,
      color: 'border-rose-500/40 hover:border-rose-400 bg-rose-500/5 text-rose-400',
      badge: 'Typosquat & Wire Risk',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      description: 'Near-matching vendor identity with suspicious banking-change instructions and large amount.',
      signals: 'VENDOR_TYPOSQUATTING, BANKING_CHANGE_UNVERIFIED'
    },
    {
      id: 'duplicate',
      title: 'Duplicate Invoice',
      vendor: 'Apex Cloud Infrastructure',
      amount: '$1,520.00',
      expected: 'REJECT',
      icon: Repeat,
      color: 'border-amber-500/40 hover:border-amber-400 bg-amber-500/5 text-amber-400',
      badge: 'Duplicate Threat',
      badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      description: 'Previously processed invoice submitted again.',
      signals: 'DUPLICATE_INVOICE_NUMBER'
    },
    {
      id: 'arithmetic_manipulation',
      title: 'Arithmetic Manipulation',
      vendor: 'Apex Cloud Infrastructure',
      amount: '$1,720.00',
      expected: 'ESCALATE',
      icon: AlertTriangle,
      color: 'border-amber-500/40 hover:border-amber-400 bg-amber-500/5 text-amber-400',
      badge: 'Math Discrepancy',
      badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      description: 'Line items sum to $1,520, but invoice total claims $1,720 ($200 unexplained difference).',
      signals: 'INVOICE_TOTAL_ARITHMETIC_MISMATCH'
    },
    {
      id: 'po_vendor_mismatch',
      title: 'Procurement PO Mismatch',
      vendor: 'Vortex Marketing Consultants',
      amount: '$1,450.00',
      expected: 'REJECT',
      icon: ShieldAlert,
      color: 'border-rose-500/40 hover:border-rose-400 bg-rose-500/5 text-rose-400',
      badge: 'PO Mismatch',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      description: 'Invoice references PO-APEX-992, but vendor name on PO is Apex Cloud Infrastructure Inc.',
      signals: 'PO_VENDOR_MISMATCH'
    },
    {
      id: 'behavioral_anomaly',
      title: 'Behavioral Anomaly',
      vendor: 'Established Vendor LLC',
      amount: '$1,470,000.00',
      expected: 'REJECT',
      icon: TrendingUp,
      color: 'border-rose-500/40 hover:border-rose-400 bg-rose-500/5 text-rose-400',
      badge: 'Behavioral Risk',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      description: 'New transaction is dramatically above historical baseline and introduces a new bank account.',
      signals: 'AMOUNT_BEHAVIOR_DEVIATION, NEW_VENDOR_BANK_ACCOUNT'
    },
    {
      id: 'connected_fraud',
      title: 'Connected Fraud Attack',
      vendor: 'Suspicious Vendor B',
      amount: '$8,900.00',
      expected: 'REJECT',
      icon: AlertOctagon,
      color: 'border-rose-500/40 hover:border-rose-400 bg-rose-500/5 text-rose-400',
      badge: 'Graph Link Threat',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      description: 'Vendor B uses a bank account previously associated with rejected Vendor C.',
      signals: 'SHARED_BANK_ACCOUNT_ACROSS_VENDORS, ENTITY_LINK_TO_PREVIOUS_RISK'
    }
  ];

  const orderPresets = [
    {
      id: 'clean_order',
      title: 'Clean Customer Order',
      vendor: 'Alice Wonderland',
      amount: '$250.00',
      expected: 'RELEASE',
      icon: CheckCircle2,
      color: 'border-emerald-500/40 hover:border-emerald-400 bg-emerald-500/5 text-emerald-400',
      badge: 'Payment Verified',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      description: 'Order amount exactly matches settled transaction in ledger.',
      signals: 'None (Clean)'
    },
    {
      id: 'fake_payment',
      title: 'Fake Payment Claim',
      vendor: 'Bob Builder',
      amount: '$5,000.00',
      expected: 'HOLD',
      icon: ShieldAlert,
      color: 'border-rose-500/40 hover:border-rose-400 bg-rose-500/5 text-rose-400',
      badge: 'Missing Payment',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      description: 'Customer claims payment was completed, but ledger contains no matching transaction.',
      signals: 'PAYMENT_NOT_FOUND'
    },
    {
      id: 'partial_payment',
      title: 'Partial Payment Attack',
      vendor: 'Charlie Check',
      amount: '$470,000.00',
      expected: 'HOLD',
      icon: FileMinus,
      color: 'border-rose-500/40 hover:border-rose-400 bg-rose-500/5 text-rose-400',
      badge: 'Amount Mismatch',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      description: 'Customer claims $470k paid, but ledger only shows $47k received.',
      signals: 'PAYMENT_AMOUNT_MISMATCH'
    },
    {
      id: 'reused_transaction',
      title: 'Reused Transaction Attack',
      vendor: 'Dave Duplicate',
      amount: '$250.00',
      expected: 'HOLD',
      icon: Repeat,
      color: 'border-amber-500/40 hover:border-amber-400 bg-amber-500/5 text-amber-400',
      badge: 'Txn Reused',
      badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      description: 'Customer attempts to use a transaction reference already associated with another order.',
      signals: 'DUPLICATE_TRANSACTION_REFERENCE'
    }
  ];

  const presets = activeWorkflow === 'customer_order' ? orderPresets : invoicePresets;

  return (
    <div className="glass-panel p-5 rounded-3xl border border-rose-500/30 bg-slate-950/90 shadow-[0_0_30px_rgba(244,63,94,0.1)]">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400">
            <Zap className="w-5 h-5 fill-rose-500/20" />
          </div>
          <div>
            <h2 className="text-lg font-black uppercase tracking-widest text-slate-100">
              ATTACK FRAUDGUARD
            </h2>
            <p className="text-xs text-slate-400 mt-0.5 max-w-xl">
              Simulate real-world transaction fraud and watch FraudGuard investigate it in real time.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {presets.map((preset) => {
          const IconComponent = preset.icon;
          const isHeroScenario = preset.id === 'procurement_overbilling' || preset.id === 'payment_tampering';
          return (
            <button
              key={preset.id}
              disabled={isLoading}
              onClick={() => onSelectPreset(preset.id)}
              className={`p-4 rounded-2xl border text-left transition-all duration-200 glass-card group hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed flex flex-col justify-between ${preset.color} ${isHeroScenario ? 'ring-2 ring-cyan-500/20' : ''}`}
            >
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="p-2 rounded-xl bg-slate-900/80 border border-slate-800 shadow-md">
                    <IconComponent className="w-4 h-4" />
                  </div>
                  <div className="flex flex-col items-end gap-1.5">
                    {isHeroScenario && (
                      <span 
                        className="text-[9px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full border animate-pulse"
                        style={{
                          color: 'var(--accent-hero)',
                          backgroundColor: 'var(--accent-hero-bg)',
                          borderColor: 'var(--accent-hero-border)',
                        }}
                      >
                        ★ HERO DEMO
                      </span>
                    )}
                    <span className={`text-[9px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full border ${preset.badgeColor}`}>
                      {preset.badge}
                    </span>
                  </div>
                </div>
                <h3 className="text-sm sm:text-base font-extrabold text-slate-105 group-hover:text-white transition-colors">
                  {preset.title}
                </h3>
                <p className="text-[12px] text-slate-400 mt-2 line-clamp-3 leading-relaxed min-h-[54px]">
                  {preset.description}
                </p>
                <div className="mt-3 p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/50">
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block mb-0.5">Expected Signals</span>
                  <span className="text-[11px] text-rose-300 font-mono line-clamp-2 leading-tight">{preset.signals}</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">Value At Risk</span>
                  <span className="font-mono text-slate-200 font-black text-base">{preset.amount}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">Expected</span>
                  <span className={`text-sm font-black tracking-wider uppercase ${preset.expected === 'APPROVE' || preset.expected === 'RELEASE' ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {preset.expected}
                  </span>
                </div>
              </div>
              
              <div className="mt-3 w-full py-2 bg-slate-900/80 hover:bg-slate-800 border border-slate-700/50 rounded-lg text-center text-[10px] font-bold uppercase tracking-widest text-slate-300 transition-colors">
                Launch Attack
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
