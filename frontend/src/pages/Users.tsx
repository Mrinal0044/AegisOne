import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import type { User } from '../types';
import { Users as UsersIcon, RefreshCw, KeyRound } from 'lucide-react';
import { useHealth } from '../context/HealthContext';

export const Users: React.FC = () => {
  const { backendConnected, dbConnected } = useHealth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = async () => {
    if (!backendConnected || !dbConnected) return;
    setLoading(true);
    try {
      const response = await apiClient.get<User[]>('/users');
      setUsers(response.data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch user directory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [backendConnected, dbConnected]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-wide text-white">USERS & OPERATORS</h2>
          <p className="text-xs text-zinc-400 font-mono">SOC security analysts and industrial control systems operators</p>
        </div>
        <button
          onClick={fetchUsers}
          className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>REFRESH DIRECTORY</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/20 border border-red-500/30 text-red-400 rounded-lg font-mono text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-zinc-500 font-mono text-xs">Querying LDAP/database directory...</div>
      ) : users.length === 0 ? (
        <div className="text-zinc-400 font-mono text-xs py-10 text-center glass-panel rounded-xl">
          No users registered.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {users.map((user) => (
            <div key={user.id} className="glass-panel p-5 rounded-xl space-y-4 relative overflow-hidden">
              {/* Profile Card Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="bg-zinc-800 p-2.5 rounded-lg text-zinc-300">
                    <UsersIcon className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-zinc-200">{user.full_name}</h3>
                    <p className="text-xs text-zinc-400 font-mono">@{user.username}</p>
                  </div>
                </div>
                
                {/* Role Badge */}
                <span className={`text-[10px] font-bold font-mono px-2 py-0.5 rounded border ${
                  user.role === 'Administrator' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                  user.role === 'Security Analyst' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                  'bg-blue-500/10 text-blue-400 border-blue-500/20'
                }`}>
                  {user.role.toUpperCase()}
                </span>
              </div>

              {/* Scope details */}
              <div className="border-t border-b border-zinc-800/80 py-3 font-mono text-xs space-y-2">
                <div className="flex justify-between">
                  <span className="text-zinc-500">EMAIL:</span>
                  <span className="text-zinc-300">{user.email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">DEPARTMENT:</span>
                  <span className="text-zinc-300">
                    {user.department ? `${user.department.name} (${user.department.code})` : 'UNASSIGNED'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">UUID:</span>
                  <span className="text-zinc-500 text-[10px]">{user.id}</span>
                </div>
              </div>

              {/* Status footer */}
              <div className="flex items-center justify-between text-xs pt-1">
                <span className="text-zinc-500 font-mono text-[10px]">
                  CREATED: {new Date(user.created_at).toLocaleDateString()}
                </span>
                
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-1.5">
                    <span className={`h-2 w-2 rounded-full ${user.is_active ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                    <span className="font-mono text-zinc-300 text-[11px]">
                      {user.is_active ? 'ACTIVE' : 'DEACTIVATED'}
                    </span>
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
