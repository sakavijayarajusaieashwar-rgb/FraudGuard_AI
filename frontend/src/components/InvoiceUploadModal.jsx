import React, { useState, useRef } from 'react';
import { Upload, X, FileText, Check, FileCheck, FileCode, AlertCircle, Loader2 } from 'lucide-react';

export default function InvoiceUploadModal({ isOpen, onClose, onSubmitCustom, onSubmitDocument }) {
  const [activeTab, setActiveTab] = useState('document'); // 'document' | 'manual'
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  // Manual Form States
  const [vendorName, setVendorName] = useState('');
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [totalAmount, setTotalAmount] = useState('');
  const [rawJson, setRawJson] = useState('');

  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleDocumentSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;
    setIsUploading(true);
    try {
      await onSubmitDocument(selectedFile);
      setSelectedFile(null);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleManualSubmit = (e) => {
    e.preventDefault();
    onSubmitCustom({
      vendor_name: vendorName || 'Custom Vendor',
      invoice_number: invoiceNumber || `INV-${Date.now().toString().slice(-4)}`,
      total_amount: parseFloat(totalAmount) || 0.0,
      raw_content: rawJson || JSON.stringify({ vendor_name: vendorName, invoice_number: invoiceNumber, total_amount: parseFloat(totalAmount) || 0.0 })
    });
    setVendorName('');
    setInvoiceNumber('');
    setTotalAmount('');
    setRawJson('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="glass-panel w-full max-w-lg p-6 rounded-3xl border border-slate-700/80 shadow-2xl relative animate-trace-slide">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl bg-slate-800/80 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header Title */}
        <div className="flex items-center gap-3 mb-5">
          <div className="p-3 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-lg shadow-cyan-500/5">
            <Upload className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-100 font-['Outfit']">Submit Invoice Document</h3>
            <p className="text-xs text-slate-400">Upload PDF/Text invoice documents or enter manual payload</p>
          </div>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex bg-slate-900/90 p-1 rounded-2xl border border-slate-800/80 mb-5">
          <button
            type="button"
            onClick={() => setActiveTab('document')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-xl transition-all ${
              activeTab === 'document'
                ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Upload Document File</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('manual')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-xl transition-all ${
              activeTab === 'manual'
                ? 'bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>Manual Form Input</span>
          </button>
        </div>

        {/* TAB 1: DOCUMENT FILE UPLOAD */}
        {activeTab === 'document' && (
          <form onSubmit={handleDocumentSubmit} className="space-y-4 text-xs">
            
            {/* Drag and Drop Zone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
                isDragOver
                  ? 'border-cyan-400 bg-cyan-500/10 scale-[1.01]'
                  : selectedFile
                  ? 'border-emerald-500/50 bg-emerald-500/5'
                  : 'border-slate-700/80 bg-slate-900/60 hover:border-slate-600 hover:bg-slate-900'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.csv,.json,.md,.log,.png,.jpg,.jpeg"
                onChange={handleFileChange}
                className="hidden"
              />

              {selectedFile ? (
                <div className="flex flex-col items-center gap-2">
                  <div className="p-3 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                    <FileCheck className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-100 truncate max-w-xs">{selectedFile.name}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">{formatFileSize(selectedFile.size)} • Click or drop to change file</p>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <div className="p-3 rounded-full bg-slate-800/80 text-cyan-400 border border-slate-700/80">
                    <Upload className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-200">Drag and drop invoice document here</p>
                    <p className="text-[11px] text-slate-400 mt-1">Supports PDF, Text, CSV, JSON, Markdown, PNG, JPG</p>
                  </div>
                  <span className="mt-2 inline-block px-3 py-1.5 rounded-xl bg-slate-800 text-cyan-400 text-xs font-semibold border border-slate-700">
                    Browse Document File
                  </span>
                </div>
              )}
            </div>

            {/* Document Info Note */}
            <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-[11px] text-slate-400">
              <AlertCircle className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <p>
                The Extraction Agent will automatically parse the vendor name, invoice number, totals, and line items directly from your uploaded document.
              </p>
            </div>

            {/* Modal Actions */}
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-medium hover:bg-slate-700 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!selectedFile || isUploading}
                className="flex items-center gap-2 px-5 py-2 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-slate-950 font-bold transition-all disabled:opacity-50 shadow-lg shadow-cyan-500/10"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Extracting Document...</span>
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    <span>Upload & Analyze Document</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}

        {/* TAB 2: MANUAL FORM INPUT */}
        {activeTab === 'manual' && (
          <form onSubmit={handleManualSubmit} className="space-y-4 text-xs">
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
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-medium hover:bg-slate-700 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex items-center gap-2 px-5 py-2 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-slate-950 font-bold transition-all shadow-lg shadow-cyan-500/10"
              >
                <Check className="w-4 h-4" />
                <span>Submit & Analyze</span>
              </button>
            </div>
          </form>
        )}

      </div>
    </div>
  );
}
