import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import TaskExecution from './components/TaskExecution';
import Orchestration from './components/Orchestration';
import Settings from './pages/SettingsPage';
import Search from './pages/SearchPage';
import Navigation from './components/Navigation';
import { apiClient } from './api/client';

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    // Check backend health on app load
    const checkHealth = async () => {
      try {
        const healthData = await apiClient.getHealth();
        setHealth(healthData);
      } catch (error) {
        console.error('Failed to connect to backend:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkHealth();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Connecting to GoblinOS Assistant...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-900 text-white">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/execute" element={<TaskExecution />} />
            <Route path="/orchestrate" element={<Orchestration />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/search" element={<Search />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
