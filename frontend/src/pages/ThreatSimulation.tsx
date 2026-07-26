import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { 
  Play, 
  Square, 
  RotateCcw, 
  ShieldAlert, 
  ShieldCheck,
  Cpu, 
  Monitor, 
  Users, 
  Activity, 
  Clock, 
  AlertTriangle,
  RefreshCw
} from 'lucide-react';
import { useHealth } from '../context/HealthContext';

export const ThreatSimulation: React.FC = () => {
  const { backendConnected, dbConnected } = useHealth();
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  
  // Lists
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [activeRuns, setActiveRuns] = useState<any[]>([]);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  
  // Targets (dropdowns)
  const [users, setUsers] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [assets, setAssets] = useState<any[]>([]);
  
  // Selected target parameters
  const [targetUser, setTargetUser] = useState<string>('');
  const [targetDevice, setTargetDevice] = useState<string>('');
  const [targetAsset, setTargetAsset] = useState<string>('');
  const [delayScale, setDelayScale] = useState<number>(1.0);
  const [error, setError] = useState<string | null>(null);

  const fetchDropdowns = async () => {
    try {
      const [uRes, dRes, aRes] = await Promise.all([
        apiClient.get('/users'),
        apiClient.get('/devices'),
        apiClient.get('/industrial-assets')
      ]);
      setUsers(uRes.data);
      setDevices(dRes.data);
      setAssets(aRes.data);
    } catch (err) {
      console.error('Failed to load target dropdowns', err);
    }
  };

  const fetchScenarios = async () => {
    try {
      const res = await apiClient.get('/threats/scenarios');
      setScenarios(res.data);
    } catch (err) {
      console.error('Failed to load scenarios', err);
    }
  };

  const fetchTimelineAndRuns = async () => {
    if (!backendConnected || !dbConnected) return;
    try {
      const [runsRes, timelineRes, historyRes] = await Promise.all([
        apiClient.get('/threats/status'),
        apiClient.get('/threats/timeline'),
        apiClient.get('/threats/history')
      ]);
      setActiveRuns(runsRes.data);
      setTimeline(timelineRes.data);
      setHistory(historyRes.data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to poll Threat Simulation status logs.');
    }
  };

  const handleLaunch = async (scenarioId: string) => {
    setRefreshing(true);
    try {
      let url = `/threats/start/${scenarioId}?delay_scale=${delayScale}`;
      if (targetUser) url += `&target_user_id=${targetUser}`;
      if (targetDevice) url += `&target_device_id=${targetDevice}`;
      if (targetAsset) url += `&target_asset_id=${targetAsset}`;
      
      await apiClient.post(url);
      fetchTimelineAndRuns();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || 'Failed to trigger attack scenario.');
    } finally {
      setRefreshing(false);
    }
  };

  const handleStop = async (scenarioId: string) => {
    try {
      await apiClient.post(`/threats/stop/${scenarioId}`);
      fetchTimelineAndRuns();
    } catch (err) {
      console.error(err);
    }
  };

  const handleReset = async () => {
    try {
      await apiClient.post('/threats/reset');
      fetchTimelineAndRuns();
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchDropdowns(), fetchScenarios(), fetchTimelineAndRuns()]).finally(() => {
      setLoading(false);
    });

    // Poll timeline and run status every 2 seconds for real-time progress updates
    const interval = setInterval(fetchTimelineAndRuns, 2000);
    return () => clearInterval(interval);
  }, [backendConnected, dbConnected]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-zinc-800 pb-4 gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-wide text-white">THREAT SIMULATION CONTROL ROOM</h2>
          <p className="text-xs text-zinc-400 font-mono">Launch simulated industrial cyberattack scripts to validate AI detection thresholds</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleReset}
            className="flex items-center space-x-2 bg-red-950/20 hover:bg-red-950/40 border border-red-500/30 text-red-400 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>RESET ENGINE</span>
          </button>
          <button
            onClick={fetchTimelineAndRuns}
            className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>SYNC</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-950/20 border border-red-500/30 text-red-400 rounded-lg font-mono text-xs">
          {error}
        </div>
      )}

      {/* Target Configuration Panel */}
      <div className="glass-panel p-5 rounded-xl border border-zinc-800 space-y-4">
        <h3 className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wider">Attack Configuration & Targets Selection</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {/* User selector */}
          <div className="space-y-1 font-mono text-xs">
            <label className="text-zinc-500 block uppercase">Target User Profile</label>
            <select
              value={targetUser}
              onChange={(e) => setTargetUser(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700 font-mono"
            >
              <option value="">-- Random User --</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>@{u.username} ({u.role})</option>
              ))}
            </select>
          </div>

          {/* Device selector */}
          <div className="space-y-1 font-mono text-xs">
            <label className="text-zinc-500 block uppercase">Target Terminal Host</label>
            <select
              value={targetDevice}
              onChange={(e) => setTargetDevice(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700 font-mono"
            >
              <option value="">-- Random Host --</option>
              {devices.map((d) => (
                <option key={d.id} value={d.id}>{d.hostname} ({d.ip_address})</option>
              ))}
            </select>
          </div>

          {/* Asset selector */}
          <div className="space-y-1 font-mono text-xs">
            <label className="text-zinc-500 block uppercase">Target PLC Asset</label>
            <select
              value={targetAsset}
              onChange={(e) => setTargetAsset(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-zinc-700 font-mono"
            >
              <option value="">-- Random PLC --</option>
              {assets.map((a) => (
                <option key={a.id} value={a.id}>{a.name} ({a.ip_address})</option>
              ))}
            </select>
          </div>

          {/* Speed Modifier */}
          <div className="space-y-1 font-mono text-xs">
            <label className="text-zinc-500 block uppercase">Injection Delay Multiplier</label>
            <div className="flex items-center space-x-2">
              <input
                type="range"
                min="0.1"
                max="3.0"
                step="0.1"
                value={delayScale}
                onChange={(e) => setDelayScale(parseFloat(e.target.value))}
                className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
              />
              <span className="text-zinc-300 font-bold w-12 text-right">{delayScale.toFixed(1)}x</span>
            </div>
          </div>
        </div>
      </div>

      {/* Available Attack Scenarios Grid */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-zinc-300 font-mono uppercase tracking-wide">AVAILABLE ATTACK SIMULATIONS</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {scenarios.map((sc) => {
            const activeRun = activeRuns.find((r) => r.scenario_id === sc.scenario_id);
            const isRunning = activeRun && activeRun.status === 'RUNNING';

            return (
              <div key={sc.scenario_id} className="glass-panel p-5 rounded-xl border border-zinc-800 flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between items-start">
                    <h4 className="font-bold text-zinc-200 text-sm tracking-wide font-sans">{sc.name}</h4>
                    <span className="text-[10px] bg-zinc-900 border border-zinc-800 text-zinc-400 px-2 py-0.5 rounded font-mono">
                      {sc.total_steps} steps
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500 font-sans leading-relaxed">{sc.description}</p>
                </div>

                <div className="pt-2">
                  {isRunning ? (
                    <button
                      onClick={() => handleStop(sc.scenario_id)}
                      className="w-full flex items-center justify-center space-x-2 bg-red-950/40 hover:bg-red-900/60 border border-red-500/30 text-red-400 py-1.5 rounded-lg text-xs font-mono transition-colors"
                    >
                      <Square className="h-3.5 w-3.5 fill-red-400" />
                      <span>TERMINATE SIMULATION</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => handleLaunch(sc.scenario_id)}
                      disabled={refreshing}
                      className="w-full flex items-center justify-center space-x-2 bg-emerald-950/40 hover:bg-emerald-900/60 border border-emerald-500/30 text-emerald-400 py-1.5 rounded-lg text-xs font-mono transition-colors"
                    >
                      <Play className="h-3.5 w-3.5 fill-emerald-400" />
                      <span>LAUNCH SIMULATION</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Active Attack Simulations Panel */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-zinc-300 font-mono uppercase tracking-wide">ACTIVE SCENARIOS MONITOR</h3>
        <div className="glass-panel rounded-xl overflow-hidden border border-zinc-800">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="bg-zinc-900/60 border-b border-zinc-850 text-zinc-400 text-[10px] uppercase tracking-wider">
                  <th className="p-4">Running Threat Script</th>
                  <th className="p-4">Target Identity</th>
                  <th className="p-4">Simulation Progress</th>
                  <th className="p-4">AI Security Detection</th>
                  <th className="p-4">Assessed Risk</th>
                  <th className="p-4">Elapsed</th>
                  <th className="p-4">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900">
                {activeRuns.map((run) => (
                  <tr key={run.scenario_id} className="hover:bg-zinc-900/40 text-zinc-300">
                    <td className="p-4">
                      <div className="font-semibold text-zinc-200">{run.name}</div>
                      <div className="text-[10px] text-zinc-500 mt-0.5">Steps: {run.current_step_index} / {run.total_steps}</div>
                    </td>
                    <td className="p-4">
                      <div className="text-zinc-300">User: {run.target_user_id ? 'Scoped' : 'Randomized'}</div>
                      <div className="text-[10px] text-zinc-500">Host IP: {run.target_device_id ? 'Mapped' : 'Default'}</div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 w-24 bg-zinc-850 h-1.5 rounded-full overflow-hidden">
                          <div className="bg-emerald-500 h-full transition-all duration-500" style={{ width: `${run.progress}%` }}></div>
                        </div>
                        <span className="text-zinc-400 font-bold">{run.progress}%</span>
                      </div>
                    </td>
                    <td className="p-4">
                      {run.detected ? (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/30 animate-pulse">
                          <ShieldAlert className="h-3 w-3 text-red-400 shrink-0" />
                          <span>FLAGGED DETECTED</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-zinc-900 text-zinc-400 border border-zinc-800">
                          <ShieldCheck className="h-3 w-3 text-zinc-500 shrink-0" />
                          <span>UNDETECTED</span>
                        </span>
                      )}
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        run.risk_level === 'Critical' ? 'bg-red-500/10 text-red-400 border border-red-500/30' :
                        run.risk_level === 'High' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/30' :
                        run.risk_level === 'Medium' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30' :
                        'bg-zinc-800 text-zinc-400'
                      }`}>
                        {run.risk_level} RISK
                      </span>
                    </td>
                    <td className="p-4 text-zinc-400 flex items-center space-x-1 mt-1.5">
                      <Clock className="h-3.5 w-3.5 shrink-0" />
                      <span>{new Date(run.started_at).toLocaleTimeString()}</span>
                    </td>
                    <td className="p-4">
                      <button
                        onClick={() => handleStop(run.scenario_id)}
                        className="bg-red-950/20 hover:bg-red-950/40 border border-red-500/30 text-red-400 p-1.5 rounded transition-colors"
                      >
                        <Square className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
                {activeRuns.length === 0 && (
                  <tr>
                    <td colSpan={7} className="p-6 text-center text-zinc-500 font-mono">No threat scenarios currently running in the Digital Twin.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Live Attack Timeline Feed */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5 text-emerald-400" />
          <h3 className="text-sm font-bold text-zinc-300 font-mono uppercase tracking-wide">Live Attack Timeline Log</h3>
        </div>

        <div className="glass-panel rounded-xl overflow-hidden border border-zinc-800/80">
          <div className="overflow-y-auto max-h-72">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="bg-zinc-900/60 border-b border-zinc-850 text-zinc-400 text-[10px] uppercase tracking-wider sticky top-0">
                  <th className="p-4">Time</th>
                  <th className="p-4">Scenario</th>
                  <th className="p-4">Execution Step Action</th>
                  <th className="p-4">Payload Summary</th>
                  <th className="p-4">Severity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900">
                {timeline.map((step) => (
                  <tr key={step.id} className="hover:bg-zinc-900/40 text-zinc-300">
                    <td className="p-4 text-zinc-500 text-[11px] whitespace-nowrap">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="p-4 font-semibold text-zinc-300 whitespace-nowrap">{step.scenario_name}</td>
                    <td className="p-4 text-emerald-400 whitespace-nowrap">{step.current_step}</td>
                    <td className="p-4 text-zinc-400">{step.payload_summary}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        step.severity === 'Critical' ? 'bg-red-500/15 text-red-400' :
                        step.severity === 'Warning' ? 'bg-yellow-500/15 text-yellow-400' :
                        'bg-zinc-900 text-zinc-400'
                      }`}>
                        {step.severity}
                      </span>
                    </td>
                  </tr>
                ))}
                {timeline.length === 0 && (
                  <tr>
                    <td colSpan={5} className="p-6 text-center text-zinc-500 font-mono">No simulation steps executed yet. Launch an attack script above.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
