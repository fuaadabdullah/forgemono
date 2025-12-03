import { useState, useEffect } from 'react';
import { apiClient } from '../api/client-axios';
import TwoColumnLayout from '../components/TwoColumnLayout';

interface SandboxJob {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  code_snippet?: string;
  language?: string;
}

/**
 * Sandbox Runner: Upload/run code, view logs, and artifacts
 */
const SandboxPage = () => {
  const [jobs, setJobs] = useState<SandboxJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<SandboxJob | null>(null);
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [logs, setLogs] = useState<string>('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    try {
      const data = await apiClient.getSandboxJobs();
      setJobs(data);
    } catch (error) {
      console.error('Failed to load sandbox jobs:', error);
    }
  };

  const handleRunCode = async () => {
    setLoading(true);
    try {
      // Simulate sandbox execution
      // In real implementation: await apiClient.runSandboxCode({ code, language });
      await new Promise(resolve => setTimeout(resolve, 2000));
      setLogs('Code executed successfully!\nOutput:\nHello from sandbox');
      loadJobs();
    } catch (error) {
      setLogs(`Error: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const loadJobLogs = async (jobId: string) => {
    try {
      const logData = await apiClient.getJobLogs(jobId);
      setLogs(JSON.stringify(logData, null, 2));
    } catch (error) {
      setLogs(`Failed to load logs: ${error}`);
    }
  };

  const sidebar = (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-text mb-3">Sandbox</h2>
        <p className="text-xs text-muted mb-4">
          Execute code in isolated environments
        </p>
      </div>

      {/* Language Selector */}
      <div>
        <label className="block text-xs font-medium text-text mb-2">
          Language
        </label>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-surface-hover focus:ring-2 focus:ring-primary"
        >
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
          <option value="typescript">TypeScript</option>
          <option value="bash">Bash</option>
        </select>
      </div>

      {/* Quick Actions */}
      <div className="space-y-2">
        <button
          onClick={handleRunCode}
          disabled={!code || loading}
          className="w-full px-3 py-2 text-sm font-medium text-text-inverse bg-success rounded-lg hover:bg-success/90 disabled:bg-surface-hover disabled:cursor-not-allowed transition-colors shadow-glow-primary"
        >
          {loading ? '⚡ Running...' : '▶️ Run Code'}
        </button>
        <button
          onClick={() => setCode('')}
          className="w-full px-3 py-2 text-sm font-medium text-text bg-surface-hover rounded-lg hover:bg-surface-active transition-colors"
        >
          🗑️ Clear
        </button>
        <button
          onClick={loadJobs}
          className="w-full px-3 py-2 text-sm font-medium text-primary bg-primary/20 rounded-lg hover:bg-primary/30 transition-colors"
        >
          🔄 Refresh Jobs
        </button>
      </div>

      {/* Recent Jobs */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold text-text uppercase tracking-wide">
          Recent Jobs
        </h3>
        {jobs.length > 0 ? (
          jobs.slice(0, 10).map((job) => (
            <button
              key={job.id}
              onClick={() => {
                setSelectedJob(job);
                loadJobLogs(job.id);
              }}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors ${
                selectedJob?.id === job.id
                  ? 'bg-primary/20 text-primary border border-primary'
                  : 'bg-surface border border-border text-text hover:bg-surface-hover'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono">{job.id.substring(0, 8)}</span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  job.status === 'completed' ? 'bg-success/20 text-success' :
                  job.status === 'failed' ? 'bg-danger/20 text-danger' :
                  job.status === 'running' ? 'bg-info/20 text-info' :
                  'bg-surface-hover text-muted'
                }`}>
                  {job.status}
                </span>
              </div>
              <div className="text-xs text-muted">
                {new Date(job.created_at).toLocaleString()}
              </div>
            </button>
          ))
        ) : (
          <div className="text-xs text-muted">No jobs yet</div>
        )}
      </div>
    </div>
  );

  const mainContent = (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-text mb-2">Sandbox Runner</h1>
        <p className="text-muted">
          Execute code in isolated environments with real-time logs and artifacts
        </p>
      </div>

      {/* Code Editor */}
      <div className="bg-surface rounded-xl shadow-sm border border-border p-6">
        <h2 className="text-lg font-semibold text-text mb-4">Code Editor</h2>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder={`Enter your ${language} code here...`}
          className="w-full h-64 px-4 py-3 font-mono text-sm border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent resize-none bg-bg"
        />
        <div className="mt-4 text-xs text-muted">
          <span className="font-medium">Language:</span> {language} |
          <span className="ml-2 font-medium">Lines:</span> {code.split('\n').length}
        </div>
      </div>

      {/* Logs/Output */}
      <div className="bg-surface rounded-xl shadow-sm border border-border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-text">Output & Logs</h2>
          {selectedJob && (
            <span className="text-sm text-muted">
              Job: <span className="font-mono">{selectedJob.id.substring(0, 8)}</span>
            </span>
          )}
        </div>
        <div className="bg-bg text-primary font-mono text-xs p-4 rounded-lg h-64 overflow-y-auto">
          {logs || 'No output yet. Run code to see results.'}
        </div>
      </div>

      {/* Artifacts (if any) */}
      {selectedJob && (
        <div className="bg-surface rounded-xl shadow-sm border border-border p-6">
          <h2 className="text-lg font-semibold text-text mb-4">Artifacts</h2>
          <div className="text-sm text-muted">
            No artifacts generated for this job.
          </div>
        </div>
      )}
    </div>
  );

  return <TwoColumnLayout sidebar={sidebar}>{mainContent}</TwoColumnLayout>;
};

export default SandboxPage;
