import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { Play, RotateCcw, Activity, ShieldAlert, Cpu, Monitor, Brain, Users, CheckCircle, Clock } from 'lucide-react';
import { useHealth } from '../context/HealthContext';

export const DetectionEngine: React.FC = () => {
  const { backendConnected, dbConnected } = useHealth();
  const [loading, setLoading] = useState<boolean>(true);
  const [training, setTraining] = useState<boolean>(false);
  const [retraining, setRetraining] = useState<boolean>(false);
  
  // State maps
  const [aiStatus, setAiStatus] = useState<any>(null);
  const [models, setModels] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [liveAlerts, setLiveAlerts] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fetchEngineData = async () => {
    if (!backendConnected || !dbConnected) return;
    setLoading(true);
    try {
      const [statusRes, modelsRes, metricsRes, alertsRes] = await Promise.all([
        apiClient.get('/ai/status'),
        apiClient.get('/ai/models'),
        apiClient.get('/ai/metrics'),
        apiClient.get('/ai/alerts/live')
      ]);

      setAiStatus(statusRes.data);
      setModels(modelsRes.data);
      setMetrics(metricsRes.data);
      setLiveAlerts(alertsRes.data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to refresh Behavioral Detection Engine diagnostics.');
    } finally {
      setLoading(false);
    }
  };

  const handleTrain = async (isRetrain: boolean) => {
    if (isRetrain) setRetraining(true);
    else setTraining(true);

    try {
      const endpoint = isRetrain ? '/ai/retrain' : '/ai/train';
      await apiClient.post(endpoint);
      
      // Await processing
      setTimeout(() => {
        fetchEngineData();
        setTraining(false);
        setRetraining(false);
      }, 2500);
    } catch (err) {
      console.error(err);
      setTraining(false);
      setRetraining(false);
    }
  };

  useEffect(() => {
    fetchEngineData();
    // Poll every 10s to reflect dynamic risk scores and generated alerts
    const interval = setInterval(fetchEngineData, 10000);
    return () => clearInterval(interval);
  }, [backendConnected, dbConnected]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-zinc-800 pb-4 gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-wide text-white">BEHAVIORAL INTELLIGENCE DETECTION ENGINE</h2>
          <p className="text-xs text-zinc-400 font-mono">Continuous unsupervised anomaly parsing and risk score assessment</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => handleTrain(false)}
            disabled={training || retraining}
            className="flex items-center space-x-2 bg-emerald-950/40 hover:bg-emerald-900/60 border border-emerald-500/30 text-emerald-400 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors disabled:opacity-50"
          >
            <Play className="h-3.5 w-3.5" />
            <span>{training ? 'FITTING...' : 'FIT MODELS'}</span>
          </button>
          <button
            onClick={() => handleTrain(true)}
            disabled={training || retraining}
            className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors disabled:opacity-50"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>{retraining ? 'CLEARING...' : 'RESET & RETRAIN'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-950/20 border border-red-500/30 text-red-400 rounded-lg font-mono text-xs">
          {error}
        </div>
      )}

      {/* Stats and Metrics Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Core status card */}
        {aiStatus && (
          <div className="glass-panel p-5 rounded-xl space-y-4 border border-zinc-800">
            <div className="flex justify-between items-center border-b border-zinc-850 pb-2.5">
              <span className="text-xs text-zinc-500 font-mono uppercase font-bold">ENGINE DEPLOYMENT</span>
              <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 px-2 py-0.5 rounded font-mono font-bold tracking-wider animate-pulse">
                {aiStatus.status}
              </span>
            </div>
            
            <div className="space-y-3 font-mono text-xs text-zinc-400">
              <div className="flex justify-between">
                <span>Total Entities:</span>
                <span className="text-zinc-200 font-bold">
                  {aiStatus.coverage.users.total + aiStatus.coverage.devices.total + aiStatus.coverage.industrial_assets.total}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Trained ML Models:</span>
                <span className="text-emerald-400 font-bold">{aiStatus.total_models_trained}</span>
              </div>
              
              <div className="border-t border-zinc-900 pt-3 space-y-2">
                <div className="text-[10px] text-zinc-500 uppercase">Model Coverage:</div>
                <div className="grid grid-cols-2 gap-2 text-[10px]">
                  <div className="bg-zinc-950/40 p-2 rounded border border-zinc-900">
                    <div className="text-zinc-500">Users</div>
                    <div className="text-zinc-200 font-semibold">{aiStatus.coverage.users.trained} / {aiStatus.coverage.users.total}</div>
                  </div>
                  <div className="bg-zinc-950/40 p-2 rounded border border-zinc-900">
                    <div className="text-zinc-500">Devices</div>
                    <div className="text-zinc-200 font-semibold">{aiStatus.coverage.devices.trained} / {aiStatus.coverage.devices.total}</div>
                  </div>
                  <div className="bg-zinc-950/40 p-2 rounded border border-zinc-900">
                    <div className="text-zinc-500">OT Assets</div>
                    <div className="text-zinc-200 font-semibold">{aiStatus.coverage.industrial_assets.trained} / {aiStatus.coverage.industrial_assets.total}</div>
                  </div>
                  <div className="bg-zinc-950/40 p-2 rounded border border-zinc-900">
                    <div className="text-zinc-500">Depts</div>
                    <div className="text-zinc-200 font-semibold">{aiStatus.coverage.departments.trained} / {aiStatus.coverage.departments.total}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Prediction Metrics */}
        {metrics && (
          <div className="glass-panel p-5 rounded-xl space-y-4 border border-zinc-800 md:col-span-2">
            <div className="border-b border-zinc-850 pb-2.5">
              <span className="text-xs text-zinc-500 font-mono uppercase font-bold">PREDICTION & INFERENCE METRICS</span>
            </div>
            
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 font-mono text-xs">
              <div className="bg-zinc-950/40 p-3.5 rounded-lg border border-zinc-900">
                <div className="text-zinc-500 text-[10px] uppercase">Evaluations</div>
                <div className="text-lg font-bold text-zinc-200 mt-1">{metrics.total_predictions_evaluated}</div>
              </div>
              <div className="bg-zinc-950/40 p-3.5 rounded-lg border border-zinc-900">
                <div className="text-zinc-500 text-[10px] uppercase">Anomalies Flagged</div>
                <div className="text-lg font-bold text-red-400 mt-1">{metrics.anomalies_flagged}</div>
              </div>
              <div className="bg-zinc-950/40 p-3.5 rounded-lg border border-zinc-900 col-span-2 sm:col-span-1">
                <div className="text-zinc-500 text-[10px] uppercase">Avg Inference</div>
                <div className="text-lg font-bold text-emerald-400 mt-1">{(metrics.average_inference_time_seconds * 1000).toFixed(2)} ms</div>
              </div>
              <div className="bg-zinc-950/40 p-3.5 rounded-lg border border-zinc-900">
                <div className="text-zinc-500 text-[10px] uppercase">FP Rate</div>
                <div className="text-lg font-bold text-zinc-400 mt-1">{(metrics.false_positive_rate_placeholder * 100).toFixed(1)}%</div>
              </div>
              <div className="bg-zinc-950/40 p-3.5 rounded-lg border border-zinc-900">
                <div className="text-zinc-500 text-[10px] uppercase">Precision Target</div>
                <div className="text-lg font-bold text-zinc-400 mt-1">{(metrics.precision_placeholder * 100).toFixed(1)}%</div>
              </div>
              <div className="bg-zinc-950/40 p-3.5 rounded-lg border border-zinc-900">
                <div className="text-zinc-500 text-[10px] uppercase">Recall Rate</div>
                <div className="text-lg font-bold text-zinc-400 mt-1">{(metrics.recall_placeholder * 100).toFixed(1)}%</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Live Alerts Stream */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="h-5 w-5 text-red-500" />
          <h3 className="text-sm font-bold text-zinc-300 font-mono uppercase tracking-wide">Live Behavioral Security Alerts Queue</h3>
        </div>
        
        <div className="glass-panel rounded-xl overflow-hidden border border-zinc-800/80">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="bg-zinc-900/60 border-b border-zinc-850 text-zinc-400 text-[10px] uppercase tracking-wider">
                  <th className="p-4">Alert Details</th>
                  <th className="p-4">Source Entity</th>
                  <th className="p-4">Severity</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Detected</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900">
                {liveAlerts.map((alert) => (
                  <tr key={alert.id} className="hover:bg-zinc-900/40 text-zinc-300">
                    <td className="p-4">
                      <div className="font-semibold text-zinc-200">{alert.title}</div>
                      <div className="text-[10px] text-zinc-500 mt-0.5">{alert.description}</div>
                    </td>
                    <td className="p-4">
                      {alert.user && (
                        <div className="flex items-center space-x-1.5">
                          <Users className="h-3.5 w-3.5 text-zinc-500" />
                          <span>User: {alert.user.username}</span>
                        </div>
                      )}
                      {alert.device && (
                        <div className="flex items-center space-x-1.5">
                          <Monitor className="h-3.5 w-3.5 text-zinc-500" />
                          <span>Device: {alert.device.hostname}</span>
                        </div>
                      )}
                      {alert.asset && (
                        <div className="flex items-center space-x-1.5">
                          <Cpu className="h-3.5 w-3.5 text-zinc-500" />
                          <span>Asset: {alert.asset.name}</span>
                        </div>
                      )}
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        alert.severity === 'Critical' ? 'bg-red-500/10 text-red-400 border border-red-500/30' :
                        alert.severity === 'High' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/30' :
                        alert.severity === 'Medium' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30' :
                        'bg-zinc-800 text-zinc-400'
                      }`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td className="p-4 text-zinc-400">{alert.status}</td>
                    <td className="p-4 text-zinc-500 flex items-center space-x-1">
                      <Clock className="h-3.5 w-3.5 shrink-0" />
                      <span>{new Date(alert.created_at).toLocaleTimeString()}</span>
                    </td>
                  </tr>
                ))}
                {liveAlerts.length === 0 && (
                  <tr>
                    <td colSpan={5} className="p-6 text-center text-zinc-500 font-mono">No active behavioral alerts flagged.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Model Manifest Directory */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <Brain className="h-5 w-5 text-emerald-400" />
          <h3 className="text-sm font-bold text-zinc-300 font-mono uppercase tracking-wide">Unsupervised ML Model Registry</h3>
        </div>

        <div className="glass-panel rounded-xl overflow-hidden border border-zinc-800/80">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="bg-zinc-900/60 border-b border-zinc-850 text-zinc-400 text-[10px] uppercase tracking-wider">
                  <th className="p-4">Model ID</th>
                  <th className="p-4">Algorithm</th>
                  <th className="p-4 text-right">Features</th>
                  <th className="p-4 text-right">Dataset Size</th>
                  <th className="p-4 text-right">Train Duration</th>
                  <th className="p-4">Last Fitted</th>
                  <th className="p-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900">
                {models.map((m) => (
                  <tr key={m.model_name} className="hover:bg-zinc-900/40 text-zinc-300">
                    <td className="p-4">
                      <div className="font-semibold text-zinc-200">{m.model_name}</div>
                      <div className="text-[10px] text-zinc-500 mt-0.5">Version Index: v{m.version}</div>
                    </td>
                    <td className="p-4 text-zinc-400">{m.algorithm}</td>
                    <td className="p-4 text-right text-zinc-200 font-semibold">{m.features_count}</td>
                    <td className="p-4 text-right text-zinc-400">{m.training_dataset_size} samples</td>
                    <td className="p-4 text-right text-zinc-400">{(m.training_duration_seconds * 1000).toFixed(1)} ms</td>
                    <td className="p-4 text-zinc-500">{new Date(m.training_time).toLocaleString()}</td>
                    <td className="p-4">
                      <span className="flex items-center space-x-1 text-[10px] text-emerald-400 font-bold">
                        <CheckCircle className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                        <span>{m.status}</span>
                      </span>
                    </td>
                  </tr>
                ))}
                {models.length === 0 && (
                  <tr>
                    <td colSpan={7} className="p-6 text-center text-zinc-500 font-mono">No trained models found. Click FIT MODELS to run the training sweep.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
