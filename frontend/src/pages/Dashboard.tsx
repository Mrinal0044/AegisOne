import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, Cpu, Monitor, Activity, ShieldCheck, Database, 
  Play, Pause, Square, RotateCcw, Save, Sliders, Timer, Users, HardDrive
} from 'lucide-react';
import apiClient from '../api/client';
import type { Alert, Event } from '../types';
import { useHealth } from '../context/HealthContext';

interface SimState {
  status: string;
  virtual_system_time: string;
  total_events: number;
  employees_count: number;
  devices_count: number;
  assets_count: number;
}

export const Dashboard: React.FC = () => {
  const { backendConnected, dbConnected, checkHealth } = useHealth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  
  // Simulation states
  const [simStatus, setSimStatus] = useState<string>('IDLE');
  const [virtualTime, setVirtualTime] = useState<string>('N/A');
  const [totalEvents, setTotalEvents] = useState<number>(0);
  const [empCount, setEmpCount] = useState<number>(0);
  const [devCount, setDevCount] = useState<number>(0);
  const [astCount, setAstCount] = useState<number>(0);

  // Config form states
  const [speedMultiplier, setSpeedMultiplier] = useState<number>(1);
  const [eventRate, setEventRate] = useState<number>(1);
  const [targetEmployees, setTargetEmployees] = useState<number>(20);
  const [targetDevices, setTargetDevices] = useState<number>(30);
  const [configSaving, setConfigSaving] = useState<boolean>(false);

  const fetchStats = async () => {
    if (!backendConnected || !dbConnected) return;
    try {
      const [alertsRes, eventsRes] = await Promise.all([
        apiClient.get<Alert[]>('/alerts?limit=5'),
        apiClient.get<Event[]>('/events?limit=5'),
      ]);
      setAlerts(alertsRes.data);
      setEvents(eventsRes.data);
    } catch (err) {
      console.error("Error fetching statistics", err);
    }
  };

  const fetchSimulationStatus = async () => {
    if (!backendConnected || !dbConnected) return;
    try {
      const res = await apiClient.get('/simulation/status');
      const data = res.data;
      setSimStatus(data.status);
      setVirtualTime(data.virtual_system_time);
      setTotalEvents(data.state.total_events_generated);
      setEmpCount(data.active_employees_count);
      setDevCount(data.active_devices_count);
      setAstCount(data.active_assets_count);

      // Map config form defaults if they are not already set by the user
      setSpeedMultiplier(data.config.speed_multiplier);
      setEventRate(data.config.event_rate);
      setTargetEmployees(data.config.num_employees);
      setTargetDevices(data.config.num_devices);
    } catch (err) {
      console.error("Error fetching simulation status", err);
    }
  };

  // Poll simulation status and stats
  useEffect(() => {
    fetchSimulationStatus();
    fetchStats();
    setLoading(false);

    const interval = setInterval(() => {
      fetchSimulationStatus();
      fetchStats();
    }, 3000);

    return () => clearInterval(interval);
  }, [backendConnected, dbConnected]);

  // Simulation controls
  const handleSimAction = async (action: 'start' | 'pause' | 'resume' | 'stop' | 'reset') => {
    if (!backendConnected || !dbConnected) return;
    try {
      const res = await apiClient.post(`/simulation/${action}`);
      const data = res.data;
      setSimStatus(data.status);
      setVirtualTime(data.virtual_system_time);
      setTotalEvents(data.state.total_events_generated);
      fetchStats();
    } catch (err) {
      console.error(`Error performing simulation action ${action}`, err);
    }
  };

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!backendConnected || !dbConnected) return;
    setConfigSaving(true);
    try {
      await apiClient.post('/simulation/config', {
        speed_multiplier: speedMultiplier,
        event_rate: eventRate,
        num_employees: targetEmployees,
        num_devices: targetDevices,
        is_active: true
      });
      fetchSimulationStatus();
    } catch (err) {
      console.error("Error saving simulation configuration", err);
    } finally {
      setConfigSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h2 className="text-2xl font-bold tracking-wide font-sans text-white">SIMULATION WORKSPACE</h2>
        <p className="text-xs text-zinc-400 font-mono">OT Behavioral Simulation Panel & Cyber Range Control</p>
      </div>

      {/* Network Alert if Disconnected */}
      {(!backendConnected || !dbConnected) && (
        <div className="glass-panel critical-glow-border p-4 rounded-xl flex items-start space-x-4 bg-red-950/20">
          <ShieldAlert className="h-6 w-6 text-red-500 shrink-0 animate-pulse" />
          <div>
            <h4 className="text-sm font-bold text-red-400 font-mono">AEGISONE CORE SERVER OFFLINE</h4>
            <p className="text-xs text-red-200/70 mt-1">
              Ensure the backend is online and PostgreSQL migrations have been completed.
            </p>
          </div>
        </div>
      )}

      {/* Main Simulation Control Center */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Panel 1: Simulation Console Controls */}
        <div className="glass-panel p-5 rounded-xl flex flex-col justify-between space-y-4 lg:col-span-2">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <h3 className="text-xs font-bold font-mono tracking-widest text-zinc-400 uppercase flex items-center space-x-2">
                <Sliders className="h-4 w-4 text-red-500" />
                <span>Simulation Command Console</span>
              </h3>
              {/* Dynamic Status Indicator */}
              <span className={`text-[10px] font-bold font-mono px-2 py-0.5 rounded border ${
                simStatus === 'RUNNING' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 animate-pulse' :
                simStatus === 'PAUSED' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                'bg-zinc-800 text-zinc-500 border-zinc-700'
              }`}>
                SYSTEM STATE: {simStatus}
              </span>
            </div>

            {/* Simulated Clock and Event Counter */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono">
              <div className="bg-zinc-950/50 border border-zinc-900 p-3 rounded-lg flex items-center space-x-3">
                <Timer className="h-5 w-5 text-red-500 shrink-0" />
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase">Virtual System Clock</div>
                  <div className="text-xs font-bold text-zinc-200">{virtualTime}</div>
                </div>
              </div>
              
              <div className="bg-zinc-950/50 border border-zinc-900 p-3 rounded-lg flex items-center space-x-3">
                <Activity className="h-5 w-5 text-red-500 shrink-0" />
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase">Simulated Telemetry Logs</div>
                  <div className="text-sm font-bold text-zinc-200">{totalEvents}</div>
                </div>
              </div>

              <div className="bg-zinc-950/50 border border-zinc-900 p-3 rounded-lg flex items-center space-x-3">
                <Users className="h-5 w-5 text-red-500 shrink-0" />
                <div>
                  <div className="text-[10px] text-zinc-500 uppercase">Twin Active Nodes</div>
                  <div className="text-xs text-zinc-300">
                    <span className="font-bold text-white">{empCount}</span> EMP / <span className="font-bold text-white">{devCount}</span> DEV
                  </div>
                </div>
              </div>
            </div>

            {/* Core Action Buttons */}
            <div className="flex flex-wrap gap-3 pt-2">
              {simStatus === 'IDLE' || simStatus === 'STOPPED' ? (
                <button
                  onClick={() => handleSimAction('start')}
                  className="flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold font-mono text-xs px-4 py-2.5 rounded-lg transition-colors cursor-pointer"
                >
                  <Play className="h-4 w-4 fill-white" />
                  <span>START SIMULATOR</span>
                </button>
              ) : simStatus === 'RUNNING' ? (
                <button
                  onClick={() => handleSimAction('pause')}
                  className="flex items-center space-x-2 bg-amber-600 hover:bg-amber-500 text-white font-semibold font-mono text-xs px-4 py-2.5 rounded-lg transition-colors cursor-pointer"
                >
                  <Pause className="h-4 w-4 fill-white" />
                  <span>PAUSE SIMULATION</span>
                </button>
              ) : (
                <button
                  onClick={() => handleSimAction('resume')}
                  className="flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold font-mono text-xs px-4 py-2.5 rounded-lg transition-colors cursor-pointer"
                >
                  <Play className="h-4 w-4 fill-white" />
                  <span>RESUME SIMULATION</span>
                </button>
              )}

              {simStatus !== 'IDLE' && (
                <button
                  onClick={() => handleSimAction('stop')}
                  className="flex items-center space-x-2 bg-red-600 hover:bg-red-500 text-white font-semibold font-mono text-xs px-4 py-2.5 rounded-lg transition-colors cursor-pointer"
                >
                  <Square className="h-4 w-4 fill-white" />
                  <span>STOP ENGINE</span>
                </button>
              )}

              <button
                onClick={() => handleSimAction('reset')}
                className="flex items-center space-x-2 bg-zinc-950 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 font-mono text-xs px-4 py-2.5 rounded-lg transition-colors cursor-pointer ml-auto"
              >
                <RotateCcw className="h-4 w-4" />
                <span>RESET RANGE</span>
              </button>
            </div>
          </div>

          <div className="bg-zinc-950/20 border border-zinc-900 rounded-lg p-3 text-[11px] text-zinc-500 font-mono leading-relaxed">
            * Standard Operations: Employee actions occur deterministically based on shift configurations. Morning Shift (06-14h), Afternoon Shift (14-22h), and Night Shift (22-06h) are fully modeled to generate authentic traffic baselines.
          </div>
        </div>

        {/* Panel 2: Live Configuration Controls */}
        <div className="glass-panel p-5 rounded-xl space-y-4">
          <h3 className="text-xs font-bold font-mono tracking-widest text-zinc-400 uppercase border-b border-zinc-800 pb-3 flex items-center space-x-2">
            <Sliders className="h-4 w-4 text-red-500" />
            <span>Digital Twin Configuration</span>
          </h3>

          <form onSubmit={handleSaveConfig} className="space-y-3 font-mono text-xs">
            {/* Speed Multiplier */}
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-zinc-500">SPEED MULTIPLIER:</span>
                <span className="text-red-400 font-bold">{speedMultiplier}x</span>
              </div>
              <input
                type="range" min="1" max="120" step="5"
                value={speedMultiplier}
                onChange={(e) => setSpeedMultiplier(Number(e.target.value))}
                className="w-full accent-red-500 bg-zinc-900 cursor-pointer h-1.5 rounded-lg"
              />
              <div className="flex justify-between text-[9px] text-zinc-600">
                <span>1x (Realtime)</span>
                <span>60x (1s = 1m)</span>
                <span>120x (1s = 2m)</span>
              </div>
            </div>

            {/* Event Generation Rate */}
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-zinc-500">EVENT FREQUENCY:</span>
                <span className="text-red-400 font-bold">{eventRate} event/s</span>
              </div>
              <input
                type="range" min="0.5" max="10" step="0.5"
                value={eventRate}
                onChange={(e) => setEventRate(Number(e.target.value))}
                className="w-full accent-red-500 bg-zinc-900 cursor-pointer h-1.5 rounded-lg"
              />
            </div>

            {/* Employees target */}
            <div className="space-y-1 pt-1">
              <label className="text-zinc-500 block">SIMULATED EMPLOYEES:</label>
              <input
                type="number" min="5" max="100"
                value={targetEmployees}
                onChange={(e) => setTargetEmployees(Number(e.target.value))}
                className="w-full bg-zinc-900/60 border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-300 font-bold focus:outline-none focus:border-zinc-700"
              />
            </div>

            {/* Devices target */}
            <div className="space-y-1">
              <label className="text-zinc-500 block">SIMULATED DEVICES:</label>
              <input
                type="number" min="5" max="150"
                value={targetDevices}
                onChange={(e) => setTargetDevices(Number(e.target.value))}
                className="w-full bg-zinc-900/60 border border-zinc-800 rounded px-2.5 py-1.5 text-zinc-300 font-bold focus:outline-none focus:border-zinc-700"
              />
            </div>

            <button
              type="submit"
              disabled={configSaving}
              className="w-full mt-2 flex items-center justify-center space-x-2 bg-zinc-800 hover:bg-zinc-750 text-white font-semibold py-2 rounded-lg cursor-pointer transition-colors"
            >
              <Save className="h-4 w-4" />
              <span>{configSaving ? 'APPLYING...' : 'APPLY CONFIGURATION'}</span>
            </button>
          </form>
        </div>
      </div>

      {/* Summary lists of Twin Data */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 font-mono text-xs">
        
        {/* Card 1: Employees stats */}
        <div className="glass-panel p-5 rounded-xl space-y-3">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
            <span className="text-zinc-400 font-bold uppercase flex items-center space-x-1.5">
              <Users className="h-4 w-4 text-red-500" />
              <span>Simulated Shifts</span>
            </span>
            <span className="text-[10px] text-zinc-500">Shift Coverage</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between py-1 bg-zinc-900/20 px-2 rounded">
              <span className="text-zinc-500">Morning Shift (06-14h):</span>
              <span className="text-zinc-300 font-semibold">{Math.ceil(empCount/3)} EMP</span>
            </div>
            <div className="flex justify-between py-1 bg-zinc-900/20 px-2 rounded">
              <span className="text-zinc-500">Afternoon Shift (14-22h):</span>
              <span className="text-zinc-300 font-semibold">{Math.ceil(empCount/3)} EMP</span>
            </div>
            <div className="flex justify-between py-1 bg-zinc-900/20 px-2 rounded">
              <span className="text-zinc-500">Night Shift (22-06h):</span>
              <span className="text-zinc-300 font-semibold">{Math.floor(empCount/3)} EMP</span>
            </div>
          </div>
        </div>

        {/* Card 2: Devices specs */}
        <div className="glass-panel p-5 rounded-xl space-y-3">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
            <span className="text-zinc-400 font-bold uppercase flex items-center space-x-1.5">
              <Monitor className="h-4 w-4 text-red-500" />
              <span>Network Segments</span>
            </span>
            <span className="text-[10px] text-zinc-500">FW Routing zones</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between py-1 bg-zinc-900/20 px-2 rounded">
              <span className="text-zinc-500">OT-Control network:</span>
              <span className="text-zinc-300 font-semibold">{Math.ceil(devCount * 0.4)} NODES</span>
            </div>
            <div className="flex justify-between py-1 bg-zinc-900/20 px-2 rounded">
              <span className="text-zinc-500">OT-Field sensor zone:</span>
              <span className="text-zinc-300 font-semibold">{Math.ceil(devCount * 0.3)} NODES</span>
            </div>
            <div className="flex justify-between py-1 bg-zinc-900/20 px-2 rounded">
              <span className="text-zinc-500">Corporate Office zone:</span>
              <span className="text-zinc-300 font-semibold">{Math.floor(devCount * 0.3)} NODES</span>
            </div>
          </div>
        </div>

        {/* Card 3: Assets telemetry */}
        <div className="glass-panel p-5 rounded-xl space-y-3">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
            <span className="text-zinc-400 font-bold uppercase flex items-center space-x-1.5">
              <HardDrive className="h-4 w-4 text-red-500" />
              <span>Physical Systems</span>
            </span>
            <span className="text-[10px] text-zinc-500">Operational state</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between py-1 bg-zinc-900/20 px-2 rounded">
              <span className="text-zinc-500">Total Factory Assets:</span>
              <span className="text-zinc-300 font-semibold">{astCount} UNITS</span>
            </div>
            <div className="flex justify-between py-1 bg-zinc-900/20 px-2 rounded">
              <span className="text-zinc-500">Boilers / Valves:</span>
              <span className="text-emerald-500 font-bold">ONLINE</span>
            </div>
            <div className="flex justify-between py-1 bg-zinc-900/20 px-2 rounded">
              <span className="text-zinc-500">Line A / B PLC:</span>
              <span className="text-emerald-500 font-bold">MONITORED</span>
            </div>
          </div>
        </div>
      </div>

      {/* Two Columns for Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Column 1: Recent Critical Alerts */}
        <div className="glass-panel p-6 rounded-xl space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
            <h3 className="text-sm font-bold tracking-wider font-mono text-white flex items-center space-x-2">
              <ShieldAlert className="h-4 w-4 text-red-500" />
              <span>VIRTUAL SECURITY INCIDENTS</span>
            </h3>
            <span className="text-[10px] font-mono bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded">ALERTS</span>
          </div>

          <div className="space-y-3">
            {loading ? (
              <div className="text-zinc-500 font-mono text-xs">Loading logs...</div>
            ) : alerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-6 text-zinc-500 space-y-2">
                <ShieldCheck className="h-8 w-8 text-emerald-500/40" />
                <span className="font-mono text-xs">NO SECURITY BREACH EVENTS</span>
              </div>
            ) : (
              alerts.map(alert => (
                <div key={alert.id} className="p-3 bg-zinc-900/40 border border-zinc-800/80 rounded-lg flex items-start justify-between space-x-3">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className={`text-[9px] font-bold font-mono px-1.5 py-0.5 rounded ${
                        alert.severity === 'Critical' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                        alert.severity === 'High' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' :
                        'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                      }`}>
                        {alert.severity}
                      </span>
                      <h4 className="text-xs font-bold text-zinc-200">{alert.title}</h4>
                    </div>
                    <p className="text-[11px] text-zinc-400 font-sans leading-relaxed">{alert.description}</p>
                  </div>
                  <span className="text-[9px] text-zinc-500 font-mono shrink-0">
                    {new Date(alert.created_at).toLocaleTimeString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Column 2: Recent Industrial Events */}
        <div className="glass-panel p-6 rounded-xl space-y-4">
          <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
            <h3 className="text-sm font-bold tracking-wider font-mono text-white flex items-center space-x-2">
              <Activity className="h-4 w-4 text-emerald-500" />
              <span>SIMULATED TRANSACTION EVENT STREAM</span>
            </h3>
            <span className="text-[10px] font-mono bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded">EVENTS</span>
          </div>

          <div className="space-y-3">
            {loading ? (
              <div className="text-zinc-500 font-mono text-xs">Loading logs...</div>
            ) : events.length === 0 ? (
              <div className="text-zinc-500 font-mono text-xs py-6 text-center">No transactions generated. Start simulation.</div>
            ) : (
              events.map(event => (
                <div key={event.id} className="p-3 bg-zinc-900/40 border border-zinc-800/80 rounded-lg flex items-center justify-between font-mono text-xs">
                  <div className="flex items-center space-x-3">
                    <span className="text-emerald-500 font-bold bg-emerald-500/5 px-1.5 py-0.5 rounded text-[10px] border border-emerald-500/10">
                      {event.protocol}
                    </span>
                    <div>
                      <div className="text-zinc-300 font-sans font-semibold">{event.event_type}</div>
                      <div className="text-[10px] text-zinc-500">
                        {event.source_ip} &rarr; {event.destination_ip}
                      </div>
                    </div>
                  </div>
                  <span className={`text-[10px] font-bold ${
                    event.severity === 'Critical' ? 'text-red-500' :
                    event.severity === 'Warning' ? 'text-amber-500' : 'text-zinc-400'
                  }`}>
                    {event.severity}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
