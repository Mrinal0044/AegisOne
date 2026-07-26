import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import type { Device } from '../types';
import { Monitor, ShieldAlert, CheckCircle, HelpCircle, RefreshCw } from 'lucide-react';
import { useHealth } from '../context/HealthContext';

export const Devices: React.FC = () => {
  const { backendConnected, dbConnected } = useHealth();
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDevices = async () => {
    if (!backendConnected || !dbConnected) return;
    setLoading(true);
    try {
      const response = await apiClient.get<Device[]>('/devices');
      setDevices(response.data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch devices data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, [backendConnected, dbConnected]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-wide text-white">DEVICES & HOSTS</h2>
          <p className="text-xs text-zinc-400 font-mono">Workstations, engineering consoles, and hardware interfaces</p>
        </div>
        <button
          onClick={fetchDevices}
          className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>RESCAN HOSTS</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/20 border border-red-500/30 text-red-400 rounded-lg font-mono text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-zinc-500 font-mono text-xs">Querying hosts list...</div>
      ) : devices.length === 0 ? (
        <div className="text-zinc-400 font-mono text-xs py-10 text-center glass-panel rounded-xl">
          No devices registered in the network logs.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {devices.map((device) => (
            <div
              key={device.id}
              className={`glass-panel p-5 rounded-xl space-y-4 flex flex-col justify-between border transition-all duration-300 ${
                device.status === 'Authorized' ? 'border-emerald-500/20 hover:border-emerald-500/40' :
                device.status === 'Quarantined' ? 'border-red-500/40 hover:border-red-500/60 bg-red-950/5 shadow-[0_0_15px_rgba(239,68,68,0.05)]' :
                'border-yellow-500/20 hover:border-yellow-500/40'
              }`}
            >
              {/* Header: Status & Icon */}
              <div className="flex items-start justify-between">
                <div className="bg-zinc-800 p-2.5 rounded-lg text-zinc-300">
                  <Monitor className="h-5 w-5" />
                </div>
                
                {/* Authorization Status Badge */}
                <div className="flex items-center space-x-1 font-mono text-[10px] font-bold">
                  {device.status === 'Authorized' && (
                    <span className="flex items-center space-x-1 bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20">
                      <CheckCircle className="h-3 w-3" />
                      <span>AUTHORIZED</span>
                    </span>
                  )}
                  {device.status === 'Quarantined' && (
                    <span className="flex items-center space-x-1 bg-red-500/15 text-red-400 px-2 py-0.5 rounded border border-red-500/30 animate-pulse-slow">
                      <ShieldAlert className="h-3 w-3" />
                      <span>QUARANTINED</span>
                    </span>
                  )}
                  {device.status === 'Unknown' && (
                    <span className="flex items-center space-x-1 bg-yellow-500/10 text-yellow-400 px-2 py-0.5 rounded border border-yellow-500/20">
                      <HelpCircle className="h-3 w-3" />
                      <span>UNKNOWN</span>
                    </span>
                  )}
                </div>
              </div>

              {/* Hostname & OS */}
              <div className="space-y-1">
                <h3 className="font-mono text-sm font-bold text-zinc-200 truncate">{device.hostname}</h3>
                <p className="text-xs text-zinc-500 font-sans">{device.device_type} &bull; {device.os_version}</p>
              </div>

              {/* Stats */}
              <div className="border-t border-zinc-800/80 pt-3 mt-1 space-y-2 font-mono text-xs">
                <div className="flex justify-between">
                  <span className="text-zinc-500">IP ADDRESS:</span>
                  <span className="text-zinc-300 font-semibold">{device.ip_address}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">MAC ADDRESS:</span>
                  <span className="text-zinc-400">{device.mac_address}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">LAST SEEN:</span>
                  <span className="text-zinc-400 text-[10px]">
                    {new Date(device.last_seen).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
