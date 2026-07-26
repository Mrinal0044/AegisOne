import React, { useState, useEffect } from 'react';
import { Shield, Clock, Wifi, WifiOff, Database } from 'lucide-react';
import { useHealth } from '../context/HealthContext';

export const Header: React.FC = () => {
  const { backendConnected, dbConnected } = useHealth();
  const [time, setTime] = useState<string>(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="glass-panel border-b border-[rgba(255,255,255,0.08)] px-6 py-4 flex items-center justify-between z-10">
      {/* Brand Logo & Title */}
      <div className="flex items-center space-x-3">
        <div className="bg-red-500/10 border border-red-500/30 p-2 rounded-lg text-red-500 shadow-[0_0_15px_rgba(239,68,68,0.15)] animate-pulse-slow">
          <Shield className="h-6 w-6" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold tracking-wider font-sans bg-clip-text text-transparent bg-gradient-to-r from-white via-zinc-200 to-zinc-400">
              AEGIS<span className="text-red-500">ONE</span>
            </h1>
            <span className="text-[10px] bg-red-500/10 text-red-400 border border-red-500/20 px-1.5 py-0.5 rounded font-mono font-bold tracking-widest">
              OT/ICS
            </span>
          </div>
          <p className="text-[11px] text-zinc-400 tracking-wider font-mono">
            INDUSTRIAL BEHAVIORAL INTELLIGENCE PLATFORM
          </p>
        </div>
      </div>

      {/* Clock and Live Status Panel */}
      <div className="flex items-center space-x-6">
        {/* System Time */}
        <div className="flex items-center space-x-2 bg-zinc-900/60 border border-zinc-800/80 px-3 py-1.5 rounded-lg text-zinc-300 font-mono text-sm">
          <Clock className="h-4 w-4 text-zinc-400" />
          <span>{time}</span>
        </div>

        {/* API Connection Indicator */}
        <div className="flex items-center space-x-4 font-mono text-xs">
          <div className="flex items-center space-x-2 bg-zinc-900/60 border border-zinc-800/80 px-3 py-1.5 rounded-lg">
            {backendConnected ? (
              <>
                <Wifi className="h-4 w-4 text-emerald-500" />
                <span className="text-zinc-300">CORE API: </span>
                <span className="text-emerald-500 font-bold">ONLINE</span>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-red-500 animate-pulse" />
                <span className="text-zinc-300">CORE API: </span>
                <span className="text-red-500 font-bold animate-pulse">OFFLINE</span>
              </>
            )}
          </div>

          {/* Database Connection Indicator */}
          <div className="flex items-center space-x-2 bg-zinc-900/60 border border-zinc-800/80 px-3 py-1.5 rounded-lg">
            <Database className="h-4 w-4 id-db-icon" />
            <span className="text-zinc-300">OT_DB: </span>
            {dbConnected ? (
              <span className="text-emerald-500 font-bold">CONNECTED</span>
            ) : (
              <span className="text-red-500 font-bold animate-pulse">DISCONNECTED</span>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
