import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Cpu,
  Monitor,
  Activity,
  AlertTriangle,
  TrendingUp,
  Users,
  BookOpen,
  Database,
  Brain,
  Flame,
  Settings
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const menuItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Industrial Assets', path: '/assets', icon: Cpu },
    { name: 'Devices & Hosts', path: '/devices', icon: Monitor },
    { name: 'Behavioral Events', path: '/events', icon: Activity },
    { name: 'Threat Alerts', path: '/alerts', icon: AlertTriangle },
    { name: 'Risk Analytics', path: '/risk-scores', icon: TrendingUp },
    { name: 'Users & Operators', path: '/users', icon: Users },
    { name: 'Behavior Profiles', path: '/behavior-profiles', icon: BookOpen },
    { name: 'Feature Store', path: '/features', icon: Database },
    { name: 'Detection Engine', path: '/detection-engine', icon: Brain },
    { name: 'Threat Simulation', path: '/threat-simulation', icon: Flame },
    { name: 'System Operations', path: '/operations', icon: Settings },
  ];

  return (
    <aside className="w-64 glass-panel border-r border-[rgba(255,255,255,0.08)] flex flex-col justify-between h-full">
      <div className="flex-1 py-6 px-4 space-y-1.5">
        <div className="text-[10px] text-zinc-500 font-mono tracking-widest font-bold px-3 mb-4 uppercase">
          Navigation
        </div>
        <nav className="space-y-1">
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group font-sans font-medium ${
                  isActive
                    ? 'bg-red-500/10 border-l-2 border-red-500 text-white shadow-[0_0_10px_rgba(239,68,68,0.05)]'
                    : 'text-zinc-400 border-l-2 border-transparent hover:bg-zinc-800/40 hover:text-zinc-200'
                }`
              }
            >
              <item.icon className="h-4.5 w-4.5 transition-transform duration-200 group-hover:scale-105" />
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Sidebar Footer Details */}
      <div className="p-4 border-t border-[rgba(255,255,255,0.06)] bg-zinc-950/20 font-mono text-[10px] text-zinc-500 space-y-1">
        <div>CORE MODULE: v1.0.0</div>
        <div>OT CLIENT ID: AEGIS_SOC_01</div>
        <div>STATION IP: 192.168.10.100</div>
      </div>
    </aside>
  );
};
