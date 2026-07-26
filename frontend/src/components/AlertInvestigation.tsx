import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { X, ShieldAlert, Cpu, Monitor, Users, Info, BrainCircuit, Activity, CheckCircle2, ShieldQuestion, HelpCircle } from 'lucide-react';

interface AlertInvestigationProps {
  alert: any;
  onClose: () => void;
  onStatusUpdated: () => void;
}

type CopilotTab = 'Overview' | 'AI Explanation' | 'Recommendations' | 'Executive Summary' | 'Timeline Summary';

export const AlertInvestigation: React.FC<AlertInvestigationProps> = ({ alert, onClose, onStatusUpdated }) => {
  const [status, setStatus] = useState<string>(alert.status);
  const [analyst, setAnalyst] = useState<string>('Analyst Team Alpha');
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loadingTimeline, setLoadingTimeline] = useState<boolean>(false);
  
  // Copilot State
  const [activeTab, setActiveTab] = useState<CopilotTab>('Overview');
  const [aiReport, setAiReport] = useState<any>(null);
  const [loadingAI, setLoadingAI] = useState<boolean>(false);

  const updateStatus = async (newStatus: string) => {
    try {
      await apiClient.put(`/alerts/${alert.id}`, { status: newStatus });
      setStatus(newStatus);
      onStatusUpdated();
    } catch (err) {
      console.error('Failed to update alert status', err);
    }
  };

  const fetchInvestigationTimeline = async () => {
    setLoadingTimeline(true);
    try {
      const res = await apiClient.get('/threats/timeline');
      const filtered = res.data.filter((item: any) => {
        return (
          (alert.user_id && item.target_user_id === alert.user_id) ||
          (alert.device_id && item.target_device_id === alert.device_id) ||
          (alert.asset_id && item.target_asset_id === alert.asset_id)
        );
      });
      setTimeline(filtered);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingTimeline(false);
    }
  };

  const fetchAIReport = async () => {
    setLoadingAI(true);
    try {
      const res = await apiClient.post('/copilot/report', { alert_id: alert.id });
      setAiReport(res.data);
    } catch (err) {
      console.error('Failed to fetch AI copilot report', err);
    } finally {
      setLoadingAI(false);
    }
  };

  useEffect(() => {
    setStatus(alert.status);
    fetchInvestigationTimeline();
    fetchAIReport();
  }, [alert]);

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Affected Entity Profile */}
      <div className="space-y-2">
        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Affected Entity profile</h4>
        
        <div className="bg-zinc-950/40 p-4 rounded-xl border border-zinc-850/80 space-y-3">
          {alert.user && (
            <div className="space-y-2">
              <div className="flex items-center space-x-1.5 text-zinc-200">
                <Users className="h-4 w-4 text-zinc-500" />
                <span className="font-semibold">Operator: {alert.user.full_name}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px] text-zinc-400">
                <div>Username: <span className="text-zinc-300">@{alert.user.username}</span></div>
                <div>Role: <span className="text-zinc-300">{alert.user.role}</span></div>
              </div>
            </div>
          )}

          {alert.device && (
            <div className="space-y-2">
              <div className="flex items-center space-x-1.5 text-zinc-200">
                <Monitor className="h-4 w-4 text-zinc-500" />
                <span className="font-semibold">Device: {alert.device.hostname}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px] text-zinc-400">
                <div>IP: <span className="text-zinc-300">{alert.device.ip_address}</span></div>
                <div>OS: <span className="text-zinc-300">{alert.device.os_version}</span></div>
              </div>
            </div>
          )}

          {alert.asset && (
            <div className="space-y-2">
              <div className="flex items-center space-x-1.5 text-zinc-200">
                <Cpu className="h-4 w-4 text-zinc-500" />
                <span className="font-semibold">Asset: {alert.asset.name}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px] text-zinc-400">
                <div>IP: <span className="text-zinc-300">{alert.asset.ip_address}</span></div>
                <div>Location: <span className="text-zinc-300">{alert.asset.location}</span></div>
                <div>Criticality: <span className="text-zinc-300">{alert.asset.criticality}</span></div>
                <div>Vendor: <span className="text-zinc-300">{alert.asset.vendor} ({alert.asset.model})</span></div>
              </div>
            </div>
          )}
          
          <div className="border-t border-zinc-900 pt-3 text-[10px] text-zinc-400">
            <span className="text-zinc-500 block uppercase mb-1">Threat Description</span>
            <p className="leading-relaxed">{alert.description}</p>
          </div>
        </div>
      </div>

      {/* Attack Chronology Timeline */}
      <div className="space-y-3">
        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Attack Chronology Timeline</h4>
        
        <div className="relative border-l border-zinc-800 pl-4 space-y-4 ml-2.5">
          {timeline.map((step, idx) => (
            <div key={step.id} className="relative">
              <span className="absolute -left-[21.5px] top-1.5 h-3 w-3 rounded-full bg-zinc-950 border-2 border-emerald-400 flex items-center justify-center">
                <span className="h-1 w-1 bg-emerald-400 rounded-full animate-ping"></span>
              </span>
              
              <div className="space-y-0.5">
                <div className="flex justify-between items-center text-[10px]">
                  <span className="font-bold text-emerald-400">{step.current_step}</span>
                  <span className="text-zinc-500">{new Date(step.timestamp).toLocaleTimeString()}</span>
                </div>
                <p className="text-[10px] text-zinc-400">{step.payload_summary}</p>
              </div>
            </div>
          ))}

          {/* Raised Alert Indicator */}
          <div className="relative">
            <span className="absolute -left-[21.5px] top-1.5 h-3 w-3 rounded-full bg-zinc-950 border-2 border-red-500 flex items-center justify-center">
              <span className="h-1 w-1 bg-red-500 rounded-full"></span>
            </span>
            <div className="space-y-0.5">
              <div className="flex justify-between items-center text-[10px]">
                <span className="font-bold text-red-400">Behavioral Alert Generated</span>
                <span className="text-zinc-500">{new Date(alert.created_at).toLocaleTimeString()}</span>
              </div>
              <p className="text-[10px] text-zinc-500">Unsupervised Isolation Forest model identified features boundary deviation.</p>
            </div>
          </div>

          {loadingTimeline && <div className="text-zinc-500 font-mono text-[10px]">Loading audit trail...</div>}
          {timeline.length === 0 && !loadingTimeline && (
            <div className="text-zinc-600 font-mono text-[10px] italic">No active scenario steps tracked. Logging raw baseline operations.</div>
          )}
        </div>
      </div>
    </div>
  );

  const formatText = (text: string) => {
    return text.split('\n').map((line, index) => {
      // Bold Markdown formatting mapping
      const formatted = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      return (
        <p 
          key={index} 
          className="mb-2 leading-relaxed" 
          dangerouslySetInnerHTML={{ __html: formatted }}
        />
      );
    });
  };

  const renderCopilotContent = (content: string | null) => {
    if (loadingAI) {
      return (
        <div className="flex flex-col items-center justify-center py-12 space-y-3 font-mono text-zinc-500">
          <BrainCircuit className="h-8 w-8 text-emerald-400 animate-pulse" />
          <span className="text-xs uppercase font-bold tracking-wider">AI Copilot Synthesizing Analysis...</span>
        </div>
      );
    }
    if (!content) {
      return <div className="text-zinc-500 italic">No AI response could be compiled.</div>;
    }
    return <div className="space-y-3 bg-zinc-950/40 p-4 rounded-xl border border-zinc-850 text-[11px] leading-relaxed text-zinc-300 font-sans">{formatText(content)}</div>;
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[500px] bg-[#090d16] border-l border-zinc-800 shadow-2xl z-50 flex flex-col font-mono text-xs text-zinc-300">
      {/* Drawer Header */}
      <div className="p-5 border-b border-zinc-800 flex justify-between items-start bg-zinc-950/40">
        <div className="space-y-1.5">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="h-4.5 w-4.5 text-red-500" />
            <span className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider">SEC-OPS INCIDENT FILE</span>
            {alert.anomaly_classification && (
              <span className="bg-red-950/40 border border-red-500/30 text-red-400 font-bold text-[9px] px-1.5 py-0.5 rounded uppercase font-mono tracking-wide">
                {alert.anomaly_classification}
              </span>
            )}
          </div>
          <h3 className="text-sm font-bold text-zinc-200">{alert.title}</h3>
        </div>
        <button 
          onClick={onClose}
          className="text-zinc-500 hover:text-zinc-300 p-1 rounded hover:bg-zinc-900 transition-colors cursor-pointer"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Tab Selector */}
      <div className="flex border-b border-zinc-850 bg-zinc-950/20 px-3 overflow-x-auto shrink-0 select-none">
        {(['Overview', 'AI Explanation', 'Recommendations', 'Executive Summary', 'Timeline Summary'] as CopilotTab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-2.5 font-bold tracking-tight text-[9px] uppercase border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === tab
                ? 'border-emerald-500 text-emerald-400 font-extrabold'
                : 'border-transparent text-zinc-500 hover:text-zinc-300'
            }`}
          >
            {tab === 'AI Explanation' ? 'AI Explain' : tab === 'Executive Summary' ? 'Exec Brief' : tab === 'Timeline Summary' ? 'Timeline Narration' : tab}
          </button>
        ))}
      </div>

      {/* Drawer Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {/* Status & Assignment Panel (Always visible at top of tabs) */}
        <div className="bg-zinc-950/30 p-4 rounded-xl border border-zinc-850 grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-[10px] text-zinc-500 uppercase">Alert Status</label>
            <select
              value={status}
              onChange={(e) => updateStatus(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1 focus:outline-none focus:border-zinc-700"
            >
              <option value="New">New</option>
              <option value="Investigating">Investigating</option>
              <option value="Resolved">Resolved</option>
              <option value="False Positive">False Positive</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-[10px] text-zinc-500 uppercase">Assigned Analyst</label>
            <select
              value={analyst}
              onChange={(e) => setAnalyst(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1 focus:outline-none focus:border-zinc-700"
            >
              <option value="Analyst Team Alpha">SOC Analyst Alpha</option>
              <option value="Threat Hunter Beta">Hunter Beta</option>
              <option value="Incident Responder Gamma">Responder Gamma</option>
            </select>
          </div>
        </div>

        {/* Tab views switcher */}
        {activeTab === 'Overview' && renderOverview()}
        {activeTab === 'AI Explanation' && renderCopilotContent(aiReport?.explanation)}
        {activeTab === 'Recommendations' && renderCopilotContent(aiReport?.recommendations)}
        {activeTab === 'Executive Summary' && renderCopilotContent(aiReport?.executive_summary)}
        {activeTab === 'Timeline Summary' && renderCopilotContent(aiReport?.timeline_summary)}
      </div>

      {/* Drawer Footer */}
      <div className="p-4 border-t border-zinc-800 bg-zinc-950/40 flex justify-end space-x-3">
        <button
          onClick={onClose}
          className="bg-zinc-900 border border-zinc-850 hover:bg-zinc-800 text-zinc-300 px-4 py-2 rounded-lg font-mono tracking-wide transition-colors cursor-pointer"
        >
          CLOSE FILE
        </button>
      </div>
    </div>
  );
};
