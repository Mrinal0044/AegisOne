import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import type { IndustrialAsset } from '../types';
import { Cpu, Tag, MapPin, HardDrive, RefreshCw } from 'lucide-react';
import { useHealth } from '../context/HealthContext';

export const Assets: React.FC = () => {
  const { backendConnected, dbConnected } = useHealth();
  const [assets, setAssets] = useState<IndustrialAsset[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAssets = async () => {
    if (!backendConnected || !dbConnected) return;
    setLoading(true);
    try {
      const response = await apiClient.get<IndustrialAsset[]>('/industrial-assets');
      setAssets(response.data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to retrieve industrial assets from core API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, [backendConnected, dbConnected]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-wide text-white">INDUSTRIAL ASSET INVENTORY</h2>
          <p className="text-xs text-zinc-400 font-mono">Monitored PLCs, RTUs, HMIs and SCADA controllers</p>
        </div>
        <button
          onClick={fetchAssets}
          className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>RELOAD INVENTORY</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/20 border border-red-500/30 text-red-400 rounded-lg font-mono text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-zinc-500 font-mono text-xs">Querying asset data from postgres...</div>
      ) : assets.length === 0 ? (
        <div className="text-zinc-400 font-mono text-xs py-10 text-center glass-panel rounded-xl">
          No industrial assets registered in the database.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {assets.map((asset) => (
            <div key={asset.id} className="glass-panel p-5 rounded-xl space-y-4 relative overflow-hidden group hover:border-zinc-700 transition-all duration-300">
              {/* Criticality Ribbon */}
              <div className={`absolute top-0 right-0 w-24 text-center py-0.5 text-[9px] font-bold font-mono tracking-wider rotate-45 translate-x-7 translate-y-3 ${
                asset.criticality === 'Critical' ? 'bg-red-500 text-white' :
                asset.criticality === 'High' ? 'bg-orange-500 text-white' :
                asset.criticality === 'Medium' ? 'bg-yellow-500 text-black' :
                'bg-cyan-500 text-black'
              }`}>
                {asset.criticality.toUpperCase()}
              </div>

              {/* Title & Vendor */}
              <div className="flex items-start space-x-3">
                <div className="bg-zinc-800 p-2.5 rounded-lg text-zinc-300">
                  <Cpu className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-bold text-zinc-200">{asset.name}</h3>
                  <div className="flex items-center space-x-2 text-zinc-400 text-xs font-mono mt-0.5">
                    <Tag className="h-3 w-3 text-zinc-500" />
                    <span>{asset.vendor} {asset.model}</span>
                  </div>
                </div>
              </div>

              {/* Grid Specifications */}
              <div className="grid grid-cols-2 gap-4 border-t border-b border-zinc-800/80 py-3 font-mono text-xs">
                <div>
                  <div className="text-zinc-500 text-[10px] uppercase">IP Address</div>
                  <div className="text-zinc-300 font-semibold">{asset.ip_address}</div>
                </div>
                <div>
                  <div className="text-zinc-500 text-[10px] uppercase">MAC Address</div>
                  <div className="text-zinc-300">{asset.mac_address}</div>
                </div>
                <div>
                  <div className="text-zinc-500 text-[10px] uppercase">Asset Class</div>
                  <div className="text-zinc-300 flex items-center space-x-1">
                    <HardDrive className="h-3 w-3 text-zinc-500" />
                    <span>{asset.asset_type}</span>
                  </div>
                </div>
                <div>
                  <div className="text-zinc-500 text-[10px] uppercase">Physical Zone</div>
                  <div className="text-zinc-300 flex items-center space-x-1">
                    <MapPin className="h-3 w-3 text-zinc-500" />
                    <span className="truncate max-w-[130px]">{asset.location}</span>
                  </div>
                </div>
              </div>

              {/* Status footer */}
              <div className="flex items-center justify-between text-xs pt-1">
                <span className="text-zinc-500 font-mono text-[10px]">UUID: {asset.id.slice(0, 8)}...</span>
                <div className="flex items-center space-x-1.5">
                  <span className={`h-2 w-2 rounded-full ${
                    asset.status === 'Operational' ? 'bg-emerald-500 animate-pulse-slow' :
                    asset.status === 'Maintenance' ? 'bg-orange-500' : 'bg-red-500'
                  }`}></span>
                  <span className="font-mono text-zinc-300 text-[11px]">{asset.status.toUpperCase()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
