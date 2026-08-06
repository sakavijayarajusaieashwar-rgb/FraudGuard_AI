import React, { useState, useEffect } from 'react';
import { Send, ShieldAlert, Award, FileText, CheckCircle, HelpCircle, Network, Users } from 'lucide-react';

export default function InvestigatorPanel({ invoice, authToken }) {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [trustProfile, setTrustProfile] = useState(null);

  const suggestionChips = [
    "Why was this blocked?",
    "Has this bank account appeared before?",
    "Why is this amount abnormal?",
    "What should our auditor verify?"
  ];

  useEffect(() => {
    if (invoice && authToken) {
      fetchTrustProfile();
      // Clear chat history when switching invoices
      setMessages([]);
    }
  }, [invoice, authToken]);

  const fetchTrustProfile = async () => {
    try {
      const res = await fetch(`/api/trust-profile?entity_name=${encodeURIComponent(invoice.vendor_name)}&entity_type=VENDOR`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      if (res.ok) {
        setTrustProfile(await res.json());
      }
    } catch (e) {
      console.error('Failed to load trust profile:', e);
    }
  };

  const handleSend = async (textToSend) => {
    const text = textToSend || query;
    if (!text.trim() || isLoading) return;

    // Add user message to log
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
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 text-center flex flex-col items-center justify-center min-h-[400px] text-slate-500">
        <HelpCircle className="w-12 h-12 text-slate-700 mb-2" />
        <p className="text-sm font-bold">No Transaction Selected</p>
        <p className="text-xs text-slate-600 mt-1">Select an invoice or order from the sidebar to launch investigation workbench.</p>
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
                      
                      {/* Structured Evidence Tags */}
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

                      {/* Structured Human Verification checks */}
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
        
        {/* Vendor Trust Profile Widget */}
        <div className="glass-panel p-5 rounded-3xl border border-slate-800 bg-slate-950/80 shadow-xl space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
              Entity Trust Profile
            </h3>
          </div>

          {trustProfile ? (
            <div className="space-y-4 text-xs">
              <div>
                <h4 className="text-base font-black text-slate-100">{trustProfile.entity_name}</h4>
                <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                  Verified Supplier
                </p>
              </div>

              {/* Trust/Risk Badge */}
              <div className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800/80 flex items-center justify-between">
                <span className="font-semibold text-slate-400">Risk Assessment:</span>
                <span className={`text-xs font-black tracking-widest uppercase px-3 py-1 rounded-full border ${
                  trustProfile.risk_level === 'HIGH' ? 'bg-rose-500/15 text-rose-400 border-rose-500/30' :
                  trustProfile.risk_level === 'MEDIUM' ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' :
                  'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                }`}>
                  {trustProfile.risk_level} RISK
                </span>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60 text-center">
                  <span className="text-[9px] uppercase font-bold text-slate-500 block">Total Audits</span>
                  <span className="text-sm font-bold font-mono mt-1 block">{trustProfile.total_transactions}</span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60 text-center">
                  <span className="text-[9px] uppercase font-bold text-slate-500 block">Avg Amount</span>
                  <span className="text-sm font-bold font-mono mt-1 block">${Math.round(trustProfile.avg_amount).toLocaleString()}</span>
                </div>
              </div>

              {/* Status Breakdown */}
              <div className="p-3.5 rounded-2xl bg-slate-900/50 border border-slate-800/50 space-y-2">
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-slate-400">Approved Payments:</span>
                  <span className="font-bold text-emerald-400 font-mono">{trustProfile.approved_count}</span>
                </div>
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-slate-400">Escalated Audits:</span>
                  <span className="font-bold text-amber-400 font-mono">{trustProfile.escalated_count}</span>
                </div>
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-slate-400">Blocked Fraud:</span>
                  <span className="font-bold text-rose-400 font-mono">{trustProfile.rejected_count}</span>
                </div>
              </div>

              {/* Bank Accounts Profile */}
              <div>
                <span className="text-[9px] uppercase font-bold tracking-widest text-slate-500 block mb-2">Known Destination Accounts</span>
                <div className="space-y-1.5">
                  {trustProfile.known_bank_accounts.map((acct, i) => (
                    <div key={i} className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800/80 font-mono font-bold text-slate-300">
                      {acct}
                    </div>
                  ))}
                  {trustProfile.known_bank_accounts.length === 0 && (
                    <p className="text-[10px] text-slate-600 italic">No bank account records found.</p>
                  )}
                </div>
              </div>

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
