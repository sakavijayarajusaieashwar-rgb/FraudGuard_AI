import React, { useState } from 'react';
import { FileText, Calendar, Code, ChevronDown, ChevronUp, Play, Sparkles, TrendingUp, ShieldAlert, AlertTriangle } from 'lucide-react';

export default function InvoicePreview({ invoice, onRunAnalysis, isAnalyzing }) {
  const [showRaw, setShowRaw] = useState(true);

  if (!invoice) {
    return (
      <div className="glass-panel p-8 rounded-2xl border border-slate-800 text-center flex flex-col items-center justify-center min-h-[300px]">
        <FileText className="w-12 h-12 text-cyan-400 mb-3 animate-pulse" />
        <h3 className="text-base font-extrabold text-slate-100 uppercase tracking-wider">No Transaction Selected</h3>
        <p className="text-xs text-slate-400 max-w-sm mt-2 leading-relaxed">
          Launch one of the scenarios above to watch FraudGuard analyze the transaction in real time.
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

      {/* Three-Way Match Visual flow */}
      {extraData.document_forensics?.three_way_match && (
        <div className="p-4 rounded-2xl border border-blue-500/20 bg-slate-950/65 flex flex-col gap-3 mt-1 text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="font-extrabold uppercase tracking-wider text-slate-300">Three-Way Procurement Match</span>
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-black border ${
              extraData.document_forensics.three_way_match.status === 'MATCH'
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
            }`}>
              {extraData.document_forensics.three_way_match.status}
            </span>
          </div>

          {/* Flow Diagram */}
          <div className="flex flex-col items-center gap-1 bg-slate-900/20 py-2.5 rounded-xl border border-slate-800/40">
            <div className="flex items-center gap-1.5 px-3 py-1 rounded bg-slate-950/80 border border-slate-800 font-mono text-[10px] text-slate-350">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
              PO: {extraData.document_forensics.three_way_match.po_number}
            </div>
            <div className="text-slate-500 text-xs">↓</div>
            <div className="flex items-center gap-1.5 px-3 py-1 rounded bg-slate-950/80 border border-slate-800 font-mono text-[10px] text-slate-350">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
              GRN: {extraData.document_forensics.three_way_match.grn_number}
            </div>
            <div className="text-slate-500 text-xs">↓</div>
            <div className="flex items-center gap-1.5 px-3 py-1 rounded bg-slate-950/80 border border-slate-850 font-mono text-[10px] text-slate-350">
              <span className="w-2 h-2 rounded-full bg-rose-450 animate-pulse"></span>
              Invoice: {invoice.invoice_number}
            </div>
          </div>

          {/* Detailed items list */}
          <div className="space-y-3">
            {extraData.document_forensics.three_way_match.items.map((item, idx) => (
              <div key={idx} className="p-3 bg-slate-900/45 rounded-xl border border-slate-800/50 space-y-2">
                <div className="flex justify-between items-center border-b border-slate-800/60 pb-1.5">
                  <span className="font-extrabold text-slate-200 truncate max-w-[170px]">{item.description}</span>
                  <span className={`text-[10px] font-black uppercase ${item.status === 'MATCH' ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {item.status}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 font-mono text-[10px] text-slate-400">
                  <div className="bg-slate-950/30 p-1.5 rounded border border-slate-850">
                    <span className="text-[8px] text-slate-500 uppercase font-bold block mb-0.5">Ordered (PO)</span>
                    <span className="text-slate-300">{item.ordered_qty} units</span>
                    <span className="text-slate-500 block text-[9px]">${item.po_price?.toFixed(2)}/u</span>
                  </div>
                  <div className="bg-slate-950/30 p-1.5 rounded border border-slate-850">
                    <span className="text-[8px] text-slate-500 uppercase font-bold block mb-0.5">Received (GR)</span>
                    <span className="text-slate-300">{item.received_qty} units</span>
                    <span className="text-slate-500 block text-[9px]">${item.po_price?.toFixed(2)}/u</span>
                  </div>
                  <div className="bg-slate-950/30 p-1.5 rounded border border-slate-850">
                    <span className="text-[8px] text-slate-500 uppercase font-bold block mb-0.5">Invoiced</span>
                    <span className="text-slate-300">{item.invoiced_qty} units</span>
                    <span className="text-slate-500 block text-[9px]">${item.invoice_price?.toFixed(2)}/u</span>
                  </div>
                </div>

                {(item.unsupported_qty > 0 || item.unsupported_amount > 0) && (
                  <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[10px] flex justify-between font-mono">
                    <span>Unsupported: {item.unsupported_qty} units</span>
                    <span className="font-extrabold">-${item.unsupported_amount?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {(extraData.document_forensics.three_way_match.total_unsupported_qty > 0 ||
            extraData.document_forensics.three_way_match.total_unsupported_amount > 0) && (
            <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-500/10 text-rose-300 leading-relaxed font-mono">
              <span className="text-[9px] uppercase font-black text-rose-400 block mb-1">overbilling warning</span>
              Total Unsupported Quantity: {extraData.document_forensics.three_way_match.total_unsupported_qty} units<br/>
              Total Unsupported Amount: <span className="font-extrabold text-rose-450">${extraData.document_forensics.three_way_match.total_unsupported_amount?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
            </div>
          )}
        </div>
      )}

      {/* Document Forensics Visual Comparison */}
      {extraData.document_forensics && (
        <div className="p-4 rounded-2xl border border-rose-500/20 bg-slate-950/65 flex flex-col gap-3.5 mt-1 text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="font-extrabold uppercase tracking-wider text-slate-300">Document Forensics</span>
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase border ${
              extraData.document_forensics.forensic_status === 'HIGH_RISK'
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                : extraData.document_forensics.forensic_status === 'REVIEW'
                ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            }`}>
              {extraData.document_forensics.forensic_status?.replace('_', ' ')}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5 bg-slate-900/40 p-2.5 rounded-xl border border-slate-800/40">
              <span className="text-[10px] uppercase font-bold text-slate-500 block border-b border-slate-800 pb-1 mb-1">Claimed By Invoice</span>
              <div className="flex justify-between font-mono"><span>Vendor:</span><span className="text-slate-300 truncate max-w-[80px]" title={extraData.document_forensics.claimed_vendor}>{extraData.document_forensics.claimed_vendor || 'n/a'}</span></div>
              <div className="flex justify-between font-mono"><span>Bank:</span><span className="text-slate-300">{extraData.document_forensics.claimed_bank || 'n/a'}</span></div>
              <div className="flex justify-between font-mono"><span>Total:</span><span className="text-slate-300">${extraData.document_forensics.claimed_amount?.toFixed(2) || '0.00'}</span></div>
              <div className="flex justify-between font-mono"><span>PO:</span><span className="text-slate-300">{extraData.document_forensics.claimed_po || 'n/a'}</span></div>
            </div>

            <div className="space-y-1.5 bg-slate-900/40 p-2.5 rounded-xl border border-slate-800/40">
              <span className="text-[10px] uppercase font-bold text-slate-500 block border-b border-slate-800 pb-1 mb-1">Verified By FraudGuard</span>
              <div className="flex justify-between font-mono"><span>Known Bank:</span><span className="text-slate-300">{extraData.document_forensics.verified_bank || 'None'}</span></div>
              <div className="flex justify-between font-mono"><span>PO Vendor:</span><span className="text-slate-300 truncate max-w-[80px]" title={extraData.document_forensics.verified_po_vendor}>{extraData.document_forensics.verified_po_vendor || 'n/a'}</span></div>
              <div className="flex justify-between font-mono"><span>Expected Total:</span><span className="text-slate-300">{extraData.document_forensics.verified_po_amount ? `$${extraData.document_forensics.verified_po_amount.toFixed(2)}` : 'n/a'}</span></div>
            </div>
          </div>

          <div className="bg-slate-900/40 p-2.5 rounded-xl border border-slate-800/40 space-y-1.5">
            <span className="text-[10px] uppercase font-bold text-slate-500 block border-b border-slate-800 pb-1 mb-1">Field Comparison</span>
            <div className="flex justify-between font-mono">
              <span>Vendor Identity:</span>
              <span className={extraData.document_forensics.comparison_vendor === 'MATCH' ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                {extraData.document_forensics.comparison_vendor === 'MATCH' ? '✓ MATCH' : '✕ MISMATCH'}
              </span>
            </div>
            <div className="flex justify-between font-mono">
              <span>Payment Destination Bank:</span>
              <span className={extraData.document_forensics.comparison_bank === 'MATCH' ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                {extraData.document_forensics.comparison_bank === 'MATCH' ? '✓ MATCH' : '✕ MISMATCH'}
              </span>
            </div>
            <div className="flex justify-between font-mono">
              <span>Invoice Total Amount:</span>
              <span className={extraData.document_forensics.comparison_amount === 'MATCH' ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                {extraData.document_forensics.comparison_amount === 'MATCH' ? '✓ MATCH' : '✕ MISMATCH'}
              </span>
            </div>
          </div>

          {extraData.document_forensics.forensic_signals?.length > 0 && (
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Forensic Tampering Signals</span>
              <div className="flex flex-wrap gap-1">
                {extraData.document_forensics.forensic_signals.map((sig, i) => (
                  <span key={i} className="px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/25 text-rose-300 font-mono text-[9px] font-bold">
                    {sig}
                  </span>
                ))}
              </div>
            </div>
          )}

          {extraData.document_forensics.metadata && (
            <div className="p-2 bg-slate-900/25 rounded-lg border border-slate-850 text-[10px] text-slate-400 space-y-1">
              <span className="text-[9px] uppercase font-bold text-slate-500 block">Document Metadata Context</span>
              {extraData.document_forensics.metadata.file_size && (
                <div className="flex justify-between font-mono"><span>File Size:</span><span>{extraData.document_forensics.metadata.file_size} bytes</span></div>
              )}
              {extraData.document_forensics.metadata.pdf_producer && (
                <div className="flex justify-between font-mono"><span>Producer / Creator:</span><span>{extraData.document_forensics.metadata.pdf_producer} / {extraData.document_forensics.metadata.pdf_creator}</span></div>
              )}
              {extraData.document_forensics.metadata.sha256_hash && (
                <div className="flex justify-between font-mono"><span>SHA-256 Fingerprint:</span><span className="truncate max-w-[150px]">{extraData.document_forensics.metadata.sha256_hash}</span></div>
              )}
            </div>
          )}

          <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/10 text-cyan-300 text-[11px] leading-relaxed">
            <span className="text-[10px] uppercase font-bold tracking-widest text-cyan-400 block mb-0.5">Auditor Recommendation</span>
            {extraData.document_forensics.recommended_action}
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
