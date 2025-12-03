import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import App from './App.tsx'
import './index.css'
import { queryClient } from './lib/queryClient'

console.log('🚀 main.tsx loading...');
console.log('API Base URL:', import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001');

try {
  const rootElement = document.getElementById('root');
  console.log('Root element found:', rootElement);

  if (!rootElement) {
    throw new Error('Root element not found!');
  }

  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </React.StrictMode>,
  );
  console.log('✅ React app rendered successfully');
} catch (error) {
  console.error('❌ Failed to render React app:', error);
  document.body.innerHTML = `
    <div style="padding: 20px; font-family: monospace;">
      <h1 style="color: red;">Failed to load app</h1>
      <pre>${error}</pre>
    </div>
  `;
}
