import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { RefreshCw, Play, ShieldAlert, Cpu, Monitor, Users, Layers, CalendarRange } from 'lucide-react';
import { useHealth } from '../context/HealthContext';

type WindowSize = '5m' | '15m' | '1h' | '24h' | '7d';
type FeatureTab = 'users' | 'devices' | 'assets' | 'departments';

export const FeatureStore: React.FC = () => {
  const { backendConnected, dbConnected } = useHealth();
  const [selectedWindow, setSelectedWindow] = useState<WindowSize>('1h');
  const [activeTab, setActiveTab] = useState<FeatureTab>('users');
  const [loading, setLoading] = useState<boolean>(true);
  const [rebuilding, setRebuilding] = useState<boolean>(false);
  const [statistics, setStatistics] = useState<any>(null);
  
  // Data vectors
  const [userFeatures, setUserFeatures] = useState<any[]>([]);
  const [deviceFeatures, setDeviceFeatures] = useState<any[]>([]);
  const [assetFeatures, setAssetFeatures] = useState<any[]>([]);
  const [deptFeatures, setDeptFeatures] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      const res = await apiClient.get('/behavior/statistics');
      setStatistics(res.data);
    } catch (err) {
      console.error('Failed to load stats', err);
    }
  };

  const fetchFeaturesData = async () => {
    if (!backendConnected || !dbConnected) return;
    setLoading(true);
    setError(null);
    try {
      const url = `/behavior/features/${activeTab}?window=${selectedWindow}`;
      const res = await apiClient.get<any[]>(url);
      
      if (activeTab === 'users') setUserFeatures(res.data);
      else if (activeTab === 'devices') setDeviceFeatures(res.data);
      else if (activeTab === 'assets') setAssetFeatures(res.data);
      else if (activeTab === 'departments') setDeptFeatures(res.data);
    } catch (err: any) {
      console.error(err);
      setError(`Failed to retrieve behavioral vectors for tab: ${activeTab}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRebuild = async () => {
    setRebuilding(true);
    try {
      await apiClient.post('/behavior/rebuild');
      // Briefly wait and reload
      setTimeout(() => {
        fetchFeaturesData();
        fetchStats();
        setRebuilding(false);
      }, 1500);
    } catch (err) {
      console.error('Rebuild failed', err);
      setRebuilding(false);
    }
  };

  useEffect(() => {
    fetchFeaturesData();
  }, [activeTab, selectedWindow, backendConnected, dbConnected]);

  useEffect(() => {
    fetchStats();
  }, [backendConnected, dbConnected]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-zinc-800 pb-4 gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-wide text-white">BEHAVIORAL FEATURE STORE</h2>
          <p className="text-xs text-zinc-400 font-mono">Structured ML-ready feature vectors engineered incrementally from raw events</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleRebuild}
            disabled={rebuilding}
            className="flex items-center space-x-2 bg-emerald-950/40 hover:bg-emerald-900/60 border border-emerald-500/30 text-emerald-400 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors disabled:opacity-50"
          >
            <Play className={`h-3.5 w-3.5 ${rebuilding ? 'animate-spin' : ''}`} />
            <span>{rebuilding ? 'REBUILDING...' : 'REBUILD STORE'}</span>
          </button>
          <button
            onClick={() => { fetchFeaturesData(); fetchStats(); }}
            className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>SYNC</span>
          </button>
        </div>
      </div>

      {/* Stats Summary Widgets */}
      {statistics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-4">
          <div className="glass-panel p-3.5 rounded-xl border border-zinc-800/80">
            <div className="text-[10px] text-zinc-500 font-mono uppercase">User Vectors</div>
            <div className="text-xl font-bold text-white mt-0.5">{statistics.user_features_count}</div>
          </div>
          <div className="glass-panel p-3.5 rounded-xl border border-zinc-800/80">
            <div className="text-[10px] text-zinc-500 font-mono uppercase">Device Vectors</div>
            <div className="text-xl font-bold text-white mt-0.5">{statistics.device_features_count}</div>
          </div>
          <div className="glass-panel p-3.5 rounded-xl border border-zinc-800/80">
            <div className="text-[10px] text-zinc-500 font-mono uppercase">Asset Vectors</div>
            <div className="text-xl font-bold text-white mt-0.5">{statistics.asset_features_count}</div>
          </div>
          <div className="glass-panel p-3.5 rounded-xl border border-zinc-800/80">
            <div className="text-[10px] text-zinc-500 font-mono uppercase">Dept Vectors</div>
            <div className="text-xl font-bold text-white mt-0.5">{statistics.department_features_count}</div>
          </div>
          <div className="glass-panel p-3.5 rounded-xl border border-zinc-800/80 col-span-2 sm:col-span-1">
            <div className="text-[10px] text-zinc-500 font-mono uppercase">Snapshot Logs</div>
            <div className="text-xl font-bold text-zinc-400 mt-0.5">{statistics.snapshots_count}</div>
          </div>
        </div>
      )}

      {/* Filter and Tab Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center bg-zinc-950/60 border border-zinc-800/80 rounded-xl p-3 gap-3">
        {/* Entity Tabs */}
        <div className="flex space-x-1.5 bg-zinc-900/60 p-1 rounded-lg border border-zinc-800/40 w-full sm:w-auto">
          <button
            onClick={() => setActiveTab('users')}
            className={`flex-1 sm:flex-none flex items-center justify-center space-x-2 px-3 py-1.5 rounded-md text-xs font-mono transition-all ${
              activeTab === 'users' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Users className="h-3.5 w-3.5" />
            <span>USERS</span>
          </button>
          <button
            onClick={() => setActiveTab('devices')}
            className={`flex-1 sm:flex-none flex items-center justify-center space-x-2 px-3 py-1.5 rounded-md text-xs font-mono transition-all ${
              activeTab === 'devices' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Monitor className="h-3.5 w-3.5" />
            <span>DEVICES</span>
          </button>
          <button
            onClick={() => setActiveTab('assets')}
            className={`flex-1 sm:flex-none flex items-center justify-center space-x-2 px-3 py-1.5 rounded-md text-xs font-mono transition-all ${
              activeTab === 'assets' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Cpu className="h-3.5 w-3.5" />
            <span>ASSETS</span>
          </button>
          <button
            onClick={() => setActiveTab('departments')}
            className={`flex-1 sm:flex-none flex items-center justify-center space-x-2 px-3 py-1.5 rounded-md text-xs font-mono transition-all ${
              activeTab === 'departments' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>DEPTS</span>
          </button>
        </div>

        {/* Window Selector */}
        <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
          <CalendarRange className="h-4 w-4 text-zinc-500" />
          <span className="text-xs font-mono text-zinc-500 uppercase">Window:</span>
          <div className="flex bg-zinc-900 border border-zinc-850 rounded-lg p-0.5 font-mono text-[11px]">
            {(['5m', '15m', '1h', '24h', '7d'] as WindowSize[]).map((w) => (
              <button
                key={w}
                onClick={() => setSelectedWindow(w)}
                className={`px-2 py-1 rounded transition-colors ${
                  selectedWindow === w ? 'bg-zinc-800 text-emerald-400 font-bold' : 'text-zinc-400 hover:text-zinc-200'
                }`}
              >
                {w}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-950/20 border border-red-500/30 text-red-400 rounded-lg font-mono text-xs flex items-center space-x-2">
          <ShieldAlert className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Feature Data Grid */}
      <div className="glass-panel rounded-xl overflow-hidden border border-zinc-800/80">
        {loading ? (
          <div className="p-8 text-zinc-500 font-mono text-xs text-center animate-pulse">
            Fetching feature coefficients directory...
          </div>
        ) : activeTab === 'users' ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="bg-zinc-900/60 border-b border-zinc-850 text-zinc-400 text-[10px] uppercase tracking-wider">
                  <th className="p-4">User Identity</th>
                  <th className="p-4">Department</th>
                  <th className="p-4 text-right">Avg Session</th>
                  <th className="p-4 text-right">Failed Logins</th>
                  <th className="p-4 text-right">Devices</th>
                  <th className="p-4 text-right">Assets</th>
                  <th className="p-4 text-right">Cmds/Hr</th>
                  <th className="p-4 text-right">Night %</th>
                  <th className="p-4 text-right">USB Count</th>
                  <th className="p-4 text-right">Downloads</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900">
                {userFeatures.map((row) => (
                  <tr key={row.id} className="hover:bg-zinc-900/40 text-zinc-300">
                    <td className="p-4">
                      <div className="font-semibold text-zinc-200">{row.user?.full_name || 'System Account'}</div>
                      <div className="text-[10px] text-zinc-500">@{row.user?.username || 'system'} • {row.user?.role}</div>
                    </td>
                    <td className="p-4 text-zinc-400">{row.user?.department?.name || 'N/A'}</td>
                    <td className="p-4 text-right">{(row.avg_session_duration / 60).toFixed(1)}m</td>
                    <td className={`p-4 text-right font-bold ${row.failed_login_count > 0 ? 'text-red-400' : 'text-zinc-500'}`}>
                      {row.failed_login_count}
                    </td>
                    <td className="p-4 text-right text-zinc-200 font-semibold">{row.unique_devices_count}</td>
                    <td className="p-4 text-right text-zinc-200 font-semibold">{row.unique_assets_count}</td>
                    <td className="p-4 text-right text-emerald-400">{row.commands_per_hour.toFixed(1)}</td>
                    <td className="p-4 text-right">{(row.night_activity_ratio * 100).toFixed(0)}%</td>
                    <td className={`p-4 text-right ${row.usb_usage_count > 0 ? 'text-yellow-500 font-bold' : ''}`}>
                      {row.usb_usage_count}
                    </td>
                    <td className="p-4 text-right">{row.download_frequency.toFixed(1)}</td>
                  </tr>
                ))}
                {userFeatures.length === 0 && (
                  <tr>
                    <td colSpan={10} className="p-8 text-center text-zinc-500">No user behavior profiles recorded in this window.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ) : activeTab === 'devices' ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="bg-zinc-900/60 border-b border-zinc-850 text-zinc-400 text-[10px] uppercase tracking-wider">
                  <th className="p-4">Terminal Device</th>
                  <th className="p-4 text-right">Active Hours</th>
                  <th className="p-4 text-right">Users Connected</th>
                  <th className="p-4 text-right">Avg Payload Size</th>
                  <th className="p-4 text-right">Config Changes</th>
                  <th className="p-4 text-right">Firmware Updates</th>
                  <th className="p-4 text-right">Maint. Freq/Hr</th>
                  <th className="p-4 text-right">Unexpected Downtime</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900">
                {deviceFeatures.map((row) => (
                  <tr key={row.id} className="hover:bg-zinc-900/40 text-zinc-300">
                    <td className="p-4">
                      <div className="font-semibold text-zinc-200">{row.device?.hostname || 'Unknown Host'}</div>
                      <div className="text-[10px] text-zinc-500">{row.device?.ip_address} • {row.device?.device_type}</div>
                    </td>
                    <td className="p-4 text-right">{row.active_hours.toFixed(2)}h</td>
                    <td className="p-4 text-right text-zinc-200 font-semibold">{row.connected_users_count}</td>
                    <td className="p-4 text-right text-zinc-400">{row.avg_network_traffic_bytes.toFixed(0)} B</td>
                    <td className="p-4 text-right">{row.config_change_count}</td>
                    <td className="p-4 text-right">{row.firmware_change_count}</td>
                    <td className="p-4 text-right text-emerald-400">{row.maintenance_frequency.toFixed(2)}</td>
                    <td className={`p-4 text-right ${row.unexpected_downtime_count > 0 ? 'text-red-400 font-bold' : 'text-zinc-500'}`}>
                      {row.unexpected_downtime_count}
                    </td>
                  </tr>
                ))}
                {deviceFeatures.length === 0 && (
                  <tr>
                    <td colSpan={8} className="p-8 text-center text-zinc-500">No device logs registered.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ) : activeTab === 'assets' ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="bg-zinc-900/60 border-b border-zinc-850 text-zinc-400 text-[10px] uppercase tracking-wider">
                  <th className="p-4">Industrial OT Asset</th>
                  <th className="p-4 text-right">Access Rate/Hr</th>
                  <th className="p-4 text-right">Unique Operators</th>
                  <th className="p-4 text-right">Avg Commands/Event</th>
                  <th className="p-4 text-right">Alarm Acks</th>
                  <th className="p-4 text-right">Maintenance Count</th>
                  <th className="p-4 text-right">Operational Hours</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900">
                {assetFeatures.map((row) => (
                  <tr key={row.id} className="hover:bg-zinc-900/40 text-zinc-300">
                    <td className="p-4">
                      <div className="font-semibold text-zinc-200">{row.asset?.name || 'Unknown Asset'}</div>
                      <div className="text-[10px] text-zinc-500">{row.asset?.vendor} {row.asset?.model} • {row.asset?.asset_type}</div>
                    </td>
                    <td className="p-4 text-right text-emerald-400">{row.access_frequency.toFixed(2)}</td>
                    <td className="p-4 text-right text-zinc-200 font-semibold">{row.unique_operators_count}</td>
                    <td className="p-4 text-right">{row.avg_commands_count.toFixed(2)}</td>
                    <td className="p-4 text-right">{row.alarm_acknowledgements_count}</td>
                    <td className="p-4 text-right text-yellow-500 font-medium">{row.maintenance_events_count}</td>
                    <td className="p-4 text-right">{row.operational_hours.toFixed(2)}h</td>
                  </tr>
                ))}
                {assetFeatures.length === 0 && (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-zinc-500">No assets monitored in database.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="bg-zinc-900/60 border-b border-zinc-850 text-zinc-400 text-[10px] uppercase tracking-wider">
                  <th className="p-4">Department Scope</th>
                  <th className="p-4 text-right">Peak Event Rate/Hr</th>
                  <th className="p-4 text-right">Avg Active Users</th>
                  <th className="p-4 text-right">Assets Accessed</th>
                  <th className="p-4 text-right">Avg Network Payload</th>
                  <th className="p-4 text-right">Typical Hours Ratio</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900">
                {deptFeatures.map((row) => (
                  <tr key={row.id} className="hover:bg-zinc-900/40 text-zinc-300">
                    <td className="p-4">
                      <div className="font-semibold text-zinc-200">{row.department?.name || 'Unknown Department'}</div>
                      <div className="text-[10px] text-zinc-500">Code: {row.department?.code}</div>
                    </td>
                    <td className="p-4 text-right text-emerald-400">{row.peak_activity_rate.toFixed(2)}</td>
                    <td className="p-4 text-right text-zinc-200 font-semibold">{row.avg_users_online.toFixed(1)}</td>
                    <td className="p-4 text-right text-zinc-200 font-semibold">{row.unique_assets_accessed_count}</td>
                    <td className="p-4 text-right text-zinc-400">{row.avg_network_usage.toFixed(0)} B</td>
                    <td className="p-4 text-right">{(row.typical_working_hours_ratio * 100).toFixed(0)}%</td>
                  </tr>
                ))}
                {deptFeatures.length === 0 && (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-zinc-500">No department statistics available.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
