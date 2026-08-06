import React, { useState } from 'react';
import { FileText, DollarSign, Calendar, Building2, Hash, Code, ChevronDown, ChevronUp } from 'lucide-react';

export default function InvoicePreview({ invoice }) {
  const [showRaw, setShowRaw] = useState(false);

  if (!invoice) {
    return (
      <div className="glass-panel p-8 rounded-2xl border border-slate-800 text-center flex flex-col items-center justify-center min-h-[300px]">
        <FileText className="w-12 h-12 text-slate-600 mb-3 animate-pulse" />
        <h3 className="text-base font-semibold text-slate-300">No Invoice Selected</h3>
        <p className="text-xs text-slate-500 max-w-xs mt-1">
          Select a preset scenario above or upload a new invoice file to start multi-agent analysis.
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
            <span className="text-slate-500 block text-[10px]">Due Date</span>
            <span className="text-slate-200 font-medium">{invoice.due_date || 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Line Items Table if parsed */}
      {lineItems.length > 0 && (
        <div className="mt-2">
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
      {invoice.raw_content && (
        <div className="mt-1">
          <button
            onClick={() => setShowRaw(!showRaw)}
            className="flex items-center justify-between w-full p-2.5 rounded-xl bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800 text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Code className="w-3.5 h-3.5 text-cyan-400" />
              <span>Raw Document Payload</span>
            </div>
            {showRaw ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showRaw && (
            <pre className="mt-2 p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] text-cyan-400 overflow-x-auto max-h-48">
              {invoice.raw_content}
            </pre>
          )}
        </div>
      )}

    </div>
  );
}
