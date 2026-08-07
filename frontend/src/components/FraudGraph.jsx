import React, { useState, useEffect } from 'react';
import { Network, ShieldAlert, Award, FileText, ShoppingBag, ShieldCheck, HelpCircle } from 'lucide-react';

export default function FraudGraph({ authToken, onSwitchTab }) {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [filter, setFilter] = useState('ALL');

  useEffect(() => {
    fetchGraph();
  }, [authToken]);

  const fetchGraph = async () => {
    if (!authToken) return;
    setIsLoading(true);
    try {
      const res = await fetch('/api/graph', {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        setGraphData(await res.json());
      }
    } catch (e) {
      console.error('Failed to fetch graph data:', e);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter nodes based on selector
  const filteredNodes = graphData.nodes.filter(node => {
    if (filter === 'ALL') return true;
    if (filter === 'HIGH_RISK') return node.risk_level === 'HIGH';
    if (filter === 'VENDORS') return node.type === 'VENDOR';
    if (filter === 'CUSTOMERS') return node.type === 'CUSTOMER';
    if (filter === 'BANK_ACCOUNTS') return node.type === 'BANK_ACCOUNT';
    return true;
  });

  // Calculate layered layout coordinates
  const centerX = 400;
  const centerY = 300;

  const nodePositions = {};

  const invoices = filteredNodes.filter(n => n.type === 'INVOICE' || n.type === 'ORDER');
  const middle = filteredNodes.filter(n => n.type === 'BANK_ACCOUNT' || n.type === 'TRANSACTION');
  const outer = filteredNodes.filter(n => n.type === 'VENDOR' || n.type === 'CUSTOMER');

  // Layer 1: Invoices at the center
  invoices.forEach((node, index) => {
    const angle = invoices.length > 1 ? (index / invoices.length) * 2 * Math.PI : 0;
    const r = invoices.length > 1 ? 60 : 0;
    nodePositions[node.id] = {
      x: centerX + r * Math.cos(angle),
      y: centerY + r * Math.sin(angle),
    };
  });

  // Layer 2: Bank accounts / Transactions
  middle.forEach((node, index) => {
    const angle = (index / middle.length) * 2 * Math.PI;
    nodePositions[node.id] = {
      x: centerX + 170 * Math.cos(angle),
      y: centerY + 170 * Math.sin(angle),
    };
  });

  // Layer 3: Vendors / Customers
  outer.forEach((node, index) => {
    const angle = (index / outer.length) * 2 * Math.PI + 0.3; // Offset slightly for aesthetics
    nodePositions[node.id] = {
      x: centerX + 280 * Math.cos(angle),
      y: centerY + 280 * Math.sin(angle),
    };
  });

  // Any remaining nodes
  filteredNodes.forEach(node => {
    if (!nodePositions[node.id]) {
      nodePositions[node.id] = { x: centerX, y: centerY };
    }
  });

  const getNodeColor = (node) => {
    if (node.risk_level === 'HIGH') return 'fill-rose-500 stroke-rose-400 shadow-rose-500/50';
    if (node.risk_level === 'MEDIUM') return 'fill-amber-500 stroke-amber-400 shadow-amber-500/50';
    return 'fill-slate-800 stroke-slate-700';
  };

  const getNodeIcon = (type) => {
    if (type === 'INVOICE') return FileText;
    if (type === 'ORDER') return ShoppingBag;
    if (type === 'BANK_ACCOUNT') return ShieldCheck;
    return Network;
  };

  if (!isLoading && graphData.nodes.length === 0) {
    return (
      <div className="glass-panel p-8 rounded-3xl border border-slate-800 text-center flex flex-col items-center justify-center min-h-[420px]">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 mb-4">
          <Network className="w-10 h-10 text-cyan-400 animate-pulse" />
        </div>
        <h3 className="text-base font-extrabold text-slate-100 uppercase tracking-wider">No fraud relationship selected</h3>
        <p className="text-xs text-slate-400 max-w-md mt-2 leading-relaxed">
          Launch or analyze a transaction to reveal connected vendors, customers, bank accounts and historical fraud relationships.
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
      {/* Sidebar Controls (4 cols) */}
      <div className="lg:col-span-4 space-y-6">
        <div className="glass-panel p-5 rounded-3xl border border-slate-800 bg-slate-950/80 shadow-xl">
          <div className="flex items-center gap-2 mb-4">
            <Network className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
              Relationship Intelligence
            </h3>
          </div>
          
          <p className="text-xs text-slate-400 leading-relaxed mb-4">
            FraudGuard correlates identities and bank details across transactions to discover hidden fraud rings and repeat offenders.
          </p>

          <div className="space-y-3">
            <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider block">Filter View</span>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {['ALL', 'HIGH_RISK', 'VENDORS', 'CUSTOMERS', 'BANK_ACCOUNTS'].map(opt => (
                <button
                  key={opt}
                  onClick={() => setFilter(opt)}
                  className={`py-2 px-3 rounded-lg border text-left font-bold transition-all ${
                    filter === opt
                      ? 'bg-cyan-500/10 border-cyan-400 text-cyan-300'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  {opt.replace('_', ' ')}
                </button>
              ))}
            </div>
            
            <button
              onClick={fetchGraph}
              className="w-full py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-bold text-slate-200 rounded-lg transition-colors mt-2"
            >
              Refresh Graph Data
            </button>
          </div>
        </div>

        {/* Selected Entity Details */}
        <div className="glass-panel p-5 rounded-3xl border border-slate-800 bg-slate-950/80 shadow-xl min-h-[220px]">
          {selectedNode ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-[9px] uppercase font-bold tracking-widest text-slate-500">
                  {selectedNode.type} Node Details
                </span>
                <span className={`text-[9px] uppercase font-extrabold px-2.5 py-0.5 rounded-full border ${
                  selectedNode.risk_level === 'HIGH' ? 'bg-rose-500/15 text-rose-400 border-rose-500/30' :
                  selectedNode.risk_level === 'MEDIUM' ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' :
                  'bg-slate-900 text-slate-400 border-slate-800'
                }`}>
                  {selectedNode.risk_level} Risk
                </span>
              </div>

              <div>
                <h4 className="text-base font-black text-slate-100">{selectedNode.label}</h4>
                {selectedNode.metadata?.amount && (
                  <p className="text-xs font-mono font-bold text-slate-300 mt-1">
                    Amount: ${selectedNode.metadata.amount.toLocaleString(undefined, {minimumFractionDigits: 2})}
                  </p>
                )}
                {selectedNode.metadata?.status && (
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Workflow Status: <span className="font-bold">{selectedNode.metadata.status}</span>
                  </p>
                )}
              </div>

              {/* Show connections to this node */}
              <div className="border-t border-slate-800/80 pt-3">
                <span className="text-[9px] uppercase font-bold tracking-widest text-slate-500 block mb-2">Connected Relationships</span>
                <div className="space-y-2 max-h-[160px] overflow-y-auto">
                  {graphData.edges
                    .filter(e => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((edge, idx) => {
                      const otherId = edge.source === selectedNode.id ? edge.target : edge.source;
                      const otherNode = graphData.nodes.find(n => n.id === otherId);
                      return (
                        <div key={idx} className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                          <div className="flex justify-between items-center text-[10px] text-cyan-400 font-bold mb-1">
                            <span>{edge.relationship}</span>
                            <span className="text-slate-500 font-normal">({otherNode?.type})</span>
                          </div>
                          <p className="text-slate-200 font-semibold">{otherNode?.label}</p>
                          <p className="text-[10px] text-slate-500 mt-1">{edge.evidence}</p>
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center text-center py-8 text-slate-500">
              <HelpCircle className="w-8 h-8 text-slate-700 mb-2" />
              <p className="text-xs font-bold">Select any node on the graph</p>
              <p className="text-[10px] text-slate-600 mt-1 max-w-[180px]">
                Click nodes to trace entities, relationships, and risk evidence.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Main Graph Visualization (8 cols) */}
      <div className="lg:col-span-8 glass-panel rounded-3xl border border-slate-800 bg-slate-950/80 shadow-xl overflow-hidden relative min-h-[500px]">
        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-950/40 backdrop-blur-sm">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-cyan-400"></div>
          </div>
        ) : null}

        <div className="absolute top-4 left-4 flex gap-2 text-[10px] uppercase font-bold tracking-widest text-slate-500">
          <span>● CENTER: Transactions</span>
          <span>● MIDDLE: Bank Accounts / Payments</span>
          <span>● OUTER: Vendors / Customers</span>
        </div>

        <svg width="100%" height="580" viewBox="0 0 800 600" className="select-none">
          {/* Render Connections / Edges */}
          {graphData.edges.map((edge, idx) => {
            const from = nodePositions[edge.source];
            const to = nodePositions[edge.target];
            if (!from || !to) return null;

            return (
              <g key={idx}>
                {/* Edge line */}
                <line
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke="#334155"
                  strokeWidth="2"
                  strokeDasharray="4 4"
                  className="opacity-70"
                />
                {/* Relationship label on hover / mouseOver can be added, but keeping it clean */}
              </g>
            );
          })}

          {/* Render Nodes */}
          {filteredNodes.map((node) => {
            const pos = nodePositions[node.id];
            if (!pos) return null;

            const isSelected = selectedNode?.id === node.id;
            const Icon = getNodeIcon(node.type);

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => setSelectedNode(node)}
                className="cursor-pointer group"
              >
                {/* Highlight ring */}
                <circle
                  r={isSelected ? 26 : 22}
                  className={`transition-all duration-200 fill-none ${
                    isSelected ? 'stroke-cyan-400 stroke-2' : 'stroke-transparent group-hover:stroke-slate-600 stroke-1'
                  }`}
                />
                
                {/* Inner node circle */}
                <circle
                  r="18"
                  className={`transition-colors duration-200 ${getNodeColor(node)}`}
                />

                {/* Node Label overlay */}
                <text
                  y="30"
                  textAnchor="middle"
                  className={`text-[9px] font-bold fill-slate-300 transition-colors pointer-events-none ${
                    isSelected ? 'fill-cyan-300 font-extrabold' : 'group-hover:fill-white'
                  }`}
                >
                  {node.label}
                </text>
                
                {/* Masked entity type subtitle */}
                <text
                  y="40"
                  textAnchor="middle"
                  className="text-[7px] font-semibold fill-slate-500 pointer-events-none uppercase tracking-wider"
                >
                  {node.type}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
