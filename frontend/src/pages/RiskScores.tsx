import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import type { RiskScore } from '../types';
import { TrendingUp, RefreshCw, Layers } from 'lucide-react';
import { useHealth } from '../context/HealthContext';

export const RiskScores: React.FC = () => {
  const { backendConnected, dbConnected } = useHealth();
  const [scores, setScores] = useState<RiskScore[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRiskScores = async () => {
    if (!backendConnected || !dbConnected) return;
    setLoading(true);
    try {
      const response = await apiClient.get<RiskScore[]>('/risk-scores');
      setScores(response.data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch risk score analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRiskScores();
  }, [backendConnected, dbConnected]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-wide text-white">BEHAVIORAL RISK SCORES</h2>
          <p className="text-xs text-zinc-400 font-mono">Real-time threat indices computed for OT devices, physical assets, and operator profiles</p>
        </div>
        <button
          onClick={fetchRiskScores}
          className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>RECOMPUTE RISK</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/20 border border-red-500/30 text-red-400 rounded-lg font-mono text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-zinc-500 font-mono text-xs">Calculating score distributions...</div>
      ) : scores.length === 0 ? (
        <div className="text-zinc-400 font-mono text-xs py-10 text-center glass-panel rounded-xl">
          No risk metrics registered in system metadata.
        </div>
      ) : (
        <div className="space-y-6">
          {scores.map((risk) => (
            <div key={risk.id} className="glass-panel p-5 rounded-xl space-y-4">
              {/* Header row */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="bg-zinc-800 p-2.5 rounded-lg text-zinc-300">
                    <Layers className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-zinc-200 uppercase tracking-wide text-sm font-sans">
                      {risk.entity_type} ID: {risk.entity_id}
                    </h3>
                    <p className="text-[10px] text-zinc-500 font-mono">
                      LOGGED: {new Date(risk.last_calculated).toLocaleString()}
                    </p>
                  </div>
                </div>
                
                {/* Visual Score Badge */}
                <div className="text-right">
                  <span className={`text-2xl font-bold font-mono ${
                    risk.score >= 75 ? 'text-red-500' :
                    risk.score >= 40 ? 'text-orange-500' : 'text-emerald-500'
                  }`}>
                    {risk.score}
                  </span>
                  <span className="text-[10px] text-zinc-500 font-mono block uppercase">Threat Index</span>
                </div>
              </div>

              {/* Progress bar visual indicator */}
              <div className="w-full bg-zinc-900 border border-zinc-800 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    risk.score >= 75 ? 'bg-gradient-to-r from-red-600 to-red-500' :
                    risk.score >= 40 ? 'bg-gradient-to-r from-amber-600 to-amber-500' :
                    'bg-gradient-to-r from-emerald-600 to-emerald-500'
                  }`}
                  style={{ width: `${risk.score}%` }}
                ></div>
              </div>

              {/* Dynamic Risk Factors Table/Bullets */}
              <div className="bg-zinc-950/40 border border-zinc-800/80 p-3 rounded-lg space-y-2">
                <div className="text-[10px] text-zinc-400 font-mono font-bold flex items-center space-x-1.5 uppercase">
                  <TrendingUp className="h-3.5 w-3.5 text-zinc-500" />
                  <span>Calculated Vulnerability Metrics:</span>
                </div>
                
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1.5 list-disc pl-4 text-zinc-300 font-mono text-xs">
                  {Object.entries(risk.factors).map(([key, val]) => (
                    <li key={key} className="marker:text-zinc-500">
                      <span className="text-zinc-500 uppercase">{key.replace(/_/g, ' ')}:</span>{' '}
                      <span className={val === true || val > 0 ? 'text-amber-500 font-semibold' : 'text-zinc-300'}>
                        {typeof val === 'boolean' ? (val ? 'TRUE' : 'FALSE') : String(val)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
