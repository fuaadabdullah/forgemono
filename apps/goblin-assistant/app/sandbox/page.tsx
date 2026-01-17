"use client";

import React, { useState, useEffect, useRef } from 'react';
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
  AlertTriangle,
  ChevronLeft,
  Sparkles,
  BookOpen,
  History,
  Save
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

interface ExecutionResult {
  success: boolean;
  output?: {
    stdout: string;
    stderr: string;
    truncated: boolean;
    truncation_reason?: string;
  };
  execution_time?: number;
  error_class?: string;
  timestamp?: Date;
}

interface SavedSnippet {
  id: string;
  name: string;
  code: string;
  createdAt: Date;
}

const EXAMPLE_CODES = [
  {
    name: 'Hello World',
    description: 'Simple print statement',
    code: 'print("Hello from Goblin Sandbox!")',
  },
  {
    name: 'Math Operations',
    description: 'Basic arithmetic',
    code: 'result = 2 + 2\nprint(f"2 + 2 = {result}")\nprint(f"10 * 5 = {10 * 5}")',
  },
  {
    name: 'Fibonacci Sequence',
    description: 'Generate Fibonacci numbers',
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
    description: 'Working with lists',
    code: `squares = [x**2 for x in range(10)]
print("Squares:", squares)
evens = [x for x in range(20) if x % 2 == 0]
print("Evens:", evens)`,
  },
  {
    name: 'Dictionary Operations',
    description: 'Working with dictionaries',
    code: `person = {"name": "Goblin", "age": 25, "city": "Cloud"}
print("Person:", person)
for key, value in person.items():
    print(f"{key}: {value}")`,
  },
  {
    name: 'String Manipulation',
    description: 'String methods',
    code: `text = "Python Sandbox"
print("Upper:", text.upper())
print("Lower:", text.lower())
print("Split:", text.split())
print("Reversed:", text[::-1])`,
  },
];

