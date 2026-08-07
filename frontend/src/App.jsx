import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import AuthForm from './components/AuthForm';
import UnifiedStats from './components/UnifiedStats';
import WorkflowSelector from './components/WorkflowSelector';
import PresetSelector from './components/PresetSelector';
import InvoicePreview from './components/InvoicePreview';
import LiveAgentTrace from './components/LiveAgentTrace';
import DecisionPanel from './components/DecisionPanel';
import InvoiceHistory from './components/InvoiceHistory';
import InvoiceUploadModal from './components/InvoiceUploadModal';
import FraudGraph from './components/FraudGraph';
import InvestigatorPanel from './components/InvestigatorPanel';
import { Plus, Play, Network, Shield, Search } from 'lucide-react';

export default function App() {
  const [backendConnected, setBackendConnected] = useState(false);
  const [authToken, setAuthToken] = useState(null);
  const [userEmail, setUserEmail] = useState(null);
  const [activeWorkflow, setActiveWorkflow] = useState('invoice_fraud');
  const [invoices, setInvoices] = useState([]);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [traces, setTraces] = useState([]);
  const [activeAgent, setActiveAgent] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [activeTab, setActiveTab] = useState('simulator');
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('fraudguard_theme');
    if (saved) return saved;
    // Default is dark mode per instructions
    const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
    return prefersLight ? 'light' : 'dark';
  });

  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.add('light');
    } else {
      document.documentElement.classList.remove('light');
    }
    localStorage.setItem('fraudguard_theme', theme);
  }, [theme]);

  const filteredInvoices = invoices.filter(
    (inv) => inv.workflow_type === activeWorkflow || (!inv.workflow_type && activeWorkflow === 'invoice_fraud')
  );

  // Check health and load invoices on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('fraudguard_token');
    if (storedToken) {
      setAuthToken(storedToken);
    }
    checkHealth();
  }, []);

  useEffect(() => {
    if (authToken) {
      validateToken();
    }
  }, [authToken]);

  const checkHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        setBackendConnected(true);
      } else {
        setBackendConnected(false);
      }
    } catch (e) {
      setBackendConnected(false);
    }
  };

  const validateToken = async () => {
    try {
      const res = await fetch('/api/auth/me', {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });
      if (!res.ok) {
        throw new Error('Invalid token');
      }
      const data = await res.json();
      setUserEmail(data.email);
      fetchInvoices();
      fetchMetrics();
    } catch (error) {
      setAuthToken(null);
      setUserEmail(null);
      localStorage.removeItem('fraudguard_token');
    }
  };

  const handleAuthSuccess = (token) => {
    setAuthToken(token);
    localStorage.setItem('fraudguard_token', token);
  };

  const handleLogout = () => {
    setAuthToken(null);
    setUserEmail(null);
    localStorage.removeItem('fraudguard_token');
    setInvoices([]);
    setSelectedInvoice(null);
    setTraces([]);
    window.location.reload();
  };

  const authHeaders = authToken
    ? { Authorization: `Bearer ${authToken}` }
    : {};

  const fetchInvoices = async () => {
    if (!authToken) return;
    try {
      const res = await fetch('/api/invoices/', {
        headers: authHeaders,
      });
      if (res.ok) {
        const data = await res.json();
        const normalized = data.map(normalizeInvoice);
        setInvoices(normalized);
        if (normalized.length > 0 && !selectedInvoice) {
          loadInvoiceDetails(normalized[0].id);
        }
      }
    } catch (e) {
      console.error('Failed to fetch invoices:', e);
    }
  };

  const fetchMetrics = async () => {
    if (!authToken) return;
    try {
      const res = await fetch('/api/dashboard/metrics', {
        headers: authHeaders,
      });
      if (res.ok) {
        setMetrics(await res.json());
      }
    } catch (e) {
      console.error('Failed to fetch metrics:', e);
    }
  };

  const normalizeInvoice = (inv) => ({
    ...inv,
    amount: inv.amount ?? inv.total_amount ?? 0.0,
    total_amount: inv.total_amount ?? inv.amount ?? 0.0,
    risk_score: inv.risk_score ?? 0.0,
    confidence: inv.confidence ?? 0.0,
    risk_signals: inv.risk_signals ?? [],
    verdict_summary: inv.verdict_summary ?? inv.reasoning ?? null,
    critic_notes: inv.critic_notes ?? null,
  });

  const loadInvoiceDetails = async (invoiceId) => {
    try {
      const res = await fetch(`/api/invoices/${invoiceId}`, {
        headers: authHeaders,
      });
      if (res.ok) {
        const data = await res.json();
        const normalized = normalizeInvoice(data);
        setSelectedInvoice(normalized);
        if (data.logs && data.logs.length > 0) {
          const mappedTraces = data.logs.map((log) => ({
            invoice_id: log.invoice_id,
            agent_name: log.agent_name,
            step_name: log.step_name,
            thought_process: log.thought_process,
            output_data: typeof log.output_data === 'string' ? JSON.parse(log.output_data) : log.output_data,
            status: log.status,
            timestamp: log.timestamp,
          }));
          setTraces(mappedTraces);
        } else {
          setTraces([]);
        }
      }
    } catch (e) {
      console.error('Failed to load invoice detail:', e);
    }
  };

  // Trigger Live SSE Stream Analysis
  const runAnalysisStream = (invoiceId) => {
    setTraces([]);
    setIsAnalyzing(true);
    setActiveAgent('Extraction Agent');

    const streamUrl = authToken
      ? `/api/invoices/${invoiceId}/analyze/stream?token=${authToken}`
      : `/api/invoices/${invoiceId}/analyze/stream`;
    const eventSource = new EventSource(streamUrl);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.agent_name && data.agent_name !== 'FraudGuard Orchestrator') {
          setActiveAgent(data.agent_name);
        }

        setTraces((prev) => [...prev, data]);

        if (data.step_name === 'Pipeline Execution Finished') {
          eventSource.close();
          setIsAnalyzing(false);
          setActiveAgent(null);
          loadInvoiceDetails(invoiceId);
          fetchInvoices();
          fetchMetrics();
        }
      } catch (e) {
        console.error('Error parsing SSE event:', e);
      }
    };

    eventSource.onerror = (err) => {
      console.error('EventSource failed:', err);
      eventSource.close();
      setIsAnalyzing(false);
      setActiveAgent(null);
      loadInvoiceDetails(invoiceId);
      fetchInvoices();
      fetchMetrics();
    };
  };

  // Preset Selection Handler — Populates data WITHOUT auto-running analysis
  const handleSelectPreset = async (presetType) => {
    try {
      const res = await fetch('/api/invoices/preset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
        body: JSON.stringify({ preset_type: presetType, workflow_type: activeWorkflow }),
      });
      if (res.ok) {
        const newInv = normalizeInvoice(await res.json());
        setSelectedInvoice(newInv);
        setTraces([]);
        setInvoices((prev) => [newInv, ...prev]);
        // Do NOT auto-run stream; let user click "Analyze Invoice" in front of judges
      }
    } catch (e) {
      console.error('Preset generation failed:', e);
    }
  };

  // Document File Upload Handler (.pdf, .txt, .json, .csv, .png, .jpg)
  const handleDocumentUpload = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('workflow_type', activeWorkflow);

      const res = await fetch('/api/invoices/upload-document', {
        method: 'POST',
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        body: formData,
      });

      if (res.ok) {
        const newInv = normalizeInvoice(await res.json());
        setSelectedInvoice(newInv);
        setTraces([]);
        setInvoices((prev) => [newInv, ...prev]);
      } else {
        const errData = await res.json();
        alert(`Document upload failed: ${errData.detail || 'Server error'}`);
      }
    } catch (e) {
      console.error('Document upload error:', e);
      alert('Failed to upload document file.');
    }
  };

  // Custom Invoice Upload Handler
  const handleCustomUpload = async (payload) => {
    try {
      const res = await fetch('/api/invoices/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
        body: JSON.stringify({ ...payload, workflow_type: activeWorkflow }),
      });
      if (res.ok) {
        const newInv = normalizeInvoice(await res.json());
        setSelectedInvoice(newInv);
        setTraces([]);
        setInvoices((prev) => [newInv, ...prev]);
      }
    } catch (e) {
      console.error('Custom invoice creation failed:', e);
    }
  };

  // Delete invoice
  const handleDeleteInvoice = async (invoiceId) => {
    try {
      await fetch(`/api/invoices/${invoiceId}`, {
        method: 'DELETE',
        headers: authHeaders,
      });
      const updated = invoices.filter((i) => i.id !== invoiceId);
      setInvoices(updated);
      if (selectedInvoice?.id === invoiceId) {
        setSelectedInvoice(updated[0] || null);
        setTraces([]);
      }
    } catch (e) {
      console.error('Failed to delete invoice:', e);
    }
  };

  // Reset entire DB state
  const handleResetDB = async () => {
    for (const inv of invoices) {
      await fetch(`/api/invoices/${inv.id}`, {
        method: 'DELETE',
        headers: authHeaders,
      });
    }
    setInvoices([]);
    setSelectedInvoice(null);
    setTraces([]);
    setMetrics(null);
    fetchMetrics();
  };

  const handleResetDemo = async () => {
    try {
      await fetch('/api/demo/reset', {
        method: 'POST',
        headers: authHeaders,
      });
      fetchInvoices();
      fetchMetrics();
    } catch (e) {
      console.error('Reset failed:', e);
    }
  };

  if (!authToken) {
    return <AuthForm onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-dark-900 text-slate-100">
      <Navbar
        backendConnected={backendConnected}
        onResetDB={handleResetDemo}
        userEmail={userEmail}
        onLogout={handleLogout}
        theme={theme}
        setTheme={setTheme}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        
        {/* FraudGuard Business Impact Dashboard */}
        <UnifiedStats metrics={metrics} />

        {/* Invoice Fraud Engine Indicator */}
        <WorkflowSelector activeWorkflow={activeWorkflow} onChange={setActiveWorkflow} />

        {/* 3 Preset Demos Panel */}
        <PresetSelector activeWorkflow={activeWorkflow} onSelectPreset={handleSelectPreset} isLoading={isAnalyzing} />

        {/* Demo Flow Journey */}
        <div className="glass-panel p-3.5 rounded-2xl border border-slate-800/80 bg-slate-950/40 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
              DEMO FLOW
            </span>
            <span className="text-[11px] text-slate-450 font-bold hidden sm:inline">
              Coordinated Security Sequence:
            </span>
          </div>
          
          <div className="flex items-center gap-2 sm:gap-4 text-[11px] font-bold text-slate-350">
            <div className="flex items-center gap-1.5">
              <span className="w-5 h-5 flex items-center justify-center rounded-full bg-slate-800 border border-slate-700 text-[10px] text-slate-200">1</span>
              <span>Launch Attack</span>
            </div>
            <span className="text-slate-655 font-bold">→</span>
            <div className="flex items-center gap-1.5">
              <span className="w-5 h-5 flex items-center justify-center rounded-full bg-slate-800 border border-slate-700 text-[10px] text-slate-200">2</span>
              <span>Review Evidence</span>
            </div>
            <span className="text-slate-655 font-bold">→</span>
            <div className="flex items-center gap-1.5">
              <span className="w-5 h-5 flex items-center justify-center rounded-full bg-slate-800 border border-slate-700 text-[10px] text-slate-200">3</span>
              <span>Trace Network</span>
            </div>
            <span className="text-slate-655 font-bold">→</span>
            <div className="flex items-center gap-1.5">
              <span className="w-5 h-5 flex items-center justify-center rounded-full bg-slate-800 border border-slate-700 text-[10px] text-slate-200">4</span>
              <span>Ask Investigator</span>
            </div>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex gap-2 border-b border-slate-800 pb-px">
          <button
            onClick={() => setActiveTab('simulator')}
            className={`py-3 px-6 font-bold text-xs uppercase tracking-wider border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'simulator'
                ? 'border-cyan-400 text-cyan-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Shield className="w-4 h-4" />
            <span>Simulator & Workbench</span>
          </button>
          <button
            onClick={() => setActiveTab('graph')}
            className={`py-3 px-6 font-bold text-xs uppercase tracking-wider border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'graph'
                ? 'border-cyan-400 text-cyan-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Network className="w-4 h-4" />
            <span>Fraud Relationship Graph</span>
          </button>
          <button
            onClick={() => setActiveTab('investigate')}
            className={`py-3 px-6 font-bold text-xs uppercase tracking-wider border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'investigate'
                ? 'border-cyan-400 text-cyan-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Search className="w-4 h-4" />
            <span>AI Fraud Investigator</span>
          </button>
        </div>

        {activeTab === 'graph' ? (
          <FraudGraph authToken={authToken} onSwitchTab={setActiveTab} />
        ) : activeTab === 'investigate' ? (
          <InvestigatorPanel invoice={selectedInvoice} authToken={authToken} onSwitchTab={setActiveTab} />
        ) : (
          /* Main Content Grid */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left Column (5 cols): Document Details & History */}
          <div className="lg:col-span-5 space-y-6">
            
            {/* Top Action Bar */}
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
                Document Details View
              </h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsUploadOpen(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-slate-900 bg-cyan-400 hover:bg-cyan-300 rounded-lg transition-all shadow-md shadow-cyan-500/10"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Custom Submission</span>
                </button>
                {selectedInvoice && (
                  <button
                    disabled={isAnalyzing}
                    onClick={() => runAnalysisStream(selectedInvoice.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-all disabled:opacity-50"
                  >
                    <Play className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Run Trace</span>
                  </button>
                )}
              </div>
            </div>

            {/* Document Preview Card */}
            <InvoicePreview
              invoice={selectedInvoice}
              onRunAnalysis={runAnalysisStream}
              isAnalyzing={isAnalyzing}
            />

            {/* History List */}
            <InvoiceHistory
              invoices={filteredInvoices}
              selectedId={selectedInvoice?.id}
              onSelectInvoice={(inv) => {
                loadInvoiceDetails(inv.id);
              }}
              onDeleteInvoice={handleDeleteInvoice}
            />

          </div>

          {/* Right Column (7 cols): Live Agent Reasoning Trace, Verdict & Accounts Queue */}
          <div className="lg:col-span-7 space-y-6">
            
            {/* Decision Hero Panel */}
            <DecisionPanel invoice={selectedInvoice} />

            {/* Approved Accounts Department Queue */}
            <div className="glass-panel p-5 rounded-3xl border border-slate-800 bg-slate-950/80 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">
                    Accounts Payable Queue
                  </h3>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Invoices approved for payment, ready for disbursement.
                  </p>
                </div>
                <span className="text-[10px] uppercase tracking-[0.2em] font-bold text-emerald-400">
                  {invoices.filter((inv) => inv.status === 'APPROVE' || inv.status === 'APPROVED').length} approved
                </span>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {invoices
                  .filter((inv) => inv.status === 'APPROVE' || inv.status === 'APPROVED')
                  .slice(0, 5)
                  .map((inv) => (
                    <div key={inv.id} className="p-3 rounded-2xl bg-slate-900/80 border border-slate-800/80">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
                            Approved #{inv.invoice_number}
                          </p>
                          <p className="text-sm font-semibold text-slate-100 mt-1 truncate">{inv.vendor_name}</p>
                        </div>
                        <span className="text-xs font-bold text-emerald-300">${inv.amount?.toFixed(2)}</span>
                      </div>
                      <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
                        <span>Risk: {inv.risk_score?.toFixed(0)}/100</span>
                        <button
                          onClick={() => loadInvoiceDetails(inv.id)}
                          className="text-cyan-300 hover:text-cyan-100 font-semibold"
                        >
                          View Details
                        </button>
                      </div>
                    </div>
                  ))}

                {invoices.filter((inv) => inv.status === 'APPROVE' || inv.status === 'APPROVED').length === 0 && (
                  <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 text-xs text-slate-500">
                    No approved invoices currently queued for payment.
                  </div>
                )}
              </div>
            </div>

            {/* Live Agent Reasoning Trace Stream */}
            <LiveAgentTrace
              traces={traces}
              activeAgent={activeAgent}
              isAnalyzing={isAnalyzing}
            />

          </div>
        </div>
        )}
      </main>

      <InvoiceUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSubmitCustom={handleCustomUpload}
        onSubmitDocument={handleDocumentUpload}
      />
    </div>
  );
}
