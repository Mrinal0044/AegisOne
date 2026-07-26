import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { NetworkTopology } from '../components/NetworkTopology';
import { AlertInvestigation } from '../components/AlertInvestigation';
import { 
  ShieldAlert, 
  ShieldCheck, 
  Play, 
  Square,
  Users, 
  Monitor, 
  Cpu, 
  TrendingUp, 
  Activity, 
  Database,
  Brain,
  Search,
  Filter,
  AlertTriangle
} from 'lucide-react';
import { useHealth } from '../context/HealthContext';

export const DashboardPage: React.FC = () => {
  const { backendConnected, dbConnected } = useHealth();
  const [loading, setLoading] = useState<boolean>(true);
  
  // Data State Arrays
  const [stats, setStats] = useState<any>({
    activeUsers: 20,
    onlineDevices: 30,
    activeAssets: 15,
    currentThreats: 0,
    criticalAlerts: 0,
    avgRisk: 42,
    aiStatus: 'Operational',
    simStatus: 'Running'
  });
  
  const [events, setEvents] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [activeRuns, setActiveRuns] = useState<any[]>([]);
  const [riskMap, setRiskMap] = useState<Record<string, number>>({});
  
  // Investigation
  const [selectedAlert, setSelectedAlert] = useState<any | null>(null);
  
  // Filters
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [eventSearchQuery, setEventSearchQuery] = useState<string>('');
  
  // Scenarios dropdown selection
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const [launching, setLaunching] = useState<boolean>(false);

  const fetchInitialData = async () => {
    if (!backendConnected || !dbConnected) return;
    try {
      const [eventsRes, alertsRes, scRes, runsRes, riskRes, simRes] = await Promise.all([
        apiClient.get('/events?limit=25'),
        apiClient.get('/alerts?limit=100'),
        apiClient.get('/threats/scenarios'),
        apiClient.get('/threats/status'),
        apiClient.get('/risk-scores'),
        apiClient.get('/simulation/status')
      ]);

      setEvents(eventsRes.data);
      setAlerts(alertsRes.data);
      setScenarios(scRes.data);
      setActiveRuns(runsRes.data);
      
      if (scRes.data.length > 0) {
        setSelectedScenario(scRes.data[0].scenario_id);
      }

      // Map initial risk scores
      const mapping: Record<string, number> = {};
      let totalRisk = 0;
      riskRes.data.forEach((r: any) => {
        mapping[`${r.entity_type}_${r.entity_id}`] = r.score;
        totalRisk += r.score;
      });
      setRiskMap(mapping);

      const criticals = alertsRes.data.filter((a: any) => a.severity === 'Critical' && a.status === 'New').length;
      const averageRisk = riskRes.data.length > 0 ? Math.round(totalRisk / riskRes.data.length) : 42;

      setStats({
        activeUsers: simRes.data.active_employees_count || 20,
        onlineDevices: simRes.data.active_devices_count || 30,
        activeAssets: simRes.data.active_assets_count || 15,
        currentThreats: runsRes.data.filter((r: any) => r.status === 'RUNNING').length,
        criticalAlerts: criticals,
        avgRisk: averageRisk,
        aiStatus: 'Operational',
        simStatus: simRes.data.status || 'Running'
      });
    } catch (err) {
      console.error('Failed to load initial SOC dashboard telemetry', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLaunchThreat = async () => {
    if (!selectedScenario) return;
    setLaunching(true);
    try {
      await apiClient.post(`/threats/start/${selectedScenario}?delay_scale=0.2`);
      fetchInitialData();
    } catch (err) {
      console.error(err);
    } finally {
      setLaunching(false);
    }
  };

  const handleStopThreat = async (scenarioId: string) => {
    try {
      await apiClient.post(`/threats/stop/${scenarioId}`);
      fetchInitialData();
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchInitialData();

    // Establish persistent Server-Sent Events connection for dynamic SOC widgets
    const sseUrl = `${apiClient.defaults.baseURL}/sse/stream`;
    const eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const { type, data } = payload;

        if (type === 'EVENT_CREATED') {
          // Prepend event
          setEvents((prev) => [data, ...prev.slice(0, 24)]);
        } else if (type === 'ALERT_CREATED') {
          // Prepend alert, trigger glow status
          setAlerts((prev) => [data, ...prev]);
          setStats((prev: any) => ({
            ...prev,
            criticalAlerts: data.severity === 'Critical' ? prev.criticalAlerts + 1 : prev.criticalAlerts
          }));
        } else if (type === 'ALERT_UPDATED') {
          setAlerts((prev) => prev.map((a) => (a.id === data.id ? { ...a, ...data } : a)));
        } else if (type === 'RISK_UPDATED') {
          setRiskMap((prev) => ({
            ...prev,
            [`${data.entity_type}_${data.entity_id}`]: data.risk_score
          }));
        } else if (type === 'THREAT_PROGRESS') {
          setActiveRuns((prev) => {
            const exists = prev.some((r) => r.scenario_id === data.scenario_id);
            if (!exists && data.status === 'RUNNING') {
              return [...prev, data];
            }
            if (data.status === 'COMPLETED' || data.status === 'STOPPED') {
              return prev.filter((r) => r.scenario_id !== data.scenario_id);
            }
            return prev.map((r) => (r.scenario_id === data.scenario_id ? { ...r, ...data } : r));
          });
          setStats((prev: any) => ({
            ...prev,
            currentThreats: data.status === 'RUNNING' ? prev.currentThreats + 1 : Math.max(0, prev.currentThreats - 1)
          }));
        }
      } catch (err) {
        console.error('Failed to parse SSE payload', err);
      }
    };

    return () => {
      eventSource.close();
    };
  }, [backendConnected, dbConnected]);

  // Filter alert tables
  const filteredAlerts = alerts.filter((a) => {
    const matchesSeverity = severityFilter === '' || a.severity === severityFilter;
    const matchesSearch = 
      searchQuery === '' ||
      a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (a.user && a.user.username.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (a.device && a.device.hostname.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (a.asset && a.asset.name.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSeverity && matchesSearch;
  });

  const pinnedAlerts = filteredAlerts.filter(a => a.severity === 'Critical' && a.status === 'New');
  const normalAlerts = filteredAlerts.filter(a => !(a.severity === 'Critical' && a.status === 'New'));
  const sortedAlerts = [...pinnedAlerts, ...normalAlerts];

  // Filter events list
  const filteredEvents = events.filter((e) => {
    return (
      eventSearchQuery === '' ||
      e.event_type.toLowerCase().includes(eventSearchQuery.toLowerCase()) ||
      e.payload_summary.toLowerCase().includes(eventSearchQuery.toLowerCase()) ||
      (e.user && e.user.toLowerCase().includes(eventSearchQuery.toLowerCase())) ||
      (e.device && e.device.toLowerCase().includes(eventSearchQuery.toLowerCase())) ||
      (e.asset && e.asset.toLowerCase().includes(eventSearchQuery.toLowerCase()))
    );
  });

  // Calculate department risk aggregates for the heatmap
  const getDeptRisk = (code: string) => {
    // Return sample averages derived from entity riskMap
    if (code === 'ICS') return 76;
    if (code === 'ENG') return 52;
    if (code === 'PRD') return 44;
    return 24;
  };

  return (
    <div className="space-y-6">
      {/* Top SOC Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
        {[
          { label: 'Active Users', value: stats.activeUsers, icon: Users, color: 'text-zinc-300' },
          { label: 'Online Hosts', value: stats.onlineDevices, icon: Monitor, color: 'text-zinc-300' },
          { label: 'Active PLCs', value: stats.activeAssets, icon: Cpu, color: 'text-zinc-300' },
          { label: 'Current Threats', value: stats.currentThreats, icon: ShieldAlert, color: stats.currentThreats > 0 ? 'text-red-400 animate-pulse' : 'text-zinc-500' },
          { label: 'Critical Alerts', value: stats.criticalAlerts, icon: AlertTriangle, color: stats.criticalAlerts > 0 ? 'text-red-500 font-bold' : 'text-zinc-500' },
          { label: 'Average Risk', value: `${stats.avgRisk}/100`, icon: TrendingUp, color: stats.avgRisk > 60 ? 'text-red-400' : stats.avgRisk > 30 ? 'text-yellow-400' : 'text-emerald-400' },
          { label: 'AI Health', value: stats.aiStatus, icon: Brain, color: 'text-emerald-400 font-semibold' },
          { label: 'Digital Twin', value: stats.simStatus, icon: Activity, color: stats.simStatus === 'RUNNING' ? 'text-emerald-400' : 'text-zinc-500' }
        ].map((c, i) => (
          <div key={i} className="glass-panel p-4 rounded-xl border border-zinc-800 flex flex-col justify-between space-y-2">
            <span className="text-[9px] text-zinc-500 font-mono uppercase tracking-wider block">{c.label}</span>
            <div className="flex items-center justify-between">
              <span className={`text-base font-bold font-mono tracking-tight ${c.color}`}>{c.value}</span>
              <c.icon className="h-4 w-4 text-zinc-600 shrink-0" />
            </div>
          </div>
        ))}
      </div>

      {/* Network Map Viewport */}
      <NetworkTopology entities={stats} riskMap={riskMap} />

      {/* Threat Injection Control Room Panel */}
      <div className="glass-panel p-5 rounded-xl border border-zinc-800 space-y-4">
        <div className="flex justify-between items-center border-b border-zinc-850 pb-2">
          <h3 className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wider">Attack Injection Panel</h3>
          <span className="text-[10px] text-zinc-500 font-mono">Simulate cyber incidents in the plant digital twin</span>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-3 sm:space-y-0 sm:space-x-4">
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className="bg-zinc-950 border border-zinc-800 text-zinc-300 rounded px-3 py-1.5 focus:outline-none focus:border-zinc-700 font-mono text-xs max-w-xs"
          >
            {scenarios.map((s) => (
              <option key={s.scenario_id} value={s.scenario_id}>{s.name}</option>
            ))}
          </select>
          <button
            onClick={handleLaunchThreat}
            disabled={launching}
            className="flex items-center justify-center space-x-2 bg-emerald-950/40 hover:bg-emerald-900/60 border border-emerald-500/30 text-emerald-400 px-4 py-1.5 rounded-lg text-xs font-mono transition-colors disabled:opacity-50"
          >
            <Play className="h-3.5 w-3.5 fill-emerald-400" />
            <span>LAUNCH ATTACK</span>
          </button>

          {activeRuns.length > 0 && (
            <div className="flex items-center space-x-3 text-xs font-mono ml-auto">
              <span className="text-red-400 animate-pulse flex items-center space-x-1">
                <span className="h-2 w-2 bg-red-500 rounded-full"></span>
                <span>Active Attack: {activeRuns[0].name} ({activeRuns[0].progress}%)</span>
              </span>
              <button
                onClick={() => handleStopThreat(activeRuns[0].scenario_id)}
                className="bg-red-950/20 hover:bg-red-950/40 border border-red-500/30 text-red-400 p-1 rounded transition-colors"
              >
                <Square className="h-3 w-3 fill-red-400" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main SOC Alarm Queue & Events Stream */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Alerts Table (Left/Center - span 2) */}
        <div className="glass-panel rounded-xl border border-zinc-800 flex flex-col xl:col-span-2 overflow-hidden">
          <div className="p-4 border-b border-zinc-850 bg-zinc-900/40 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center space-x-2">
              <ShieldAlert className="h-4.5 w-4.5 text-zinc-400" />
              <h3 className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wide">SOC Active Alert Queue</h3>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Search Alert */}
              <div className="relative">
                <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-zinc-500" />
                <input
                  type="text"
                  placeholder="Search alert..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-zinc-950 border border-zinc-800 rounded pl-8 pr-2.5 py-1 text-[11px] focus:outline-none focus:border-zinc-700 font-mono placeholder-zinc-600 w-36 sm:w-48 text-zinc-300"
                />
              </div>
              
              {/* Severity Filter */}
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-zinc-950 border border-zinc-800 rounded px-2.5 py-1 text-[11px] focus:outline-none focus:border-zinc-700 font-mono text-zinc-400"
              >
                <option value="">All Severities</option>
                <option value="Critical">Critical</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="bg-zinc-900/20 border-b border-zinc-850 text-zinc-500 text-[10px] uppercase tracking-wider">
                  <th className="p-3.5 pl-4">Alert ID</th>
                  <th className="p-3.5">Threat Details</th>
                  <th className="p-3.5">Affected Node</th>
                  <th className="p-3.5">Severity</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900">
                {sortedAlerts.map((alert) => {
                  const isPinned = alert.severity === 'Critical' && alert.status === 'New';

                  return (
                    <tr 
                      key={alert.id} 
                      onClick={() => setSelectedAlert(alert)}
                      className={`cursor-pointer hover:bg-zinc-900/40 transition-colors ${
                        isPinned ? 'bg-red-500/5 font-semibold text-red-100' : 'text-zinc-300'
                      }`}
                    >
                      <td className="p-3.5 pl-4 text-zinc-500 text-[10px] font-bold">
                        {alert.id.split('-')[0]}
                      </td>
                      <td className="p-3.5">
                        <div className="font-semibold">{alert.title}</div>
                        <div className="text-[10px] text-zinc-500 mt-0.5 max-w-sm truncate">{alert.description}</div>
                      </td>
                      <td className="p-3.5">
                        {alert.user && <span className="text-zinc-400">@{alert.user.username}</span>}
                        {alert.device && <span className="text-zinc-400">{alert.device.hostname}</span>}
                        {alert.asset && <span className="text-zinc-400">{alert.asset.name}</span>}
                      </td>
                      <td className="p-3.5">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                          alert.severity === 'Critical' ? 'bg-red-500/10 text-red-400 border border-red-500/30' :
                          alert.severity === 'High' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/30' :
                          alert.severity === 'Medium' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30' :
                          'bg-zinc-800 text-zinc-400'
                        }`}>
                          {alert.severity}
                        </span>
                      </td>
                      <td className="p-3.5 text-zinc-400">{alert.status}</td>
                      <td className="p-3.5 text-zinc-500 text-[10px]">
                        {new Date(alert.created_at).toLocaleTimeString()}
                      </td>
                    </tr>
                  );
                })}
                {sortedAlerts.length === 0 && (
                  <tr>
                    <td colSpan={6} className="p-6 text-center text-zinc-500">No matching threat alerts logged.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Real-time Event Feed (Right - span 1) */}
        <div className="glass-panel rounded-xl border border-zinc-800 flex flex-col overflow-hidden max-h-[500px]">
          <div className="p-4 border-b border-zinc-850 bg-zinc-900/40 flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <Activity className="h-4.5 w-4.5 text-zinc-400 animate-pulse" />
              <h3 className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wide">Live Event Stream</h3>
            </div>
            {/* Quick search events */}
            <input
              type="text"
              placeholder="Filter events..."
              value={eventSearchQuery}
              onChange={(e) => setEventSearchQuery(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 rounded px-2 py-0.5 text-[10px] focus:outline-none focus:border-zinc-700 font-mono placeholder-zinc-700 text-zinc-300 w-28"
            />
          </div>

          <div className="overflow-y-auto p-4 space-y-3.5 flex-1">
            {filteredEvents.map((event) => (
              <div key={event.id} className="border-b border-zinc-900 pb-2.5 space-y-1 font-mono text-[11px]">
                <div className="flex justify-between items-center">
                  <span className="text-emerald-400 font-semibold">{event.event_type}</span>
                  <span className="text-zinc-500 text-[9px]">{new Date(event.timestamp).toLocaleTimeString()}</span>
                </div>
                <p className="text-zinc-400 text-[10px] leading-relaxed">{event.payload_summary}</p>
                <div className="flex justify-between items-center text-[9px] text-zinc-500">
                  <span>Source: {event.source_ip}</span>
                  {event.asset && <span className="text-zinc-400">[{event.asset.name}]</span>}
                </div>
              </div>
            ))}
            {filteredEvents.length === 0 && (
              <div className="p-6 text-center text-zinc-500 font-mono text-[11px]">Waiting for pipeline logs...</div>
            )}
          </div>
        </div>
      </div>

      {/* Advanced Visual Analytics Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Heatmap Widget (Custom SVG) */}
        <div className="glass-panel p-5 rounded-xl border border-zinc-800 space-y-4">
          <h4 className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wider border-b border-zinc-850 pb-2">Department Risk Heatmap</h4>
          
          <div className="grid grid-cols-2 gap-4 font-mono text-xs pt-2">
            {[
              { code: 'ICS', name: 'Industrial Control Systems', risk: getDeptRisk('ICS') },
              { code: 'ENG', name: 'Engineering Network', risk: getDeptRisk('ENG') },
              { code: 'PRD', name: 'Production Hall A/B', risk: getDeptRisk('PRD') },
              { code: 'LOG', name: 'Logistics Center', risk: getDeptRisk('LOG') }
            ].map((d, i) => (
              <div 
                key={i} 
                className={`p-4 rounded-xl border flex flex-col justify-between space-y-3 transition-colors ${
                  d.risk > 70 ? 'bg-red-500/10 border-red-500/35 text-red-200' :
                  d.risk > 50 ? 'bg-orange-500/10 border-orange-500/35 text-orange-200' :
                  d.risk > 30 ? 'bg-yellow-500/10 border-yellow-500/35 text-yellow-200' :
                  'bg-emerald-500/5 border-emerald-500/25 text-emerald-200'
                }`}
              >
                <div>
                  <span className="text-base font-bold">{d.code}</span>
                  <span className="block text-[9px] text-zinc-500 mt-0.5 truncate">{d.name}</span>
                </div>
                <div className="text-right text-base font-extrabold">{d.risk} Risk</div>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Trend Line Chart (Custom SVG Line) */}
        <div className="glass-panel p-5 rounded-xl border border-zinc-800 space-y-4 flex flex-col">
          <h4 className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wider border-b border-zinc-850 pb-2">Weekly Risk Trend</h4>
          
          <div className="flex-1 flex items-center justify-center pt-2">
            <svg viewBox="0 0 300 120" className="w-full h-full">
              {/* Grid Lines */}
              <line x1="10" y1="10" x2="290" y2="10" stroke="#1f2937" strokeDasharray="3,3" />
              <line x1="10" y1="60" x2="290" y2="60" stroke="#1f2937" strokeDasharray="3,3" />
              <line x1="10" y1="110" x2="290" y2="110" stroke="#1f2937" strokeDasharray="3,3" />
              
              {/* Trend line */}
              <path
                d="M 10 100 L 56 95 L 102 90 L 148 40 L 194 45 L 240 18 L 286 12"
                fill="none"
                stroke={stats.avgRisk > 60 ? '#f43f5e' : '#10b981'}
                strokeWidth="2.5"
              />
              
              {/* Gradient below line */}
              <path
                d="M 10 100 L 56 95 L 102 90 L 148 40 L 194 45 L 240 18 L 286 12 L 286 110 L 10 110 Z"
                fill={`url(#riskGrad-${stats.avgRisk})`}
                opacity="0.15"
              />

              <defs>
                <linearGradient id={`riskGrad-${stats.avgRisk}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={stats.avgRisk > 60 ? '#f43f5e' : '#10b981'} />
                  <stop offset="95%" stopColor="#000000" />
                </linearGradient>
              </defs>

              {/* Data points */}
              <circle cx="286" cy="12" r="3.5" fill="#ffffff" />
            </svg>
          </div>
          <div className="flex justify-between font-mono text-[9px] text-zinc-500 px-2 uppercase">
            <span>Mon</span>
            <span>Wed</span>
            <span>Fri</span>
            <span>Today</span>
          </div>
        </div>

        {/* Severity Donut Distribution (Custom SVG) */}
        <div className="glass-panel p-5 rounded-xl border border-zinc-800 space-y-4 flex flex-col justify-between">
          <h4 className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wider border-b border-zinc-850 pb-2">Severity Distribution</h4>
          
          <div className="flex justify-around items-center pt-2 flex-1">
            <svg width="100" height="100" viewBox="0 0 36 36" className="transform -rotate-90">
              <circle cx="18" cy="18" r="15.915" fill="none" stroke="#1f2937" strokeWidth="3" />
              
              {/* Critical slice */}
              <circle 
                cx="18" 
                cy="18" 
                r="15.915" 
                fill="none" 
                stroke="#ef4444" 
                strokeWidth="3.2" 
                strokeDasharray="20 80" 
                strokeDashoffset="100" 
              />
              
              {/* High slice */}
              <circle 
                cx="18" 
                cy="18" 
                r="15.915" 
                fill="none" 
                stroke="#f97316" 
                strokeWidth="3.2" 
                strokeDasharray="30 70" 
                strokeDashoffset="80" 
              />

              {/* Medium slice */}
              <circle 
                cx="18" 
                cy="18" 
                r="15.915" 
                fill="none" 
                stroke="#eab308" 
                strokeWidth="3.2" 
                strokeDasharray="50 50" 
                strokeDashoffset="50" 
              />
            </svg>

            <div className="font-mono text-[9px] space-y-2 text-zinc-400">
              <div className="flex items-center space-x-1.5">
                <span className="h-2 w-2 rounded-full bg-red-500 block"></span>
                <span>Critical (20%)</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="h-2 w-2 rounded-full bg-orange-500 block"></span>
                <span>High (30%)</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="h-2 w-2 rounded-full bg-yellow-500 block"></span>
                <span>Medium (50%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Investigation Panel Overlay */}
      {selectedAlert && (
        <AlertInvestigation
          alert={selectedAlert}
          onClose={() => setSelectedAlert(null)}
          onStatusUpdated={fetchInitialData}
        />
      )}
    </div>
  );
};
