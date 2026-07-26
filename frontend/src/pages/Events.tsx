import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import type { Event } from '../types';
import { Terminal, RefreshCw, FileText } from 'lucide-react';
import { useHealth } from '../context/HealthContext';

export const Events: React.FC = () => {
  const { backendConnected, dbConnected } = useHealth();
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEvents = async () => {
    if (!backendConnected || !dbConnected) return;
    setLoading(true);
    try {
      const response = await apiClient.get<Event[]>('/events');
      setEvents(response.data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch protocol events stream.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [backendConnected, dbConnected]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-wide text-white">BEHAVIORAL NETWORK EVENTS</h2>
          <p className="text-xs text-zinc-400 font-mono">Modbus, OPC-UA, S7comm, and EtherNet/IP protocol log stream</p>
        </div>
        <button
          onClick={fetchEvents}
          className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>RE-POLL EVENT HUB</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/20 border border-red-500/30 text-red-400 rounded-lg font-mono text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-zinc-500 font-mono text-xs">Awaiting event pipeline payload...</div>
      ) : events.length === 0 ? (
        <div className="text-zinc-400 font-mono text-xs py-10 text-center glass-panel rounded-xl">
          No events recorded in database.
        </div>
      ) : (
        <div className="glass-panel rounded-xl overflow-hidden border border-zinc-800">
          <div className="bg-zinc-950/60 px-5 py-3 border-b border-zinc-800 flex items-center justify-between">
            <div className="flex items-center space-x-2 font-mono text-xs text-zinc-400">
              <Terminal className="h-4 w-4 text-emerald-500" />
              <span>SOC MONITOR PORT: /dev/aegis_firewall</span>
            </div>
            <span className="text-[10px] text-zinc-500 font-mono">{events.length} logs captured</span>
          </div>

          <div className="divide-y divide-zinc-800/60 overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-zinc-900/40 text-zinc-400 uppercase tracking-wider text-[10px] select-none">
                <tr>
                  <th className="px-5 py-3 font-semibold">Timestamp</th>
                  <th className="px-5 py-3 font-semibold">Protocol</th>
                  <th className="px-5 py-3 font-semibold">Severity</th>
                  <th className="px-5 py-3 font-semibold">Source IP</th>
                  <th className="px-5 py-3 font-semibold">Destination IP</th>
                  <th className="px-5 py-3 font-semibold">Transaction Operation</th>
                  <th className="px-5 py-3 font-semibold">Payload Frame</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/40 text-zinc-300">
                {events.map((event) => (
                  <tr key={event.id} className="hover:bg-zinc-900/30 transition-colors">
                    <td className="px-5 py-3.5 whitespace-nowrap text-zinc-500 text-[11px]">
                      {new Date(event.timestamp).toLocaleString()}
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                        event.protocol === 'Modbus/TCP' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' :
                        event.protocol === 'S7Comm' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' :
                        event.protocol === 'OPC-UA' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                        'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                      }`}>
                        {event.protocol}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      <span className={`font-bold ${
                        event.severity === 'Critical' ? 'text-red-500' :
                        event.severity === 'Warning' ? 'text-amber-500' : 'text-zinc-500'
                      }`}>
                        {event.severity.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap font-semibold text-zinc-200">
                      {event.source_ip}
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap text-zinc-400">
                      {event.destination_ip}
                    </td>
                    <td className="px-5 py-3.5 whitespace-nowrap text-zinc-200 font-sans font-medium">
                      {event.event_type}
                    </td>
                    <td className="px-5 py-3.5 max-w-xs truncate text-[11px] text-zinc-500">
                      <div className="flex items-center space-x-1 font-mono hover:text-zinc-300 cursor-pointer" title={event.payload_summary}>
                        <FileText className="h-3 w-3 shrink-0" />
                        <span className="truncate">{event.payload_summary || 'N/A'}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
