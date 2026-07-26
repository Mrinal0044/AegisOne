import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import type { BehaviorProfile } from '../types';
import { ShieldCheck, RefreshCw, BookOpen, Clock, Activity, Monitor } from 'lucide-react';
import { useHealth } from '../context/HealthContext';

export const BehaviorProfiles: React.FC = () => {
  const { backendConnected, dbConnected } = useHealth();
  const [profiles, setProfiles] = useState<BehaviorProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfiles = async () => {
    if (!backendConnected || !dbConnected) return;
    setLoading(true);
    try {
      const response = await apiClient.get<BehaviorProfile[]>('/behavior-profiles');
      setProfiles(response.data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch normal behavioral baselines directory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfiles();
  }, [backendConnected, dbConnected]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-wide text-white">NORMAL BEHAVIOR PROFILES</h2>
          <p className="text-xs text-zinc-400 font-mono">baseline signatures of normal operations for learning anomaly distributions</p>
        </div>
        <button
          onClick={fetchProfiles}
          className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>RELOAD BASES</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/20 border border-red-500/30 text-red-400 rounded-lg font-mono text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-zinc-500 font-mono text-xs">Loading baseline behavior registry...</div>
      ) : profiles.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 glass-panel rounded-xl space-y-3">
          <BookOpen className="h-12 w-12 text-zinc-600 animate-pulse-slow" />
          <div className="text-center">
            <h4 className="text-sm font-bold text-zinc-300 font-mono">NO BEHAVIOR BASES FOUND</h4>
            <p className="text-xs text-zinc-500 mt-1">Start the simulation engine to generate Twin employees and their behavior signatures.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {profiles.map((profile) => (
            <div key={profile.id} className="glass-panel p-5 rounded-xl space-y-4 relative border border-emerald-500/10">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="bg-emerald-950/40 text-emerald-400 p-2 rounded-lg border border-emerald-500/20">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-zinc-200 font-sans tracking-wide text-sm">
                      {profile.name}
                    </h3>
                    <span className="text-[10px] text-zinc-500 font-mono uppercase">
                      TYPE: {profile.entity_type}
                    </span>
                  </div>
                </div>
                
                <span className="text-[9px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 px-2 py-0.5 rounded font-mono font-bold tracking-wider">
                  LEARNED BASELINE
                </span>
              </div>

              {/* Timing specifications */}
              <div className="grid grid-cols-3 gap-3 bg-zinc-950/30 border border-zinc-900/60 p-3 rounded-lg font-mono text-xs">
                <div>
                  <div className="text-zinc-500 text-[9px] uppercase flex items-center space-x-1">
                    <Clock className="h-3 w-3" />
                    <span>Working Shift</span>
                  </div>
                  <div className="text-zinc-300 font-semibold mt-0.5">{profile.working_schedule.shift || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-zinc-500 text-[9px] uppercase flex items-center space-x-1">
                    <Clock className="h-3 w-3" />
                    <span>Start / End</span>
                  </div>
                  <div className="text-zinc-300 mt-0.5">{profile.login_time} - {profile.logout_time}</div>
                </div>
                <div>
                  <div className="text-zinc-500 text-[9px] uppercase flex items-center space-x-1">
                    <Activity className="h-3 w-3" />
                    <span>Avg Vol</span>
                  </div>
                  <div className="text-zinc-300 mt-0.5">{profile.avg_event_volume} events/d</div>
                </div>
              </div>

              {/* Behavior Lists */}
              <div className="space-y-3 font-mono text-xs">
                {/* Normal Devices */}
                <div className="space-y-1">
                  <div className="text-zinc-500 text-[10px] uppercase flex items-center space-x-1">
                    <Monitor className="h-3.5 w-3.5 text-zinc-600" />
                    <span>Normal Access Terminals:</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 pl-1">
                    {profile.normal_devices.hostnames?.map((d: string) => (
                      <span key={d} className="bg-zinc-900 border border-zinc-800 text-zinc-300 px-2 py-0.5 rounded text-[10px]">
                        {d}
                      </span>
                    )) || <span className="text-zinc-550">None</span>}
                  </div>
                </div>

                {/* Normal Apps */}
                <div className="space-y-1">
                  <div className="text-zinc-500 text-[10px] uppercase">Normal Applications:</div>
                  <div className="flex flex-wrap gap-1.5 pl-1">
                    {profile.typical_apps.apps?.map((a: string) => (
                      <span key={a} className="bg-zinc-900 border border-zinc-800 text-zinc-400 px-2 py-0.5 rounded text-[10px]">
                        {a}
                      </span>
                    )) || <span className="text-zinc-550">None</span>}
                  </div>
                </div>

                {/* Command actions */}
                <div className="space-y-1">
                  <div className="text-zinc-500 text-[10px] uppercase">Allowed Commands Baseline:</div>
                  <div className="flex flex-wrap gap-1.5 pl-1">
                    {profile.command_patterns.actions?.map((cmd: string) => (
                      <span key={cmd} className="bg-zinc-900 border border-zinc-800 text-emerald-400 px-2 py-0.5 rounded text-[10px]">
                        {cmd}
                      </span>
                    )) || <span className="text-zinc-550">None</span>}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
