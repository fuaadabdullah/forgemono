import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

// Define request handlers for your API endpoints
export const handlers = [
  // Health check endpoint
  http.get('http://127.0.0.1:8000/health', () => {
    return HttpResponse.json({ status: 'healthy' });
  }),

  // Execute task endpoint
  http.post('http://127.0.0.1:8000/execute/mock-task-123', () => {
    return HttpResponse.json({
      status: 'completed',
      result: 'Mock streaming task completed',
      tokenCount: 150,
      costDelta: 0.002,
    });
  }),

  // Streaming endpoint
  http.get('http://127.0.0.1:8000/execute/mock-task-123/stream', () => {
    return HttpResponse.json({
      chunk:
        '{"chunk":"Executed: streaming task completed","result":"success","tokenCount":150,"costDelta":0.002}',
      stepId: 'step1',
      chunkPreview: '{"chunk":"Executed: streaming task completed","res...',
      tokenCount: undefined,
      costDelta: undefined,
    });
  }),
];

// Setup the MSW server
export const server = setupServer(...handlers);
