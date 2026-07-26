import React from 'react';
import { useHealth } from '../context/HealthContext';

export const StatusBar: React.FC = () => {
  const { backendConnected } = useHealth();

  return (
    <footer className="glass-panel border-t border-[rgba(255,255,255,0.08)] px-6 py-2 flex items-center justify-between font-mono text-[11px] text-zinc-400 z-10 select-none">
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse-slow"></span>
          <span>SECURE NETWORK MONITORING ACTIVE</span>
        </div>
        <div className="hidden md:flex items-center space-x-4 border-l border-zinc-800 pl-6">
          <span>PROTOCOLS: </span>
          <span className="text-zinc-500"><span className="text-emerald-500 font-bold">MODBUS</span></span>
          <span className="text-zinc-500"><span className="text-emerald-500 font-bold">S7COMM</span></span>
          <span className="text-zinc-500"><span className="text-emerald-500 font-bold">OPC-UA</span></span>
          <span className="text-zinc-500"><span className="text-emerald-500 font-bold">ETHERNET/IP</span></span>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <span>GATEWAY: <span className="text-zinc-300 font-bold">192.168.10.1</span></span>
        <span>ENVIRONMENT: <span className="text-emerald-500 font-bold uppercase">DEVELOPMENT</span></span>
        <span>SECURE HANDSHAKE: {backendConnected ? (
          <span className="text-emerald-500 font-bold">VALID</span>
        ) : (
          <span className="text-red-500 font-bold">FAILED</span>
        )}</span>
      </div>
    </footer>
  );
};
