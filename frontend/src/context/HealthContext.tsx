import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';

interface HealthContextType {
  backendConnected: boolean;
  dbConnected: boolean;
  isLoading: boolean;
  errorMessage: string | null;
  checkHealth: () => Promise<void>;
}

const HealthContext = createContext<HealthContextType | undefined>(undefined);

export const HealthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  const [dbConnected, setDbConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      // Direct call to the health endpoint (configured on root or API prefix)
      // Check both health and fallbacks
      const response = await apiClient.get('/health');
      if (response.status === 200 && response.data) {
        setBackendConnected(true);
        setDbConnected(response.data.database === 'healthy');
        setErrorMessage(null);
      } else {
        setBackendConnected(true);
        setDbConnected(false);
        setErrorMessage('Database connection issue reported by server.');
      }
    } catch (error: any) {
      setBackendConnected(false);
      setDbConnected(false);
      setErrorMessage(error.message || 'Unable to connect to the AegisOne API.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    // Poll backend health status every 10 seconds
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return (
    <HealthContext.Provider value={{ backendConnected, dbConnected, isLoading, errorMessage, checkHealth }}>
      {children}
    </HealthContext.Provider>
  );
};

export const useHealth = () => {
  const context = useContext(HealthContext);
  if (context === undefined) {
    throw new Error('useHealth must be used within a HealthProvider');
  }
  return context;
};
