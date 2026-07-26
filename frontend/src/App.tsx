import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { HealthProvider } from './context/HealthContext';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { StatusBar } from './components/StatusBar';

// Import Pages
import { DashboardPage } from './pages/DashboardPage';
import { Assets } from './pages/Assets';
import { Devices } from './pages/Devices';
import { Events } from './pages/Events';
import { Alerts } from './pages/Alerts';
import { RiskScores } from './pages/RiskScores';
import { Users } from './pages/Users';
import { BehaviorProfiles } from './pages/BehaviorProfiles';
import { FeatureStore } from './pages/FeatureStore';
import { DetectionEngine } from './pages/DetectionEngine';
import { ThreatSimulation } from './pages/ThreatSimulation';
import { OperationsPage } from './pages/OperationsPage';

function App() {
  return (
    <HealthProvider>
      <Router>
        <div className="flex flex-col h-screen w-screen bg-[#030712] overflow-hidden text-zinc-100">
          {/* Top Header Panel */}
          <Header />

          {/* Core Panel Division */}
          <div className="flex flex-1 overflow-hidden">
            {/* Navigation Panel */}
            <Sidebar />

            {/* View Viewport */}
            <main className="flex-1 overflow-y-auto p-6 bg-zinc-950/40">
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/assets" element={<Assets />} />
                <Route path="/devices" element={<Devices />} />
                <Route path="/events" element={<Events />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/risk-scores" element={<RiskScores />} />
                <Route path="/users" element={<Users />} />
                <Route path="/behavior-profiles" element={<BehaviorProfiles />} />
                <Route path="/features" element={<FeatureStore />} />
                <Route path="/detection-engine" element={<DetectionEngine />} />
                <Route path="/threat-simulation" element={<ThreatSimulation />} />
                <Route path="/operations" element={<OperationsPage />} />
              </Routes>
            </main>
          </div>

          {/* Bottom Telemetry Bar */}
          <StatusBar />
        </div>
      </Router>
    </HealthProvider>
  );
}

export default App;
