"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui';
import { Badge } from '@/components/ui/Badge';
import { 
  Play, 
  Trash2, 
  Code, 
  Terminal, 
  CheckCircle, 
  XCircle, 
  Loader,
  Copy,
  AlertTriangle
} from 'lucide-react';

interface ExecutionResult {
  success: boolean;
  output?: string;
  error?: string;
  executionTime?: number;
}

const EXAMPLE_CODES = [
  {
    name: 'Hello World',
    code: 'print("Hello from Goblin Sandbox!")',
  },
  {
    name: 'Math Operations',
    code: 'result = 2 + 2\nprint(f"2 + 2 = {result}")\nprint(f"10 * 5 = {10 * 5}")',
  },
  {
    name: 'Fibonacci Sequence',
    code: `def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        print(a, end=" ")
        a, b = b, a + b
    print()

fibonacci(10)`,
  },
  {
    name: 'List Comprehension',
    code: `squares = [x**2 for x in range(10)]
print("Squares:", squares)
evens = [x for x in range(20) if x % 2 == 0]
print("Evens:", evens)`,
  },
];

export default function SandboxPage() {
  const [code, setCode] = useState('print("Hello World!")');
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  const executeCode = async () => {
    setIsExecuting(true);
    setResult(null);

    try {
      const startTime = Date.now();
      // Use relative URL - proxied through Next.js rewrites to backend
      const response = await fetch('/execute/code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      });

      const executionTime = Date.now() - startTime;
      const data = await response.json();

      if (response.ok) {
        setResult({
          success: true,
          output: data.output || data.result || 'Code executed successfully',
          executionTime,
        });
      } else {
        setResult({
          success: false,
          error: data.error || data.detail || 'Execution failed',
          executionTime,
        });
      }
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : 'Network error occurred',
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const loadExample = (exampleCode: string) => {
    setCode(exampleCode);
    setResult(null);
  };

  const clearCode = () => {
    setCode('');
    setResult(null);
  };

  const copyOutput = () => {
    if (result?.output) {
      navigator.clipboard.writeText(result.output);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-8 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
              <Code className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Python Sandbox</h1>
              <p className="text-slate-300">Execute Python code safely in an isolated environment</p>
            </div>
          </div>
          <Badge variant="secondary" className="text-sm px-4 py-2 bg-green-500/20 text-green-400 border-green-500/30">
            <CheckCircle className="w-4 h-4 mr-2" />
            Live
          </Badge>
        </div>

        {/* Security Notice */}
        <div className="mt-4 bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-amber-200 text-sm font-semibold">Security Notice</p>
            <p className="text-amber-300/80 text-sm mt-1">
              The sandbox blocks dangerous operations (os, subprocess, file I/O) and enforces a 30-second timeout.
              Perfect for testing algorithms and data processing.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Code Editor Section */}
        <div className="lg:col-span-2 space-y-4">
          {/* Editor */}
          <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Terminal className="w-5 h-5" />
                Code Editor
              </h2>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearCode}
                  disabled={isExecuting}
                  className="border-white/30 text-white hover:bg-white/10"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Clear
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={executeCode}
                  disabled={isExecuting || !code.trim()}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold"
                >
                  {isExecuting ? (
                    <>
                      <Loader className="w-4 h-4 mr-2 animate-spin" />
                      Executing...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Run Code
                    </>
                  )}
                </Button>
              </div>
            </div>

            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              disabled={isExecuting}
              className="w-full h-96 bg-slate-900 text-green-400 font-mono text-sm p-4 rounded-xl border border-white/20 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
              placeholder="# Enter your Python code here&#10;print('Hello, Goblin!')"
              spellCheck={false}
            />
          </div>

          {/* Output */}
          {result && (
            <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  {result.success ? (
                    <>
                      <CheckCircle className="w-5 h-5 text-green-400" />
                      Output
                    </>
                  ) : (
                    <>
                      <XCircle className="w-5 h-5 text-red-400" />
                      Error
                    </>
                  )}
                </h2>
                <div className="flex items-center gap-3">
                  {result.executionTime && (
                    <span className="text-slate-300 text-sm">
                      {result.executionTime}ms
                    </span>
                  )}
                  {result.output && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={copyOutput}
                      className="text-white hover:bg-white/10"
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>

              <pre
                className={`w-full bg-slate-900 font-mono text-sm p-4 rounded-xl border overflow-x-auto ${
                  result.success
                    ? 'text-green-400 border-green-500/30'
                    : 'text-red-400 border-red-500/30'
                }`}
              >
                {result.success ? result.output : result.error}
              </pre>
            </div>
          )}
        </div>

        {/* Examples Sidebar */}
        <div className="space-y-4">
          <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 shadow-xl">
            <h2 className="text-xl font-bold text-white mb-4">Examples</h2>
            <div className="space-y-3">
              {EXAMPLE_CODES.map((example, index) => (
                <button
                  key={index}
                  onClick={() => loadExample(example.code)}
                  disabled={isExecuting}
                  className="w-full text-left bg-slate-800/50 hover:bg-slate-700/50 border border-white/10 rounded-lg p-4 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-white font-medium">{example.name}</span>
                    <Code className="w-4 h-4 text-purple-400 group-hover:text-purple-300 transition-colors" />
                  </div>
                  <p className="text-slate-400 text-xs mt-2 font-mono truncate">
                    {example.code.split('\n')[0]}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Info Card */}
          <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 shadow-xl">
            <h3 className="text-lg font-bold text-white mb-3">Sandbox Limits</h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                <span>Standard library available</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                <span>30 second timeout</span>
              </li>
              <li className="flex items-start gap-2">
                <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <span>No file system access</span>
              </li>
              <li className="flex items-start gap-2">
                <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <span>No network operations</span>
              </li>
              <li className="flex items-start gap-2">
                <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <span>No subprocess execution</span>
              </li>
            </ul>
          </div>

          {/* API Info */}
          <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 shadow-xl">
            <h3 className="text-lg font-bold text-white mb-3">API Endpoint</h3>
            <div className="space-y-2">
              <div className="bg-slate-900 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-1">POST</p>
                <code className="text-sm text-purple-400 break-all">
                  https://goblin-backend.fly.dev/execute/code
                </code>
              </div>
              <p className="text-xs text-slate-300 mt-2">
                Send Python code in the request body to execute it remotely.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
