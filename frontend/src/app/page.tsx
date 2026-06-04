"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Activity, ShieldAlert, Globe, Server, LogOut, Search } from 'lucide-react';
import api from '@/lib/api';

export default function Dashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [target, setTarget] = useState('');
  const [scans, setScans] = useState<any[]>([]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
    } else {
      setLoading(false);
      // Optional: fetch recent scans
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  const startScan = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.post('/scans', {
        target,
        scan_type: 'full',
        priority: 5
      });
      setScans([response.data, ...scans]);
      setTarget('');
    } catch (err) {
      console.error(err);
      alert('Failed to start scan');
    }
  };

  if (loading) return <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white">Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-sans">
      {/* Sidebar / Navbar */}
      <nav className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <ShieldAlert className="w-8 h-8 text-emerald-400" />
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                CyberGhost OSINT
              </span>
            </div>
            <button onClick={handleLogout} className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
              <LogOut className="w-5 h-5" />
              <span className="text-sm font-medium">Sign Out</span>
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Top Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-6 flex items-center gap-4">
            <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400"><Activity size={24} /></div>
            <div>
              <p className="text-sm text-gray-400">Active Scans</p>
              <p className="text-2xl font-bold text-white">{scans.filter(s => s.status === 'pending' || s.status === 'running').length}</p>
            </div>
          </div>
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-6 flex items-center gap-4">
            <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400"><Globe size={24} /></div>
            <div>
              <p className="text-sm text-gray-400">Nodes in Graph</p>
              <p className="text-2xl font-bold text-white">--</p>
            </div>
          </div>
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-6 flex items-center gap-4">
            <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400"><Server size={24} /></div>
            <div>
              <p className="text-sm text-gray-400">System Health</p>
              <p className="text-2xl font-bold text-emerald-400">Operational</p>
            </div>
          </div>
        </div>

        {/* New Scan Action */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-2xl p-8 shadow-2xl">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Search className="text-blue-400" />
            Launch Investigation
          </h2>
          <form onSubmit={startScan} className="flex gap-4">
            <input 
              type="text" 
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="Enter domain, IP, or email (e.g. example.com)"
              className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
              required
            />
            <button type="submit" className="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold shadow-lg shadow-blue-500/30 transition-all active:scale-95">
              Start Scan
            </button>
          </form>
        </div>

        {/* Recent Scans Table */}
        <div className="bg-gray-800/30 border border-gray-700/50 rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700/50 bg-gray-800/50">
            <h3 className="font-semibold">Recent Operations</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-400">
              <thead className="text-xs uppercase bg-gray-900/50 text-gray-500">
                <tr>
                  <th className="px-6 py-4 font-medium">Target</th>
                  <th className="px-6 py-4 font-medium">Type</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                  <th className="px-6 py-4 font-medium">Task ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {scans.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                      No recent scans found.
                    </td>
                  </tr>
                ) : (
                  scans.map((scan, i) => (
                    <tr key={i} className="hover:bg-gray-800/30 transition-colors">
                      <td className="px-6 py-4 font-medium text-gray-200">{scan.target}</td>
                      <td className="px-6 py-4"><span className="px-2 py-1 bg-blue-500/10 text-blue-400 rounded-md text-xs">{scan.scan_type}</span></td>
                      <td className="px-6 py-4">
                        <span className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${scan.status === 'pending' ? 'bg-yellow-400' : 'bg-emerald-400'}`}></span>
                          {scan.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono text-xs">{scan.celery_task_id || 'pending...'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
