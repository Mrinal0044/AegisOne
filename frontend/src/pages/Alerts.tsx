import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import type { Alert } from '../types';
import { ShieldAlert, RefreshCw, AlertTriangle, ShieldCheck, Filter } from 'lucide-react';
import { useHealth } from '../context/HealthContext';

export const Alerts: React.FC = () => {
  const { backendConnected, dbConnected } = useHealth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [severityFilter, setSeverityFilter] = useState<string>('All');
  const [statusFilter, setStatusFilter] = useState<string>('All');

  const fetchAlerts = async () => {
    if (!backendConnected || !dbConnected) return;
    setLoading(true);
    try {
      const response = await apiClient.get<Alert[]>('/alerts');
      setAlerts(response.data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch security alerts database.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [backendConnected, dbConnected]);

  const filteredAlerts = alerts.filter(alert => {
    const sevMatch = severityFilter === 'All' || alert.severity === severityFilter;
    const statMatch = statusFilter === 'All' || alert.status === statusFilter;
    return sevMatch && statMatch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-wide text-white">OT INTELLIGENCE THREAT ALERTS</h2>
          <p className="text-xs text-zinc-400 font-mono">Real-time behavior indicators, network anomalies and protocol exploits</p>
        </div>
        <button
          onClick={fetchAlerts}
          className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>POLL THREAT HUBS</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/20 border border-red-500/30 text-red-400 rounded-lg font-mono text-xs">
          {error}
        </div>
      )}

      {/* Filters Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-zinc-950/40 border border-zinc-800/80 px-4 py-3 rounded-xl">
        <div className="flex items-center space-x-2 text-zinc-400 text-xs font-mono">
          <Filter className="h-3.5 w-3.5 text-zinc-500" />
          <span>FILTER CONTROLS:</span>
        </div>
        <div className="flex items-center space-x-4">
          {/* Severity Filter */}
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="text-zinc-500">SEVERITY:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-zinc-900 border border-zinc-800 text-zinc-300 rounded px-2 py-1 text-xs focus:outline-none focus:border-zinc-700"
            >
              <option value="All">ALL SEVERITIES</option>
              <option value="Critical">CRITICAL</option>
              <option value="High">HIGH</option>
              <option value="Medium">MEDIUM</option>
              <option value="Low">LOW</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="text-zinc-500">STATUS:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-zinc-900 border border-zinc-800 text-zinc-300 rounded px-2 py-1 text-xs focus:outline-none focus:border-zinc-700"
            >
              <option value="All">ALL STATUSES</option>
              <option value="New">NEW</option>
              <option value="Investigating">INVESTIGATING</option>
              <option value="Resolved">RESOLVED</option>
              <option value="False Positive">FALSE POSITIVE</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-zinc-500 font-mono text-xs">Querying alerts registry...</div>
      ) : filteredAlerts.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 glass-panel rounded-xl space-y-3">
          <ShieldCheck className="h-12 w-12 text-emerald-500/30 animate-pulse-slow" />
          <div className="text-center">
            <h4 className="text-sm font-bold text-zinc-300 font-mono">NO ACTIVE SEVERITIES MATCHED</h4>
            <p className="text-xs text-zinc-500 mt-1">Adjust filters or reload to fetch active threats.</p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`glass-panel p-5 rounded-xl border relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all duration-300 ${
                alert.severity === 'Critical' ? 'border-red-500/30 hover:border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.03)]' :
                alert.severity === 'High' ? 'border-orange-500/20 hover:border-orange-500/40' :
                alert.severity === 'Medium' ? 'border-yellow-500/20 hover:border-yellow-500/40' :
                'border-cyan-500/20 hover:border-cyan-500/40'
              }`}
            >
              {/* Criticality left indicator border */}
              <div className={`absolute left-0 top-0 bottom-0 w-1 ${
                alert.severity === 'Critical' ? 'bg-red-500' :
                alert.severity === 'High' ? 'bg-orange-500' :
                alert.severity === 'Medium' ? 'bg-yellow-500' :
                'bg-cyan-500'
              }`}></div>

              {/* Alert Content */}
              <div className="flex-1 flex items-start space-x-4 pl-2">
                <div className={`p-2.5 rounded-lg shrink-0 mt-0.5 ${
                  alert.severity === 'Critical' ? 'bg-red-500/10 text-red-500' :
                  alert.severity === 'High' ? 'bg-orange-500/10 text-orange-500' :
                  alert.severity === 'Medium' ? 'bg-yellow-500/10 text-yellow-500' :
                  'bg-cyan-500/10 text-cyan-500'
                }`}>
                  <AlertTriangle className="h-5 w-5" />
                </div>
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-bold text-zinc-100">{alert.title}</h3>
                    <span className={`text-[9px] font-bold font-mono px-2 py-0.5 rounded border ${
                      alert.severity === 'Critical' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                      alert.severity === 'High' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' :
                      alert.severity === 'Medium' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                      'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
                    }`}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className="text-[9px] bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded font-mono border border-zinc-700/50">
                      {alert.category}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-400 font-sans leading-relaxed max-w-3xl">
                    {alert.description}
                  </p>
                  
                  {/* Scope details */}
                  <div className="flex flex-wrap gap-4 pt-1 font-mono text-[10px] text-zinc-500">
                    {alert.asset && (
                      <div>
                        <span>TARGET ASSET: </span>
                        <span className="text-zinc-400 font-semibold">{alert.asset.name} ({alert.asset.ip_address})</span>
                      </div>
                    )}
                    {alert.device && (
                      <div>
                        <span>ORIGIN HOST: </span>
                        <span className="text-zinc-400 font-semibold">{alert.device.hostname}</span>
                      </div>
                    )}
                    {alert.user && (
                      <div>
                        <span>OPERATOR: </span>
                        <span className="text-zinc-400 font-semibold">{alert.user.full_name} ({alert.user.username})</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Status Action Block */}
              <div className="flex flex-col items-end justify-between self-stretch shrink-0 py-1 font-mono text-xs">
                <div className="text-zinc-500 text-[10px] uppercase">
                  {new Date(alert.created_at).toLocaleDateString()} &bull; {new Date(alert.created_at).toLocaleTimeString()}
                </div>
                
                {/* Status Indicator */}
                <span className={`text-[10px] font-bold px-2.5 py-1 rounded border ${
                  alert.status === 'New' ? 'bg-red-500/10 text-red-400 border-red-500/20 animate-pulse-slow' :
                  alert.status === 'Investigating' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                  alert.status === 'Resolved' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                  'bg-zinc-800 text-zinc-400 border-zinc-700'
                }`}>
                  STATUS: {alert.status.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
