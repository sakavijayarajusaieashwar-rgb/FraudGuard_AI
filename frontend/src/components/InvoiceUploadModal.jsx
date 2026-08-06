import React, { useState } from 'react';
import { Upload, X, FileCode, Check } from 'lucide-react';

export default function InvoiceUploadModal({ isOpen, onClose, onSubmitCustom }) {
  const [vendorName, setVendorName] = useState('');
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [totalAmount, setTotalAmount] = useState('');
  const [rawJson, setRawJson] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmitCustom({
      vendor_name: vendorName || 'Custom Vendor',
      invoice_number: invoiceNumber || `INV-${Date.now().toString().slice(-4)}`,
      total_amount: parseFloat(totalAmount) || 0.0,
      raw_content: rawJson || JSON.stringify({ vendor_name: vendorName, invoice_number: invoiceNumber, total_amount: parseFloat(totalAmount) || 0.0 })
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="glass-panel w-full max-w-lg p-6 rounded-2xl border border-slate-700/80 shadow-2xl relative animate-trace-slide">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Upload className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-100 font-['Outfit']">Submit Custom Invoice</h3>
            <p className="text-xs text-slate-400">Input custom invoice metadata or JSON payload for AI analysis</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-400 font-medium mb-1">Vendor Name</label>
            <input
              type="text"
              placeholder="e.g. Acme Cloud Corp"
              value={vendorName}
              onChange={(e) => setVendorName(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 font-medium mb-1">Invoice Number</label>
              <input
                type="text"
                placeholder="e.g. INV-9921"
                value={invoiceNumber}
                onChange={(e) => setInvoiceNumber(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 font-medium mb-1">Total Amount ($)</label>
              <input
                type="number"
                step="0.01"
                placeholder="0.00"
                value={totalAmount}
                onChange={(e) => setTotalAmount(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-400 font-medium mb-1">Optional Raw JSON or Document Text</label>
            <textarea
              rows={4}
              placeholder='{"line_items": [{"description": "Service Fee", "quantity": 1, "unit_price": 500, "total": 500}]}'
              value={rawJson}
              onChange={(e) => setRawJson(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-medium hover:bg-slate-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex items-center gap-2 px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold transition-all"
            >
              <Check className="w-4 h-4" />
              <span>Submit & Analyze</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
