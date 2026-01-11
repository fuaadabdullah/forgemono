"use client";

import React, { useState } from 'react';
import { DashboardSkeleton } from '@/components/LoadingSkeleton';
import { UsageStats } from '@/components/dashboard/UsageStats';
import { ProviderHealth } from '@/components/dashboard/ProviderHealth';
import { RoutingDashboard } from '@/components/dashboard/RoutingDashboard';
import { Button } from '@/components/ui';
import { RefreshCw, Settings, Database, FileText, Cpu } from 'lucide-react';

/**
 * Dashboard Page - Next.js App Router
 * Enhanced version with consistent dark theme and visual design
 */
export default function DashboardPage() {
  const [loading, setLoading] = useState(false);

  const handleRefresh = () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  };

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-full h-full">
          <div className="absolute top-20 left-10 w-72 h-72 bg-emerald-500/5 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute top-40 right-10 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl animate-pulse delay-1000"></div>
          <div className="absolute bottom-20 left-1/3 w-80 h-80 bg-blue-500/5 rounded-full blur-3xl animate-pulse delay-500"></div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative z-10">
        <div className="container mx-auto px-6 py-8 space-y-8">
          {/* Header */}
          <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-8 shadow-xl">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white mb-2">System Dashboard</h1>
                <p className="text-slate-300">Real-time overview of your AI infrastructure</p>
              </div>
              <div className="flex space-x-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={loading}
                  className="border-white/30 text-white hover:bg-white/10 font-semibold px-4 py-2 rounded-lg transition-all duration-300 backdrop-blur-sm"
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </Button>
              </div>
            </div>
          </div>

          {/* Usage Statistics */}
          <UsageStats />

          {/* Provider Health */}
          <ProviderHealth />

          {/* AI Routing Analytics */}
          <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-8 shadow-xl">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
              <span className="text-2xl">🧠</span> AI Provider Routing
            </h2>
            <RoutingDashboard />
          </div>

          {/* Quick Links Card */}
          <div className="bg-gradient-to-r from-white/10 to-white/5 backdrop-blur-sm border border-white/20 rounded-2xl p-8 shadow-xl">
            <h2 className="text-2xl font-bold text-white mb-6">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <a
                href="/providers"
                className="group bg-gradient-to-br from-emerald-500/20 to-blue-500/20 border border-white/20 rounded-xl p-6 hover:from-emerald-500/30 hover:to-blue-500/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-emerald-500/20"
              >
                <div className="flex items-center justify-center w-12 h-12 bg-white/10 rounded-xl mb-4 group-hover:bg-white/20 transition-all duration-300">
                  <Database className="w-6 h-6 text-emerald-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Manage Providers</h3>
                <p className="text-slate-300 text-sm leading-relaxed">Configure and monitor your AI model providers</p>
              </a>
              
              <a
                href="/logs"
                className="group bg-gradient-to-br from-green-500/20 to-emerald-500/20 border border-white/20 rounded-xl p-6 hover:from-green-500/30 hover:to-emerald-500/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-green-500/20"
              >
                <div className="flex items-center justify-center w-12 h-12 bg-white/10 rounded-xl mb-4 group-hover:bg-white/20 transition-all duration-300">
                  <FileText className="w-6 h-6 text-green-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">View Logs</h3>
                <p className="text-slate-300 text-sm leading-relaxed">Monitor system activity and troubleshoot issues</p>
              </a>
              
              <a
                href="/sandbox"
                className="group bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-white/20 rounded-xl p-6 hover:from-purple-500/30 hover:to-pink-500/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-purple-500/20"
              >
                <div className="flex items-center justify-center w-12 h-12 bg-white/10 rounded-xl mb-4 group-hover:bg-white/20 transition-all duration-300">
                  <Cpu className="w-6 h-6 text-purple-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Sandbox Jobs</h3>
                <p className="text-slate-300 text-sm leading-relaxed">Test and experiment with AI model configurations</p>
              </a>
              
              <a
                href="/settings"
                className="group bg-gradient-to-br from-slate-500/20 to-gray-500/20 border border-white/20 rounded-xl p-6 hover:from-slate-500/30 hover:to-gray-500/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-slate-500/20"
              >
                <div className="flex items-center justify-center w-12 h-12 bg-white/10 rounded-xl mb-4 group-hover:bg-white/20 transition-all duration-300">
                  <Settings className="w-6 h-6 text-slate-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Settings</h3>
                <p className="text-slate-300 text-sm leading-relaxed">Configure your preferences and system settings</p>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
