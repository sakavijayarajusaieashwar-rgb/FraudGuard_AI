import React, { useState } from 'react';
import { FileText, Calendar, Code, ChevronDown, ChevronUp, Play, Sparkles, TrendingUp, ShieldAlert, AlertTriangle } from 'lucide-react';

export default function InvoicePreview({ invoice, onRunAnalysis, isAnalyzing }) {
  const [showRaw, setShowRaw] = useState(true);

  if (!invoice) {
    return (
      <div className="glass-panel p-8 rounded-2xl border border-slate-800 text-center flex flex-col items-center justify-center min-h-[300px]">
        <FileText className="w-12 h-12 text-slate-600 mb-3 animate-pulse" />
        <h3 className="text-base font-semibold text-slate-300">No Invoice Selected</h3>
        <p className="text-xs text-slate-500 max-w-xs mt-1">
          Select a preset scenario above or upload a new invoice file to load data and run analysis.
        </p>
      </div>
    );
  }

  let parsedRaw = null;
  try {
    if (invoice.raw_content && invoice.raw_content.trim().startsWith('{')) {
      parsedRaw = JSON.parse(invoice.raw_content);
    }
  } catch (e) {
    parsedRaw = null;
  }

  const lineItems = parsedRaw?.line_items || [];
  const isPending = invoice.status === 'PENDING';
  const extraData = invoice.extra_data || {};
  const behaviorProfile = extraData.behavior_profile;
  const categoryScores = extraData.category_scores;

  return (
    <div className="glass-panel p-5 rounded-2xl border border-slate-800 flex flex-col gap-4">
      
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100">{invoice.vendor_name || 'Pending Extraction'}</h3>
            <p className="text-xs text-slate-400 font-mono">Invoice #{invoice.invoice_number || 'N/A'}</p>
          </div>
        </div>

        <div className="text-right">
          <span className="text-xs text-slate-400">Total Amount</span>
          <div className="text-xl font-bold font-mono text-cyan-400">
            ${invoice.amount ? invoice.amount.toLocaleString('en-US', { minimumFractionDigits: 2 }) : '0.00'}
          </div>
        </div>
      </div>

      {/* Prominent Analyze Invoice Button */}
      {onRunAnalysis && (
        <button
          disabled={isAnalyzing}
          onClick={() => onRunAnalysis(invoice.id)}
          className={`w-full py-3 px-4 rounded-xl font-bold text-sm flex items-center justify-center gap-2.5 transition-all shadow-lg ${
            isAnalyzing
              ? 'bg-slate-800 text-slate-400 border border-slate-700 cursor-not-allowed'
              : isPending
              ? 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 border border-cyan-400/50 shadow-cyan-500/20 animate-pulse'
              : 'bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30'
          }`}
        >
          {isAnalyzing ? (
            <>
              <Sparkles className="w-4 h-4 animate-spin text-cyan-400" />
              <span>Multi-Agent Trace Running...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 text-slate-950 fill-current" />
              <span>{isPending ? 'Analyze Invoice (Run Live Trace)' : 'Re-Run Multi-Agent Trace'}</span>
            </>
          )}
        </button>
      )}

      {/* Grid Metadata */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center gap-2.5">
          <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
          <div>
            <span className="text-slate-500 block text-[10px]">Invoice Date</span>
            <span className="text-slate-200 font-medium">{invoice.invoice_date || 'N/A'}</span>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center gap-2.5">
          <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
          <div>
            <span className="text-slate-500 block text-[10px]">Status</span>
            <span className={`font-bold uppercase text-[11px] ${
              ['APPROVE', 'APPROVED', 'RELEASE'].includes(invoice.status)
                ? 'text-emerald-400'
                : ['REJECT', 'REJECTED'].includes(invoice.status)
                ? 'text-rose-400'
                : 'text-amber-400'
            }`}>
              {invoice.status || 'PENDING'}
            </span>
          </div>
        </div>
      </div>

      {/* Behavioral Profile and Categories */}
      {(behaviorProfile || categoryScores) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-1">
          {behaviorProfile && (
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col gap-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-cyan-400 mb-1">
                <TrendingUp className="w-4 h-4" />
                Behavioral Profile
              </div>
              <div className="flex justify-between text-[11px] text-slate-300">
                <span className="text-slate-500">Historical Median:</span>
                <span className="font-mono font-medium">${behaviorProfile.median_amount?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between text-[11px] text-slate-300">
                <span className="text-slate-500">Known Accounts:</span>
                <span className="font-mono">{behaviorProfile.known_bank_accounts?.length || 0}</span>
              </div>
              <div className="flex justify-between text-[11px] text-slate-300">
                <span className="text-slate-500">Past Invoices:</span>
                <span className="font-mono">{behaviorProfile.invoice_count || 0}</span>
              </div>
            </div>
          )}

          {categoryScores && (
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col gap-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-rose-400 mb-1">
                <ShieldAlert className="w-4 h-4" />
                Risk Categories
              </div>
              {Object.entries(categoryScores).map(([cat, score]) => (
                <div key={cat} className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-500 capitalize">{cat.toLowerCase()} Risk:</span>
                  <span className={`font-mono font-bold ${score > 20 ? 'text-rose-400' : 'text-amber-400'}`}>
                    {score.toFixed(0)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Line Items Table if parsed */}
      {lineItems.length > 0 && (
        <div className="mt-1">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Line Items Breakdown</h4>
          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-3 py-2">Item Description</th>
                  <th className="px-3 py-2 text-center">Qty</th>
                  <th className="px-3 py-2 text-right">Unit Price</th>
                  <th className="px-3 py-2 text-right">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {lineItems.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="px-3 py-2 font-medium">{item.description}</td>
                    <td className="px-3 py-2 text-center font-mono">{item.quantity}</td>
                    <td className="px-3 py-2 text-right font-mono">${item.unit_price?.toFixed(2)}</td>
                    <td className="px-3 py-2 text-right font-mono font-semibold text-cyan-300">${item.total?.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Raw Payload Collapsible */}
      {invoice.reasoning && (
        <div className="mt-1">
          <button
            onClick={() => setShowRaw(!showRaw)}
            className="flex items-center justify-between w-full p-2.5 rounded-xl bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800 text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Code className="w-3.5 h-3.5 text-cyan-400" />
              <span>Loaded Raw Invoice Text / Payload</span>
            </div>
            {showRaw ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showRaw && (
            <pre className="mt-2 p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] text-cyan-400 overflow-x-auto max-h-48 whitespace-pre-wrap">
              {invoice.raw_content || invoice.reasoning}
            </pre>
          )}
        </div>
      )}

    </div>
  );
}