export default function SandboxPage() {
  const router = useRouter();
  const [code, setCode] = useState('print("Hello World!")');
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionHistory, setExecutionHistory] = useState<ExecutionResult[]>([]);
  const [savedSnippets, setSavedSnippets] = useState<SavedSnippet[]>([]);
  const [showExamples, setShowExamples] = useState(true);
  const [showHistory, setShowHistory] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load saved snippets from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('goblin_sandbox_snippets');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          setSavedSnippets(parsed.map((s: any) => ({
            ...s,
            createdAt: new Date(s.createdAt)
          })));
        } catch (error) {
          console.error('Failed to load saved snippets:', error);
        }
      }

      const history = localStorage.getItem('goblin_sandbox_history');
      if (history) {
        try {
          const parsed = JSON.parse(history);
          setExecutionHistory(parsed.map((h: any) => ({
            ...h,
            timestamp: new Date(h.timestamp)
          })));
        } catch (error) {
          console.error('Failed to load history:', error);
        }
      }
    }
  }, []);

  // Save execution history to localStorage
  useEffect(() => {
    if (executionHistory.length > 0 && typeof window !== 'undefined') {
      localStorage.setItem('goblin_sandbox_history', JSON.stringify(executionHistory));
    }
  }, [executionHistory]);

  const executeCode = async () => {
    setIsExecuting(true);
    setResult(null);

    try {
      const startTime = Date.now();
      // Use relative URL - proxied through Next.js rewrites to backend
      const response = await fetch('/v1/execute/code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          code,
          capabilities: {
            allow_math: true,
            allow_random: true,
            allow_datetime: true,
            allow_json: true,
            allow_re: true,
            allow_itertools: true,
            allow_collections: true,
          }
        }),
      });

      const executionTime = Date.now() - startTime;
      const data = await response.json();

      const newResult: ExecutionResult = {
        success: response.ok,
        output: response.ok 
          ? (data.output || { stdout: 'Code executed successfully', stderr: '', truncated: false })
          : { stdout: '', stderr: data.detail || 'Execution failed', truncated: false },
        execution_time: data.execution_time || executionTime / 1000,
        error_class: data.error_class,
        timestamp: new Date(),
      };

      setResult(newResult);
      
      // Add to history (keep last 10)
      setExecutionHistory((prev: ExecutionResult[]) => [newResult, ...prev].slice(0, 10));
    } catch (error) {
      const errorResult: ExecutionResult = {
        success: false,
        output: {
          stdout: '',
          stderr: error instanceof Error ? error.message : 'Network error occurred',
          truncated: false,
        },
        error_class: 'network',
        timestamp: new Date(),
      };
      setResult(errorResult);
      setExecutionHistory((prev: ExecutionResult[]) => [errorResult, ...prev].slice(0, 10));
    } finally {
      setIsExecuting(false);
    }
  };

  const loadExample = (exampleCode: string) => {
    setCode(exampleCode);
    setResult(null);
    textareaRef.current?.focus();
  };

  const clearCode = () => {
    setCode('');
    setResult(null);
    textareaRef.current?.focus();
  };

  const copyOutput = () => {
    if (result?.output) {
      navigator.clipboard.writeText(result.output);
    }
  };

  const saveSnippet = () => {
    const name = prompt('Enter a name for this snippet:');
    if (name && code.trim()) {
      const newSnippet: SavedSnippet = {
        id: Date.now().toString(),
        name,
        code,
        createdAt: new Date(),
      };
      const updated = [newSnippet, ...savedSnippets];
      setSavedSnippets(updated);
      localStorage.setItem('goblin_sandbox_snippets', JSON.stringify(updated));
    }
  };

  const loadSnippet = (snippet: SavedSnippet) => {
    setCode(snippet.code);
    setResult(null);
  };

  const deleteSnippet = (id: string) => {
    const updated = savedSnippets.filter((s: SavedSnippet) => s.id !== id);
    setSavedSnippets(updated);
    localStorage.setItem('goblin_sandbox_snippets', JSON.stringify(updated));
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + Enter: Execute code
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (code.trim() && !isExecuting) {
          executeCode();
        }
      }
      // Ctrl/Cmd + S: Save snippet
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveSnippet();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [code, isExecuting]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-white/10 bg-white/5 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push('/chat')}
                className="text-white hover:bg-white/10"
              >
                <ChevronLeft className="w-4 h-4 mr-2" />
                Back to Chat
              </Button>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                  <Code className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">Python Sandbox</h1>
                  <p className="text-xs text-slate-300">Test your Python code safely</p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="secondary" className="text-sm bg-green-500/20 text-green-400 border-green-500/30">
                <CheckCircle className="w-3 h-3 mr-1" />
                Live
              </Badge>
              <LanguageSwitcher />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Info Banner */}
        <div className="mb-6 bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-white font-semibold mb-1">Safe Python Execution</h3>
              <p className="text-slate-300 text-sm">
                Run Python code in a secure sandbox environment. Standard library available, 30-second timeout.
                Press <kbd className="px-2 py-0.5 bg-white/10 rounded text-xs">Ctrl+Enter</kbd> to execute.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-4">
            {/* Tab Switcher */}
            <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-2 flex gap-2">
              <button
                onClick={() => {
                  setShowExamples(true);
                  setShowHistory(false);
                }}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  showExamples
                    ? 'bg-white/20 text-white'
                    : 'text-slate-300 hover:bg-white/10'
                }`}
              >
                <BookOpen className="w-4 h-4 inline mr-2" />
                Examples
              </button>
              <button
                onClick={() => {
                  setShowExamples(false);
                  setShowHistory(true);
                }}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  showHistory
                    ? 'bg-white/20 text-white'
                    : 'text-slate-300 hover:bg-white/10'
                }`}
              >
                <History className="w-4 h-4 inline mr-2" />
                History
              </button>
            </div>

            {/* Examples Tab */}
            {showExamples && (
              <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-4 max-h-[calc(100vh-16rem)] overflow-y-auto">
                <h2 className="text-lg font-bold text-white mb-3">Code Examples</h2>
                <div className="space-y-2">
                  {EXAMPLE_CODES.map((example, index) => (
                    <button
                      key={index}
                      onClick={() => loadExample(example.code)}
                      disabled={isExecuting}
                      className="w-full text-left bg-slate-800/50 hover:bg-slate-700/50 border border-white/10 rounded-lg p-3 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <span className="text-white font-medium text-sm block truncate">
                            {example.name}
                          </span>
                          <p className="text-slate-400 text-xs mt-1 truncate">
                            {example.description}
                          </p>
                        </div>
                        <Code className="w-4 h-4 text-purple-400 group-hover:text-purple-300 transition-colors flex-shrink-0" />
                      </div>
                    </button>
                  ))}
                </div>

                {/* Saved Snippets */}
                {savedSnippets.length > 0 && (
                  <>
                    <h3 className="text-md font-bold text-white mb-3 mt-6">Saved Snippets</h3>
                    <div className="space-y-2">
                      {savedSnippets.map((snippet) => (
                        <div
                          key={snippet.id}
                          className="bg-slate-800/50 border border-white/10 rounded-lg p-3"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-white font-medium text-sm truncate">
                              {snippet.name}
                            </span>
                            <button
                              onClick={() => deleteSnippet(snippet.id)}
                              className="text-red-400 hover:text-red-300 transition-colors"
                            >
                              <XCircle className="w-4 h-4" />
                            </button>
                          </div>
                          <button
                            onClick={() => loadSnippet(snippet)}
                            className="w-full text-left text-xs text-slate-400 hover:text-slate-300 font-mono truncate"
                          >
                            {snippet.code.split('\n')[0]}
                          </button>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}

            {/* History Tab */}
            {showHistory && (
              <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-4 max-h-[calc(100vh-16rem)] overflow-y-auto">
                <h2 className="text-lg font-bold text-white mb-3">Execution History</h2>
                {executionHistory.length === 0 ? (
                  <p className="text-slate-400 text-sm">No execution history yet</p>
                ) : (
                  <div className="space-y-2">
                    {executionHistory.map((item, index) => (
                      <div
                        key={index}
                        className={`border rounded-lg p-3 ${
                          item.success
                            ? 'bg-green-500/10 border-green-500/30'
                            : 'bg-red-500/10 border-red-500/30'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          {item.success ? (
                            <CheckCircle className="w-4 h-4 text-green-400" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-400" />
                          )}
                          <span className="text-xs text-slate-400">
                            {item.executionTime}ms
                          </span>
                        </div>
                        <pre className="text-xs font-mono text-slate-300 overflow-x-auto">
                          {item.success
                            ? item.output?.substring(0, 100)
                            : item.error?.substring(0, 100)}
                        </pre>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Limits Info */}
            <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 backdrop-blur-sm border border-white/20 rounded-xl p-4">
              <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                Sandbox Limits
              </h3>
              <ul className="space-y-1.5 text-xs text-slate-300">
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-3 h-3 text-green-400 flex-shrink-0 mt-0.5" />
                  <span>Standard library available</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle className="w-3 h-3 text-green-400 flex-shrink-0 mt-0.5" />
                  <span>30 second timeout</span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="w-3 h-3 text-red-400 flex-shrink-0 mt-0.5" />
                  <span>No file system access</span>
                </li>
                <li className="flex items-start gap-2">
                  <XCircle className="w-3 h-3 text-red-400 flex-shrink-0 mt-0.5" />
                  <span>No network operations</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Main Editor Area */}
          <div className="lg:col-span-3 space-y-4">
            {/* Code Editor */}
            <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Terminal className="w-5 h-5" />
                  Code Editor
                </h2>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={saveSnippet}
                    disabled={isExecuting || !code.trim()}
                    className="border-white/30 text-white hover:bg-white/10"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Save
                  </Button>
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
                ref={textareaRef}
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
              <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-6 shadow-xl">
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
                      <Badge variant="secondary" className="text-xs">
                        {result.executionTime.toFixed(0)}ms
                      </Badge>
                    )}
                    {result.errorClass && (
                      <Badge variant="destructive" className="text-xs">
                        {result.errorClass}
                      </Badge>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={copyOutput}
                      className="text-white hover:bg-white/10"
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* Stdout - Success Output */}
                {result.output?.stdout && (
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-green-400 mb-2">Output</h3>
                    <pre className="w-full bg-slate-900 text-green-400 font-mono text-sm p-4 rounded-xl border border-green-500/30 overflow-x-auto max-h-96">
                      {result.output.stdout}
                    </pre>
                  </div>
                )}

                {/* Stderr - Error Output */}
                {result.output?.stderr && (
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-red-400 mb-2 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      Error
                    </h3>
                    <pre className="w-full bg-slate-900 text-red-400 font-mono text-sm p-4 rounded-xl border border-red-500/30 overflow-x-auto max-h-96">
                      {result.output.stderr}
                    </pre>
                    
                    {/* Explain Error Button */}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        router.push(`/chat?context=${encodeURIComponent(
                          `I got this Python error in the sandbox:\n\n${result.output.stderr}\n\nCan you explain what this means and how to fix it?`
                        )}`);
                      }}
                      className="mt-2 border-red-500/30 text-red-300 hover:bg-red-500/10"
                    >
                      <Sparkles className="w-4 h-4 mr-2" />
                      Explain this error
                    </Button>
                  </div>
                )}

                {/* Truncation Warning */}
                {result.output?.truncated && (
                  <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
                    <p className="text-amber-300 text-sm flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      ⚠️ Output was truncated: {result.output.truncationReason}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
