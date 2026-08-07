import React, { useState, useEffect } from 'react';
import { Send, ShieldAlert, Award, FileText, CheckCircle, HelpCircle, Network, Users } from 'lucide-react';

export default function InvestigatorPanel({ invoice, authToken, onSwitchTab }) {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [invoiceEvidence, setInvoiceEvidence] = useState(null);
  const [trustProfile, setTrustProfile] = useState(null);

  const suggestionChips = [
    "Why was this blocked?",
    "Has this bank account appeared before?",
    "Why is this amount abnormal?",
    "What should our auditor verify?"
  ];

  useEffect(() => {
    if (invoice && authToken) {
      fetchInvoiceEvidence();
      setMessages([]);
    }
  }, [invoice, authToken]);

  const fetchInvoiceEvidence = async () => {
    try {
      const res = await fetch(`/api/invoices/${invoice.id}/evidence`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setInvoiceEvidence(data);
        setTrustProfile(data.trust_profile || null);
      }
    } catch (e) {
      console.error('Failed to load invoice evidence:', e);
    }
  };

  const handleSend = async (textToSend) => {
    const text = textToSend || query;
    if (!text.trim() || isLoading) return;

    setMessages(prev => [...prev, { role: 'user', text }]);
    setQuery('');
    setIsLoading(true);

    try {
      const res = await fetch(`/api/invoices/${invoice.id}/investigate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`
        },
        body: JSON.stringify({ query: text })
      });
      
      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          role: 'system',
          answer: data.answer,
          evidence: data.evidence || [],
          confidence: data.confidence_basis,
          checks: data.recommended_human_checks || []
        }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'system',
          text: 'Failed to investigate invoice. Please try again.'
        }]);
      }
    } catch (e) {
      console.error('Investigation error:', e);
      setMessages(prev => [...prev, {
        role: 'system',
        text: 'Error calling AI Fraud Investigator fallback.'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!invoice) {
    return (
      <div className="glass-panel p-8 rounded-3xl border border-slate-800 text-center flex flex-col items-center justify-center min-h-[420px]">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 mb-4">
          <HelpCircle className="w-10 h-10 text-cyan-400 animate-pulse" />
        </div>
        <h3 className="text-base font-extrabold text-slate-100 uppercase tracking-wider">No transaction selected</h3>
        <p className="text-xs text-slate-400 max-w-md mt-2 leading-relaxed">
          Analyze a transaction first, then ask FraudGuard questions about risk, payments, procurement discrepancies, bank changes and connected entities.
        </p>
        {onSwitchTab && (
          <button
            onClick={() => onSwitchTab('simulator')}
            className="mt-5 px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-slate-950 rounded-xl text-xs font-black uppercase tracking-wider transition-all shadow-md shadow-cyan-500/20"
          >
            Go to Simulator
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      
      {/* Ask FraudGuard Panel (8 cols) */}
      <div className="lg:col-span-8 space-y-6">
        <div className="glass-panel p-5 rounded-3xl border border-slate-800 bg-slate-950/80 shadow-xl flex flex-col min-h-[500px]">
          
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <div className="flex items-center gap-2.5">
              <Award className="w-5 h-5 text-cyan-400" />
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  AI Investigator Workbench
                </h3>
                <p className="text-[11px] text-slate-500">
                  Interactive transaction auditing with deterministic evidence checking
                </p>
              </div>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 space-y-4 max-h-[360px] overflow-y-auto pr-1">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center text-center py-12 text-slate-600">
                <HelpCircle className="w-10 h-10 text-slate-750 mb-2" />
                <p className="text-xs font-bold text-slate-400">Ask FraudGuard about this transaction</p>
                <p className="text-[11px] text-slate-500 mt-1 max-w-[260px]">
                  Click a suggested query below or type your own question to trace specific indicators.
                </p>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`p-4 rounded-2xl max-w-[85%] border text-xs leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-cyan-500/10 border-cyan-500/20 text-cyan-200'
                    : 'bg-slate-900 border-slate-800 text-slate-300'
                }`}>
                  {msg.role === 'user' ? (
                    <p className="font-semibold">{msg.text}</p>
                  ) : (
                    <div className="space-y-3">
                      <p className="text-slate-100 font-medium leading-relaxed">{msg.answer || msg.text}</p>
                      
                      {msg.evidence && msg.evidence.length > 0 && (
                        <div className="pt-2 border-t border-slate-800/80">
                          <span className="text-[9px] uppercase font-bold tracking-widest text-slate-500 block mb-1.5">Evidence Context</span>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.evidence.map((ev, i) => (
                              <span key={i} className="text-[9px] font-mono px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 font-bold">
                                {ev}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {msg.checks && msg.checks.length > 0 && (
                        <div className="p-2.5 rounded-lg bg-cyan-950/20 border border-cyan-500/10 mt-2">
                          <span className="text-[9px] uppercase font-bold tracking-widest text-cyan-400 block mb-1">Recommended Human Checks</span>
                          <ul className="list-disc pl-4 space-y-1 text-cyan-200/90 text-[11px]">
                            {msg.checks.map((chk, i) => (
                              <li key={i}>{chk}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {msg.confidence && (
                        <span className="text-[9px] text-slate-500 block text-right italic">
                          Confidence Basis: {msg.confidence}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 text-xs flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            )}
          </div>

          {/* Quick Query Chips */}
          <div className="flex flex-wrap gap-1.5 mt-4 pt-3 border-t border-slate-900">
            {suggestionChips.map((chip, idx) => (
              <button
                key={idx}
                disabled={isLoading}
                onClick={() => handleSend(chip)}
                className="text-[10px] font-bold text-slate-400 hover:text-slate-200 bg-slate-900 hover:bg-slate-800 border border-slate-800 px-3 py-1.5 rounded-full transition-all"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Chat Input */}
          <div className="flex gap-2 mt-3">
            <input
              type="text"
              disabled={isLoading}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask a custom question about this transaction..."
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
            />
            <button
              disabled={isLoading}
              onClick={() => handleSend()}
              className="p-2.5 rounded-xl bg-cyan-400 text-slate-900 hover:bg-cyan-300 transition-colors flex items-center justify-center disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>

        </div>
      </div>

      {/* Trust Profile Sidebar (4 cols) */}
      <div className="lg:col-span-4 space-y-6">
        
        <div className="glass-panel p-5 rounded-3xl border border-slate-800 bg-slate-950/80 shadow-xl space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
              Explainability Dashboard
            </h3>
          </div>

          {invoiceEvidence ? (
            <div className="space-y-4 text-xs">
              <div>
                <h4 className="text-base font-black text-slate-100">{invoiceEvidence.vendor_name}</h4>
                <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                  {invoiceEvidence.workflow_type === 'customer_order' ? 'Goods Out Protection' : 'Invoice Fraud' }
                </p>
              </div>

              <div className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800/80 flex items-center justify-between">
                <span className="font-semibold text-slate-400">Recommended Action</span>
                <span className="text-xs font-black tracking-widest uppercase px-3 py-1 rounded-full border bg-cyan-500/10 text-cyan-300 border-cyan-500/20">
                  {invoiceEvidence.recommended_action}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60 text-center">
                  <span className="text-[9px] uppercase font-bold text-slate-500 block">Primary Findings</span>
                  <span className="text-sm font-bold font-mono mt-1 block">{invoiceEvidence.primary_findings.length}</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60 text-center">
                  <span className="text-[9px] uppercase font-bold text-slate-500 block">Risk Level</span>
                  <span className="text-sm font-bold font-mono mt-1 block">{invoiceEvidence.risk_level}</span>
                </div>
              </div>

              <div className="space-y-3">
                <span className="text-[9px] uppercase font-bold tracking-widest text-slate-500 block">Invoice Evidence</span>
                {invoiceEvidence.primary_findings.length > 0 ? (
                  <div className="space-y-2">
                    {invoiceEvidence.primary_findings.map((finding, i) => (
                      <div key={i} className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
                        {finding}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[10px] text-slate-500">No explicit findings available for this transaction.</p>
                )}
              </div>

              {invoiceEvidence.document_forensics && (
                <div className="p-3.5 rounded-2xl bg-slate-900/75 border border-slate-800 text-xs space-y-3.5">
                  <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
                    <span className="font-extrabold uppercase tracking-[0.18em] text-[10px] text-slate-400">Document Forensics</span>
                    <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase border ${
                      invoiceEvidence.document_forensics.forensic_status === 'HIGH_RISK'
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        : invoiceEvidence.document_forensics.forensic_status === 'REVIEW'
                        ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                        : 'bg-emerald-500/10 text-emerald-450 border-emerald-500/20'
                    }`}>
                      {invoiceEvidence.document_forensics.forensic_status?.replace('_', ' ')}
                    </span>
                  </div>

                  <div className="space-y-1.5 font-mono text-[11px] text-slate-350 bg-slate-950/45 p-2 rounded-xl border border-slate-800/40">
                    <span className="text-[9px] uppercase font-bold text-slate-500 block mb-1">Field Verification</span>
                    <div className="flex justify-between"><span>Vendor:</span><span className={invoiceEvidence.document_forensics.comparison_vendor === 'MATCH' ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>{invoiceEvidence.document_forensics.comparison_vendor === 'MATCH' ? '✓ MATCH' : '✕ MISMATCH'}</span></div>
                    <div className="flex justify-between"><span>Bank Account:</span><span className={invoiceEvidence.document_forensics.comparison_bank === 'MATCH' ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>{invoiceEvidence.document_forensics.comparison_bank === 'MATCH' ? '✓ MATCH' : '✕ MISMATCH'}</span></div>
                    <div className="flex justify-between"><span>Total Amount:</span><span className={invoiceEvidence.document_forensics.comparison_amount === 'MATCH' ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>{invoiceEvidence.document_forensics.comparison_amount === 'MATCH' ? '✓ MATCH' : '✕ MISMATCH'}</span></div>
                  </div>

                  {invoiceEvidence.document_forensics.forensic_signals?.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[9px] uppercase font-bold tracking-widest text-slate-500 block">Tampering Signals</span>
                      <div className="flex flex-wrap gap-1">
                        {invoiceEvidence.document_forensics.forensic_signals.map((sig, i) => (
                          <span key={i} className="px-1.5 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 font-mono text-[9px]">
                            {sig}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="p-2.5 rounded-xl bg-cyan-950/20 border border-cyan-500/10 text-cyan-200 text-[11px] leading-relaxed">
                    <span className="text-[9px] uppercase font-bold tracking-widest text-cyan-400 block mb-0.5">auditor action</span>
                    {invoiceEvidence.document_forensics.recommended_action}
                  </div>
                </div>
              )}

              {invoiceEvidence.payment_evidence && (
                <div className="p-3 rounded-2xl bg-slate-900/70 border border-slate-800 text-xs space-y-2">
                  <div className="flex items-center justify-between text-slate-400 text-[10px] uppercase tracking-[0.18em] font-semibold">
                    <span>Payment Ledger Evidence</span>
                    <span className={`px-2 py-0.5 rounded-full ${invoiceEvidence.payment_evidence.verified ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-300 border border-rose-500/20'}`}>
                      {invoiceEvidence.payment_evidence.ledger_match_found ? (invoiceEvidence.payment_evidence.verified ? 'VERIFIED' : 'MISMATCHED') : 'NOT FOUND'}
                    </span>
                  </div>
                  <div className="grid gap-2 text-[11px] text-slate-300">
                    <div className="flex justify-between"><span>Order Ref</span><span>{invoiceEvidence.payment_evidence.order_reference || 'n/a'}</span></div>
                    <div className="flex justify-between"><span>Transaction Ref</span><span>{invoiceEvidence.payment_evidence.transaction_reference || 'n/a'}</span></div>
                    <div className="flex justify-between"><span>Ledger Status</span><span>{invoiceEvidence.payment_evidence.ledger_status}</span></div>
                    <div className="flex justify-between"><span>Ledger Amount</span><span>${invoiceEvidence.payment_evidence.ledger_amount?.toFixed(2) || '0.00'}</span></div>
                    {invoiceEvidence.payment_evidence.beneficiary_name && (
                      <div className="flex justify-between"><span>Beneficiary</span><span>{invoiceEvidence.payment_evidence.beneficiary_name}</span></div>
                    )}
                  </div>
                </div>
              )}

              {invoiceEvidence.vendor_behavior && (
                <div className="p-3 rounded-2xl bg-slate-900/70 border border-slate-800 text-xs">
                  <span className="text-[9px] uppercase font-bold tracking-widest text-slate-500 block mb-2">Vendor Behavior Profile</span>
                  <div className="grid gap-2 text-slate-300 text-[11px]">
                    <div className="flex justify-between"><span>Invoice Count</span><span>{invoiceEvidence.vendor_behavior.invoice_count}</span></div>
                    <div className="flex justify-between"><span>Median Amount</span><span>${invoiceEvidence.vendor_behavior.median_amount?.toFixed(2) || '0.00'}</span></div>
                    <div className="flex justify-between"><span>Avg Amount</span><span>${invoiceEvidence.vendor_behavior.avg_amount?.toFixed(2) || '0.00'}</span></div>
                    <div className="flex justify-between"><span>Known Bank Accounts</span><span>{invoiceEvidence.vendor_behavior.known_bank_accounts?.length || 0}</span></div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="animate-pulse space-y-3 py-4">
              <div className="h-4 bg-slate-800 rounded w-1/3"></div>
              <div className="h-10 bg-slate-800 rounded"></div>
              <div className="h-20 bg-slate-800 rounded"></div>
            </div>
          )}

        </div>

      </div>

    </div>
  );
}
