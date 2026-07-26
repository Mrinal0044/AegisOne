import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { 
  ShieldCheck, 
  Activity, 
  Settings, 
  Database, 
  Download, 
  RefreshCw, 
  Cpu, 
  Monitor, 
  HardDrive,
  Brain,
  AlertTriangle,
  Play
} from 'lucide-react';
import { useHealth } from '../context/HealthContext';

interface AuditRecord {
  id: string;
  timestamp: string;
  action: string;
  ip_address: string;
  details: string;
  user: string;
}

interface SystemConfig {
  risk_threshold: number;
  alert_threshold: number;
  threat_delay_scale: number;
  simulation_speed: number;
  impossible_travel_threshold: number;
  fingerprint_sensitivity: number;
  credential_stuffing_window: number;
  exfiltration_detection_window: number;
  cold_start_observation_count: number;
  drift_sensitivity: number;
}

interface OperationalHealth {
  backend: string;
  database: string;
  ai_engine: string;
  simulation: string;
  uptime_seconds: number;
  queue: {
    size: number;
    status: string;
  };
  resources: {
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
  };
}

export const OperationsPage: React.FC = () => {
  const { backendConnected, dbConnected } = useHealth();
  const [loading, setLoading] = useState<boolean>(true);
  const [updating, setUpdating] = useState<boolean>(false);
  
  // States
  const [health, setHealth] = useState<OperationalHealth | null>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [config, setConfig] = useState<SystemConfig>({
    risk_threshold: 60,
    alert_threshold: 60,
    threat_delay_scale: 1.0,
    simulation_speed: 10.0,
    impossible_travel_threshold: 800.0,
    fingerprint_sensitivity: 0.5,
    credential_stuffing_window: 60,
    exfiltration_detection_window: 3600,
    cold_start_observation_count: 10,
    drift_sensitivity: 0.5
  });
  const [logs, setLogs] = useState<AuditRecord[]>([]);
  const [toasts, setToasts] = useState<any[]>([]);

  const fetchOperationalData = async () => {
    if (!backendConnected) return;
    try {
      const [healthRes, metricsRes, configRes, logsRes] = await Promise.all([
        apiClient.get('/health/details'),
        apiClient.get('/metrics'),
        apiClient.get('/config'),
        apiClient.get('/audit?limit=25')
      ]);

      setHealth(healthRes.data);
      setMetrics(metricsRes.data);
      setConfig(configRes.data);
      setLogs(logsRes.data);
    } catch (err) {
      console.error('Failed to load system diagnostics telemetry', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setUpdating(true);
    try {
      const res = await apiClient.put('/config', config);
      setConfig(res.data);
      // Trigger update toast
      triggerToast('Configuration updated successfully.', 'success');
      fetchOperationalData();
    } catch (err: any) {
      console.error(err);
      triggerToast(err.response?.data?.detail || 'Failed to update system configurations.', 'error');
    } finally {
      setUpdating(false);
    }
  };

  const triggerToast = (message: string, type: 'info' | 'success' | 'error') => {
    const id = Math.random().toString(36).substring(7);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter(t => t.id !== id));
    }, 4000);
  };

  const handleExport = (type: 'audit' | 'alerts', format: 'csv' | 'json') => {
    const url = `${apiClient.defaults.baseURL}/${type}/export?format=${format}`;
    // Force trigger download via dynamic anchor tag
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${type}_logs.${format}`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    triggerToast(`Exported ${type} logs as ${format.toUpperCase()}`, 'success');
  };

  useEffect(() => {
    fetchOperationalData();

    // Setup realtime event notification hooks via SSE
    const sseUrl = `${apiClient.defaults.baseURL}/sse/stream`;
    const eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const { type, data } = payload;

        if (type === 'ALERT_CREATED') {
          triggerToast(`ALERT FIRED: ${data.title} (${data.severity})`, 'error');
        } else if (type === 'ALERT_UPDATED' && data.status === 'Resolved') {
          triggerToast(`ALERT RESOLVED: ${data.title}`, 'success');
        } else if (type === 'THREAT_PROGRESS') {
          if (data.progress === 100) {
            triggerToast(`THREAT EXHAUSTED: ${data.name} completed.`, 'info');
          } else if (data.progress === 0 || data.current_step_index === 1) {
            triggerToast(`THREAT INITIATED: ${data.name} active.`, 'error');
          }
        } else if (type === 'AUDIT_LOG_CREATED') {
          // Prepend new audit log record
          setLogs((prev) => [data, ...prev.slice(0, 24)]);
        }
      } catch (err) {
        console.error(err);
      }
    };

    return () => {
      eventSource.close();
    };
  }, [backendConnected]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20 text-zinc-500 font-mono text-xs">
        <RefreshCw className="h-4 w-4 animate-spin mr-2" />
        <span>AGGREGATING SYSTEM DIAGNOSTICS...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Realtime Toast Notifications List */}
      <div className="fixed top-5 right-5 space-y-2.5 z-50 pointer-events-none select-none max-w-sm">
        {toasts.map((t) => (
          <div 
            key={t.id}
            className={`p-3.5 rounded-lg border shadow-xl flex items-start space-x-2 font-mono text-[10px] leading-relaxed transition-all duration-300 animate-slide-in ${
              t.type === 'error' ? 'bg-red-950/90 border-red-500/50 text-red-200' :
              t.type === 'success' ? 'bg-emerald-950/90 border-emerald-500/50 text-emerald-200' :
              'bg-zinc-900/90 border-zinc-800 text-zinc-300'
            }`}
          >
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{t.message}</span>
          </div>
        ))}
      </div>

      {/* Grid: Health meters & API stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Component Health Indicators */}
        <div className="glass-panel p-5 rounded-xl border border-zinc-800 space-y-4">
          <div className="flex justify-between items-center border-b border-zinc-850 pb-2">
            <h3 className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wider flex items-center space-x-1.5">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <span>Component status</span>
            </h3>
            <button 
              onClick={fetchOperationalData}
              className="text-[10px] text-zinc-500 hover:text-zinc-300 flex items-center space-x-1 font-mono uppercase tracking-wider"
            >
              <RefreshCw className="h-3 w-3" />
            </button>
          </div>

          <div className="space-y-3 font-mono text-[11px] text-zinc-400">
            {[
              { label: 'FastAPI Backend Core', status: health?.backend || 'Online', color: 'text-emerald-400' },
              { label: 'PostgreSQL Database', status: health?.database || 'healthy', color: health?.database === 'healthy' ? 'text-emerald-400' : 'text-red-400' },
              { label: 'AI Anomaly Detector', status: health?.ai_engine || 'Operational', color: 'text-emerald-400' },
              { label: 'Twin Simulation Loop', status: health?.simulation || 'STOPPED', color: health?.simulation === 'RUNNING' ? 'text-emerald-400' : 'text-zinc-500' },
              { label: 'Aggregation Queue', status: health?.queue.status === 'idle' ? 'Idle' : 'Active', color: 'text-zinc-500' }
            ].map((item, index) => (
              <div key={index} className="flex justify-between items-center border-b border-zinc-900 pb-2.5 last:border-0 last:pb-0">
                <span>{item.label}</span>
                <span className={`font-bold uppercase ${item.color}`}>{item.status}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Hardware Resource Usage */}
        <div className="glass-panel p-5 rounded-xl border border-zinc-800 space-y-4">
          <h3 className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wider border-b border-zinc-850 pb-2">Hardware Telemetry</h3>
          
          <div className="grid grid-cols-3 gap-4 text-center font-mono text-[10px]">
            {/* CPU */}
            <div className="space-y-2 flex flex-col items-center">
              <Cpu className="h-5 w-5 text-zinc-500" />
              <span className="text-zinc-400">CPU Usage</span>
              <span className="text-zinc-100 text-sm font-bold">{health?.resources.cpu_percent}%</span>
            </div>
            {/* RAM */}
            <div className="space-y-2 flex flex-col items-center">
              <Monitor className="h-5 w-5 text-zinc-500" />
              <span className="text-zinc-400">RAM Allocation</span>
              <span className="text-zinc-100 text-sm font-bold">{health?.resources.memory_percent}%</span>
            </div>
            {/* DISK */}
            <div className="space-y-2 flex flex-col items-center">
              <HardDrive className="h-5 w-5 text-zinc-500" />
              <span className="text-zinc-400">Disk Storage</span>
              <span className="text-zinc-100 text-sm font-bold">{health?.resources.disk_percent}%</span>
            </div>
          </div>
        </div>

        {/* API Statistics */}
        <div className="glass-panel p-5 rounded-xl border border-zinc-800 space-y-4">
          <h3 className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wider border-b border-zinc-850 pb-2">API Metrics</h3>
          
          <div className="space-y-2.5 font-mono text-[11px] text-zinc-400">
            <div className="flex justify-between">
              <span>Total Handled Calls</span>
              <span className="text-zinc-200 font-bold">{metrics?.total_requests || 0}</span>
            </div>
            <div className="flex justify-between">
              <span>Average Response Latency</span>
              <span className="text-zinc-200 font-bold">{metrics?.average_latency_seconds || 0.005}s</span>
            </div>
            <div className="flex justify-between">
              <span>Failed Call Ratio</span>
              <span className="text-zinc-200 font-bold">{metrics?.error_rate_percent || 0.0}%</span>
            </div>
            <div className="flex justify-between">
              <span>Active SSE Streams</span>
              <span className="text-zinc-200 font-bold">{metrics?.active_sse_connections || 0}</span>
            </div>
          </div>
        </div>

      </div>

      {/* Grid: Config Management & Export Options */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Configuration Panel */}
        <div className="glass-panel p-5 rounded-xl border border-zinc-800 space-y-4 lg:col-span-2">
          <h3 className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wider border-b border-zinc-850 pb-2">System Config settings</h3>
          
          <form onSubmit={handleUpdateConfig} className="grid grid-cols-1 sm:grid-cols-2 gap-4 font-mono text-xs text-zinc-400">
            <div className="space-y-1">
              <label className="text-[10px] text-zinc-500 uppercase block">Risk Boundary Limit (10-95)</label>
              <input
                type="number"
                value={config.risk_threshold}
                onChange={(e) => setConfig({ ...config, risk_threshold: parseInt(e.target.value) })}
                className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-zinc-500 uppercase block">Alert Filter Limit (10-95)</label>
              <input
                type="number"
                value={config.alert_threshold}
                onChange={(e) => setConfig({ ...config, alert_threshold: parseInt(e.target.value) })}
                className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-zinc-500 uppercase block">Threat Execution Delay (0.05x - 5.0x)</label>
              <input
                type="number"
                step="0.05"
                value={config.threat_delay_scale}
                onChange={(e) => setConfig({ ...config, threat_delay_scale: parseFloat(e.target.value) })}
                className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-zinc-500 uppercase block">Simulation Pacing Scale (1x - 100x)</label>
              <input
                type="number"
                value={config.simulation_speed}
                onChange={(e) => setConfig({ ...config, simulation_speed: parseFloat(e.target.value) })}
                className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-zinc-500 uppercase block">Impossible Travel Speed Limit (km/h)</label>
              <input
                type="number"
                value={config.impossible_travel_threshold}
                onChange={(e) => setConfig({ ...config, impossible_travel_threshold: parseFloat(e.target.value) })}
                className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-zinc-500 uppercase block">Fingerprint Spoof Sensitivity (0.0 - 1.0)</label>
              <input
                type="number"
                step="0.1"
                value={config.fingerprint_sensitivity}
                onChange={(e) => setConfig({ ...config, fingerprint_sensitivity: parseFloat(e.target.value) })}
                className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-zinc-500 uppercase block">Stuffing Security Window (sec)</label>
              <input
                type="number"
                value={config.credential_stuffing_window}
                onChange={(e) => setConfig({ ...config, credential_stuffing_window: parseInt(e.target.value) })}
                className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-zinc-500 uppercase block">Exfiltration Detection Window (sec)</label>
              <input
                type="number"
                value={config.exfiltration_detection_window}
                onChange={(e) => setConfig({ ...config, exfiltration_detection_window: parseInt(e.target.value) })}
                className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-zinc-500 uppercase block">Cold Start Observation Count</label>
              <input
                type="number"
                value={config.cold_start_observation_count}
                onChange={(e) => setConfig({ ...config, cold_start_observation_count: parseInt(e.target.value) })}
                className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-zinc-500 uppercase block">Drift Anomaly Sensitivity (0.0 - 1.0)</label>
              <input
                type="number"
                step="0.1"
                value={config.drift_sensitivity}
                onChange={(e) => setConfig({ ...config, drift_sensitivity: parseFloat(e.target.value) })}
                className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700"
              />
            </div>
            
            <div className="sm:col-span-2 pt-2 flex justify-end">
              <button
                type="submit"
                disabled={updating}
                className="bg-emerald-950/40 hover:bg-emerald-900/60 border border-emerald-500/30 text-emerald-400 px-4 py-2 rounded-lg font-mono tracking-wide transition-colors cursor-pointer disabled:opacity-50"
              >
                APPLY CONFIGURATION
              </button>
            </div>
          </form>
        </div>

        {/* Database Export Panel */}
        <div className="glass-panel p-5 rounded-xl border border-zinc-800 space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wider border-b border-zinc-850 pb-2">Logs Export Center</h3>
            
            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between items-center">
                <span className="text-zinc-400">Central Audit trail</span>
                <div className="flex space-x-1.5">
                  <button 
                    onClick={() => handleExport('audit', 'csv')}
                    className="bg-zinc-900 border border-zinc-800 hover:bg-zinc-850 p-1.5 rounded flex items-center text-zinc-300 transition-colors cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span className="text-[9px] font-bold ml-1">CSV</span>
                  </button>
                  <button 
                    onClick={() => handleExport('audit', 'json')}
                    className="bg-zinc-900 border border-zinc-800 hover:bg-zinc-850 p-1.5 rounded flex items-center text-zinc-300 transition-colors cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span className="text-[9px] font-bold ml-1">JSON</span>
                  </button>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-zinc-400">Security alert logs</span>
                <div className="flex space-x-1.5">
                  <button 
                    onClick={() => handleExport('alerts', 'csv')}
                    className="bg-zinc-900 border border-zinc-800 hover:bg-zinc-850 p-1.5 rounded flex items-center text-zinc-300 transition-colors cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span className="text-[9px] font-bold ml-1">CSV</span>
                  </button>
                  <button 
                    onClick={() => handleExport('alerts', 'json')}
                    className="bg-zinc-900 border border-zinc-800 hover:bg-zinc-850 p-1.5 rounded flex items-center text-zinc-300 transition-colors cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span className="text-[9px] font-bold ml-1">JSON</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="text-[10px] text-zinc-500 font-mono italic pt-4 border-t border-zinc-900">
            Exports limit queries up to 1000 history entries. Output format maps standard RFC standards.
          </div>
        </div>

      </div>

      {/* Central Audit Trail Log */}
      <div className="glass-panel rounded-xl border border-zinc-800 overflow-hidden flex flex-col">
        <div className="p-4 border-b border-zinc-850 bg-zinc-900/40 flex justify-between items-center">
          <h3 className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wide">Central System Audit logs</h3>
          <span className="text-[10px] text-zinc-500 font-mono">Traceability log for admin parameters shifts</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr className="bg-zinc-900/20 border-b border-zinc-850 text-zinc-500 text-[10px] uppercase tracking-wider">
                <th className="p-3.5 pl-4">Timestamp</th>
                <th className="p-3.5">Actor</th>
                <th className="p-3.5">Action Code</th>
                <th className="p-3.5">IP Address</th>
                <th className="p-3.5">Transaction Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-900 text-zinc-300">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-zinc-900/20 transition-colors">
                  <td className="p-3.5 pl-4 text-zinc-500 text-[10px]">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="p-3.5 text-zinc-400 font-bold">{log.user}</td>
                  <td className="p-3.5">
                    <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-zinc-800 text-zinc-300 uppercase">
                      {log.action}
                    </span>
                  </td>
                  <td className="p-3.5 text-zinc-500 text-[10px]">{log.ip_address}</td>
                  <td className="p-3.5 text-[11px] text-zinc-400">{log.details}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-6 text-center text-zinc-500">No database audit records written.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
