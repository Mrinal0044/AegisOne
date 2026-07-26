import React, { useState } from 'react';
import { Shield, Cpu, Monitor, Users, Info, Activity } from 'lucide-react';

interface TopologyNode {
  id: string;
  name: string;
  type: 'User' | 'Device' | 'IndustrialAsset';
  ip?: string;
  role?: string;
  criticality?: string;
  riskScore: number;
  status: string;
  x: number;
  y: number;
}

interface TopologyLink {
  from: string;
  to: string;
  active: boolean;
}

interface NetworkTopologyProps {
  entities: {
    users: any[];
    devices: any[];
    assets: any[];
  };
  riskMap: Record<string, number>;
}

export const NetworkTopology: React.FC<NetworkTopologyProps> = ({ entities, riskMap }) => {
  const [selectedNode, setSelectedNode] = useState<TopologyNode | null>(null);

  // Position nodes systematically on a 800x450 grid
  const nodes: TopologyNode[] = [];
  const links: TopologyLink[] = [];

  // Group 1: SCADA Server & Gateway (Utilities Zone - Center)
  nodes.push({
    id: 'center-gateway',
    name: 'Security Gateway Cisco ISA3000',
    type: 'IndustrialAsset',
    ip: '192.168.10.1',
    criticality: 'Critical',
    riskScore: riskMap['IndustrialAsset_0760a062-ca41-4cdd-8dda-3a3301eb2ffe'] || 0,
    status: 'Operational',
    x: 400,
    y: 220
  });

  // Group 2: Engineering Workstations (ENG Zone - Left)
  nodes.push({
    id: 'eng-ws',
    name: 'Engineering Workstation 01',
    type: 'Device',
    ip: '192.168.10.120',
    criticality: 'Critical',
    riskScore: riskMap['Device_ae08cce8-6f35-4a46-9bbd-54b34de3e1a0'] || 0,
    status: 'Authorized',
    x: 200,
    y: 150
  });

  // Group 3: PLCs (Control Zone - Right)
  nodes.push({
    id: 'turbine-plc',
    name: 'Turbine PLC 01 (S7-1500)',
    type: 'IndustrialAsset',
    ip: '192.168.10.50',
    criticality: 'Critical',
    riskScore: riskMap['IndustrialAsset_be39c0ba-567a-4246-ab4e-0540f55ead09'] || 0,
    status: 'Operational',
    x: 600,
    y: 120
  });

  nodes.push({
    id: 'cooling-plc',
    name: 'Cooling Pump PLC 02 (M580)',
    type: 'IndustrialAsset',
    ip: '192.168.10.52',
    criticality: 'High',
    riskScore: riskMap['IndustrialAsset_50a6b58c-dc9c-43d1-8c38-79471ff32241'] || 0,
    status: 'Operational',
    x: 600,
    y: 300
  });

  // Group 4: Users / Operators (Logistics / Admin - Bottom)
  nodes.push({
    id: 'op-ws',
    name: 'Operator Station 01',
    type: 'Device',
    ip: '192.168.10.110',
    criticality: 'High',
    riskScore: riskMap['Device_a38f38cb-41c5-4a23-8967-848bc6325ba2'] || 0,
    status: 'Authorized',
    x: 200,
    y: 320
  });

  // Links definitions
  links.push({ from: 'eng-ws', to: 'center-gateway', active: true });
  links.push({ from: 'op-ws', to: 'center-gateway', active: true });
  links.push({ from: 'center-gateway', to: 'turbine-plc', active: true });
  links.push({ from: 'center-gateway', to: 'cooling-plc', active: true });

  const getNodeColor = (score: number) => {
    if (score > 80) return 'text-red-500 fill-red-500/10 stroke-red-500';
    if (score > 60) return 'text-orange-500 fill-orange-500/10 stroke-orange-500';
    if (score > 30) return 'text-yellow-500 fill-yellow-500/10 stroke-yellow-500';
    return 'text-emerald-500 fill-emerald-500/10 stroke-emerald-500';
  };

  const getLinkColor = (scoreFrom: number, scoreTo: number) => {
    const maxScore = Math.max(scoreFrom, scoreTo);
    if (maxScore > 80) return 'stroke-red-500/50';
    if (maxScore > 60) return 'stroke-orange-500/50';
    if (maxScore > 30) return 'stroke-yellow-500/50';
    return 'stroke-emerald-500/35';
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Network SVG Viewport */}
      <div className="glass-panel p-4 rounded-xl border border-zinc-800 lg:col-span-3 flex flex-col relative overflow-hidden bg-zinc-950/20 min-h-[380px]">
        <div className="flex justify-between items-center border-b border-zinc-850 pb-2.5 mb-4">
          <div className="flex items-center space-x-1.5">
            <Activity className="h-4 w-4 text-emerald-400" />
            <span className="text-xs font-bold text-zinc-300 font-mono uppercase tracking-wide">Live Industrial Twin Topology map</span>
          </div>
          <div className="flex items-center space-x-3 text-[9px] font-mono">
            <span className="flex items-center space-x-1"><span className="h-2 w-2 rounded-full bg-emerald-500"></span><span className="text-zinc-500">Normal</span></span>
            <span className="flex items-center space-x-1"><span className="h-2 w-2 rounded-full bg-yellow-500"></span><span className="text-zinc-500">Warning</span></span>
            <span className="flex items-center space-x-1"><span className="h-2 w-2 rounded-full bg-orange-500"></span><span className="text-zinc-500">High Risk</span></span>
            <span className="flex items-center space-x-1 animate-pulse"><span className="h-2 w-2 rounded-full bg-red-500"></span><span className="text-zinc-500">Active Threat</span></span>
          </div>
        </div>

        {/* SVG View */}
        <div className="flex-1 flex justify-center items-center">
          <svg viewBox="0 0 800 450" className="w-full max-w-[760px] h-auto">
            {/* Draw Links */}
            {links.map((link, index) => {
              const fromNode = nodes.find(n => n.id === link.from)!;
              const toNode = nodes.find(n => n.id === link.to)!;
              const colorClass = getLinkColor(fromNode.riskScore, toNode.riskScore);
              const isHigh = Math.max(fromNode.riskScore, toNode.riskScore) > 60;

              return (
                <g key={index}>
                  <line
                    x1={fromNode.x}
                    y1={fromNode.y}
                    x2={toNode.x}
                    y2={toNode.y}
                    className={`stroke-2 transition-all duration-500 ${colorClass}`}
                  />
                  {/* Glowing transmission packet dash arrays */}
                  <line
                    x1={fromNode.x}
                    y1={fromNode.y}
                    x2={toNode.x}
                    y2={toNode.y}
                    strokeDasharray="6,20"
                    className={`stroke-[3px] fill-none stroke-zinc-200/80`}
                    style={{
                      animation: 'dash 3s linear infinite',
                      stroke: isHigh ? '#f43f5e' : '#10b981'
                    }}
                  />
                </g>
              );
            })}

            {/* Draw Nodes */}
            {nodes.map((node) => {
              const colorClass = getNodeColor(node.riskScore);
              const isSelected = selectedNode?.id === node.id;
              const isCritical = node.riskScore > 80;

              return (
                <g 
                  key={node.id} 
                  transform={`translate(${node.x}, ${node.y})`}
                  className="cursor-pointer group"
                  onClick={() => setSelectedNode(node)}
                >
                  {/* Glowing alert ring if anomaly matches */}
                  {isCritical && (
                    <circle 
                      r="28" 
                      className="fill-none stroke-red-500/40 stroke-2 animate-ping"
                    />
                  )}
                  {node.riskScore > 60 && (
                    <circle 
                      r="24" 
                      className={`fill-none stroke-2 animate-pulse ${
                        node.riskScore > 80 ? 'stroke-red-500/30' : 'stroke-orange-500/30'
                      }`}
                    />
                  )}

                  {/* Core node shell */}
                  <circle
                    r="18"
                    className={`stroke-2 transition-all duration-500 fill-zinc-950/90 ${
                      isSelected ? 'stroke-zinc-100' : colorClass
                    }`}
                  />

                  {/* Dynamic icons */}
                  <g transform="translate(-8, -8)" className="pointer-events-none select-none text-zinc-300">
                    {node.type === 'IndustrialAsset' && <Cpu className="h-4.5 w-4.5 text-zinc-300" />}
                    {node.type === 'Device' && <Monitor className="h-4.5 w-4.5 text-zinc-300" />}
                    {node.type === 'User' && <Users className="h-4.5 w-4.5 text-zinc-300" />}
                  </g>

                  {/* Label */}
                  <text
                    y="32"
                    textAnchor="middle"
                    className="fill-zinc-400 font-mono text-[9px] pointer-events-none tracking-wide"
                  >
                    {node.name.split(' ')[0]} {node.name.split(' ')[1] || ''}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* CSS for animating packets */}
        <style>{`
          @keyframes dash {
            to {
              stroke-dashoffset: -100;
            }
          }
        `}</style>
      </div>

      {/* Side Inspector Panel */}
      <div className="glass-panel p-5 rounded-xl border border-zinc-800 flex flex-col justify-between space-y-4 min-h-[350px]">
        {selectedNode ? (
          <div className="space-y-4 font-mono text-xs text-zinc-400">
            <div className="border-b border-zinc-850 pb-2 flex justify-between items-center">
              <span className="text-[10px] uppercase font-bold text-zinc-500">NODE DIAGNOSTICS</span>
              <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                selectedNode.riskScore > 80 ? 'bg-red-500/10 text-red-400 border border-red-500/30' :
                selectedNode.riskScore > 60 ? 'bg-orange-500/10 text-orange-400 border border-orange-500/30' :
                selectedNode.riskScore > 30 ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30' :
                'bg-emerald-500/10 text-emerald-400 border border-emerald-500/25'
              }`}>
                {selectedNode.riskScore} RISK
              </span>
            </div>

            <div className="space-y-2.5">
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Entity Name</span>
                <span className="text-zinc-200 font-semibold">{selectedNode.name}</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">IP Address</span>
                <span className="text-zinc-300">{selectedNode.ip || '127.0.0.1'}</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Entity Type</span>
                <span className="text-zinc-300">{selectedNode.type}</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Criticality</span>
                <span className="text-zinc-200">{selectedNode.criticality || 'Normal'}</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Deployment Status</span>
                <span className="text-zinc-300">{selectedNode.status}</span>
              </div>
            </div>

            <div className="bg-zinc-950/40 p-3 rounded-lg border border-zinc-900 flex items-start space-x-2 text-[10px]">
              <Info className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
              <p className="leading-relaxed">This node is evaluated in real time by the Behavioral Engine. Current anomaly score lies within boundaries.</p>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col justify-center items-center text-center space-y-2 font-mono">
            <Shield className="h-10 w-10 text-zinc-700" />
            <p className="text-xs text-zinc-500 uppercase font-bold tracking-wide">Select Node</p>
            <p className="text-[10px] text-zinc-600 px-4">Click any node in the twin topology map to inspect physical diagnostics and active risk vectors.</p>
          </div>
        )}
      </div>
    </div>
  );
};
