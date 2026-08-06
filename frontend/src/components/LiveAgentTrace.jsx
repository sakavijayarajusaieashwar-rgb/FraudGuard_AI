import React, { useEffect, useRef } from 'react';
import { Bot, ShieldAlert, Scale, CheckCheck, Terminal, Loader2, Sparkles } from 'lucide-react';

const AGENT_CONFIGS = {
  'Extraction Agent': {
    icon: Bot,
    color: 'from-cyan-500/20 to-blue-500/10 border-cyan-500/40 text-cyan-400',
    badge: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    accent: '#00f2fe',
    description: 'Document OCR & Line Item Extraction'
  },
  'Risk Agent': {
    icon: ShieldAlert,
    color: 'from-amber-500/20 to-purple-500/10 border-amber-500/40 text-amber-400',
    badge: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    accent: '#f59e0b',
    description: 'Duplicate & Financial Anomaly Scan'
  },
  'Decision Agent': {
    icon: Scale,
    color: 'from-purple-500/20 to-indigo-500/10 border-purple-500/40 text-purple-400',
    badge: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    accent: '#7f53ac',
    description: 'Verdict & Risk Score Synthesis'
  },
  'Critic Agent': {
    icon: CheckCheck,
    color: 'from-emerald-500/20 to-teal-500/10 border-emerald-500/40 text-emerald-400',
    badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    accent: '#10b981',
    description: 'Governance & False-Positive Audit'
  }
};

export default function LiveAgentTrace({ traces, activeAgent, isAnalyzing }) {
  const consoleEndRef = useRef(null);

  // Auto-scroll console to bottom as traces arrive
  useEffect(() => {
    consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [traces]);

  // Group traces by Agent
  const agentTraces = {
    'Extraction Agent': [],
    'Risk Agent': [],
    'Decision Agent': [],
    'Critic Agent': []
  };

  traces.forEach((trace) => {
    if (agentTraces[trace.agent_name]) {
      agentTraces[trace.agent_name].push(trace);
    }
  });

  return (
    <div className="glass-panel p-5 rounded-2xl border border-slate-800 flex flex-col gap-5">
      
      {/* Title Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-cyan-400" />
          <h2 className="text-base font-bold text-slate-100 font-['Outfit']">
            Autonomous Multi-Agent Reasoning Trace
          </h2>
        </div>

        {isAnalyzing && (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold animate-pulse">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Agents Thinking...</span>
          </div>
        )}
      </div>

      {/* 4 Agent Status Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {Object.entries(AGENT_CONFIGS).map(([agentName, cfg]) => {
          const IconComp = cfg.icon;
          const isActive = activeAgent === agentName;
          const count = agentTraces[agentName].length;
          const isComplete = !isActive && count > 0;
          const statusClass = isActive ? 'agent-active-glow scale-[1.02]' : isComplete ? 'opacity-100' : 'opacity-80';

          return (
            <div
              key={agentName}
              className={`p-3.5 rounded-xl border bg-gradient-to-b transition-all duration-300 ${cfg.color} ${statusClass}`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800">
                  <IconComp className="w-4 h-4" />
                </div>
                
                {isActive ? (
                  <span className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 animate-pulse">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
                    Active
                  </span>
                ) : isComplete ? (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    Completed ({count})
                  </span>
                ) : (
                  <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                    Standby
                  </span>
                )}
              </div>

              <h4 className="text-xs font-bold text-slate-100">{agentName}</h4>
              <p className="text-[10px] text-slate-400 mt-0.5 truncate">{cfg.description}</p>
            </div>
          );
        })}
      </div>

      {/* Real-time Stream Console */}
      <div className="p-4 rounded-xl bg-slate-950/90 border border-slate-800 font-mono text-xs max-h-[380px] overflow-y-auto space-y-3">
        {traces.length === 0 ? (
          <div className="text-slate-500 text-center py-8 flex flex-col items-center justify-center gap-2">
            <Sparkles className="w-6 h-6 text-slate-600 animate-pulse" />
            <span>Waiting for invoice analysis to start...</span>
          </div>
        ) : (
          traces.map((t, idx) => {
            const statusColors = {
              INFO: 'text-cyan-400 border-cyan-500/30 bg-cyan-500/5',
              WARNING: 'text-amber-400 border-amber-500/30 bg-amber-500/5',
              ERROR: 'text-rose-400 border-rose-500/30 bg-rose-500/5',
              SUCCESS: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/5',
            };
            const badgeClass = statusColors[t.status] || statusColors.INFO;

            return (
              <div
                key={idx}
                className="p-3 rounded-lg bg-slate-900/70 border border-slate-800/80 animate-trace-slide"
              >
                <div className="flex items-center justify-between mb-1 text-[11px]">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-200">[{t.agent_name}]</span>
                    <span className="text-slate-400">• {t.step_name}</span>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${badgeClass}`}>
                    {t.status}
                  </span>
                </div>

                <p className="text-slate-300 text-[11.5px] leading-relaxed pl-2 border-l-2 border-slate-700/60">
                  {t.thought_process}
                </p>

                {t.output_data && Object.keys(t.output_data).length > 0 && (
                  <div className="mt-2 p-2 rounded bg-slate-950 border border-slate-800/60 text-[10.5px] text-cyan-300/90 overflow-x-auto">
                    {JSON.stringify(t.output_data, null, 2)}
                  </div>
                )}
              </div>
            );
          })
        )}
        <div ref={consoleEndRef} />
      </div>

    </div>
  );
}
