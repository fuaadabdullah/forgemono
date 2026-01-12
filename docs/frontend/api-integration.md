# API Integration Guide

This document describes how the frontend integrates with the backend API, including patterns, best practices, and implementation details.

## 🌐 Overview

The frontend communicates with a FastAPI backend using RESTful APIs with TypeScript interfaces for type safety. We use Axios for HTTP requests and React Query for state management and caching.

## 🏗️ Architecture

### Service Layer Pattern

We follow a service layer pattern to abstract API interactions:

```
Frontend
    ↓
Service Layer (API clients)
    ↓
HTTP Client (Axios)
    ↓
Backend API (FastAPI)
```

### Key Components

1. **API Client** (`lib/api/client-axios.ts`) - HTTP client configuration
2. **Service Layer** (`lib/api/services/`) - Business logic services
3. **React Query** (`lib/api/queries/`) - Data fetching and caching
4. **Type Definitions** (`types/api/`) - TypeScript interfaces

## 🔌 API Client Configuration

### Base Client Setup

```typescript
// lib/api/client-axios.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - add auth tokens
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors globally
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.get(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.post(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.put(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.delete(url, config);
    return response.data;
  }
}

export const apiClient = new ApiClient(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');
```

### Environment Configuration

```env
# Environment variables for API configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8000
```

## 📊 Service Layer Implementation

### Provider Service Example

```typescript
// lib/api/services/providerService.ts
import { apiClient } from '../client-axios';
import { Provider, CreateProviderRequest, UpdateProviderRequest } from '../../types/api';

class ProviderService {
  private basePath = '/api/providers';

  async getProviders(): Promise<Provider[]> {
    return apiClient.get<Provider[]>(this.basePath);
  }

  async getProvider(id: string): Promise<Provider> {
    return apiClient.get<Provider>(`${this.basePath}/${id}`);
  }

  async createProvider(data: CreateProviderRequest): Promise<Provider> {
    return apiClient.post<Provider>(this.basePath, data);
  }

  async updateProvider(id: string, data: UpdateProviderRequest): Promise<Provider> {
    return apiClient.put<Provider>(`${this.basePath}/${id}`, data);
  }

  async deleteProvider(id: string): Promise<void> {
    return apiClient.delete<void>(`${this.basePath}/${id}`);
  }

  async testProvider(id: string): Promise<{ status: string; message: string }> {
    return apiClient.post<{ status: string; message: string }>(`${this.basePath}/${id}/test`);
  }
}

export const providerService = new ProviderService();
```

### Type Definitions

```typescript
// types/api/provider.ts
export interface Provider {
  id: string;
  name: string;
  type: 'openai' | 'anthropic' | 'local' | 'ollama';
  status: 'active' | 'inactive' | 'error';
  config: ProviderConfig;
  createdAt: string;
  updatedAt: string;
}

export interface ProviderConfig {
  apiKey?: string;
  baseUrl?: string;
  model?: string;
  temperature?: number;
  maxTokens?: number;
}

export interface CreateProviderRequest {
  name: string;
  type: Provider['type'];
  config: ProviderConfig;
}

export interface UpdateProviderRequest {
  name?: string;
  status?: Provider['status'];
  config?: Partial<ProviderConfig>;
}
```

## 🔄 React Query Integration

### Query Hooks

```typescript
// lib/api/queries/providerQueries.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { providerService } from '../services/providerService';
import { Provider } from '../../types/api';

export const useProviders = () => {
  return useQuery<Provider[], Error>({
    queryKey: ['providers'],
    queryFn: () => providerService.getProviders(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useProvider = (id: string) => {
  return useQuery<Provider, Error>({
    queryKey: ['providers', id],
    queryFn: () => providerService.getProvider(id),
    enabled: !!id,
  });
};

export const useCreateProvider = () => {
  const queryClient = useQueryClient();

  return useMutation<Provider, Error, CreateProviderRequest>({
    mutationFn: (data) => providerService.createProvider(data),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['providers'] });
    },
  });
};

export const useUpdateProvider = () => {
  const queryClient = useQueryClient();

  return useMutation<Provider, Error, { id: string; data: UpdateProviderRequest }>({
    mutationFn: ({ id, data }) => providerService.updateProvider(id, data),
    onSuccess: (_, { id }) => {
      // Invalidate specific provider and list
      queryClient.invalidateQueries({ queryKey: ['providers'] });
      queryClient.invalidateQueries({ queryKey: ['providers', id] });
    },
  });
};

export const useDeleteProvider = () => {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: (id) => providerService.deleteProvider(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['providers'] });
    },
  });
};
```

### Query Provider Setup

```typescript
// lib/api/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
    mutations: {
      retry: 1,
    },
  },
});
```

## 🎯 Usage in Components

### Basic Component Usage

```tsx
// components/providers/ProviderList.tsx
import React from 'react';
import { useProviders, useDeleteProvider } from '@/lib/api/queries/providerQueries';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export function ProviderList() {
  const { data: providers, isLoading, error } = useProviders();
  const deleteProvider = useDeleteProvider();

  if (isLoading) {
    return <div>Loading providers...</div>;
  }

  if (error) {
    return <div>Error loading providers: {error.message}</div>;
  }

  return (
    <div className="space-y-4">
      {providers?.map((provider) => (
        <div key={provider.id} className="flex items-center justify-between p-4 border rounded">
          <div className="flex items-center space-x-4">
            <div>
              <h3 className="font-semibold">{provider.name}</h3>
              <p className="text-sm text-gray-600">{provider.type}</p>
            </div>
            <Badge variant={provider.status === 'active' ? 'success' : 'warning'}>
              {provider.status}
            </Badge>
          </div>
          <div className="flex space-x-2">
            <Button size="sm" variant="ghost">Edit</Button>
            <Button 
              size="sm" 
              variant="danger"
              onClick={() => deleteProvider.mutate(provider.id)}
              disabled={deleteProvider.isPending}
            >
              {deleteProvider.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
```

### Form with API Integration

```tsx
// components/providers/ProviderForm.tsx
import React, { useState } from 'react';
import { useCreateProvider } from '@/lib/api/queries/providerQueries';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { FormField } from '@/components/shared/FormField';

interface ProviderFormProps {
  onSuccess?: () => void;
}

export function ProviderForm({ onSuccess }: ProviderFormProps) {
  const [formData, setFormData] = useState({
    name: '',
    type: 'openai' as const,
    config: {
      apiKey: '',
      baseUrl: '',
      model: 'gpt-3.5-turbo',
    },
  });

  const createProvider = useCreateProvider();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createProvider.mutateAsync(formData);
      onSuccess?.();
      setFormData({
        name: '',
        type: 'openai',
        config: { apiKey: '', baseUrl: '', model: 'gpt-3.5-turbo' },
      });
    } catch (error) {
      console.error('Failed to create provider:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <FormField label="Provider Name" required>
        <Input
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="Enter provider name"
          required
        />
      </FormField>

      <FormField label="Provider Type" required>
        <select
          value={formData.type}
          onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
          className="w-full p-2 border rounded"
          required
        >
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
          <option value="local">Local</option>
          <option value="ollama">Ollama</option>
        </select>
      </FormField>

      <FormField label="API Key" required>
        <Input
          type="password"
          value={formData.config.apiKey}
          onChange={(e) => setFormData({
            ...formData,
            config: { ...formData.config, apiKey: e.target.value }
          })}
          placeholder="Enter API key"
          required
        />
      </FormField>

      <Button 
        type="submit" 
        disabled={createProvider.isPending}
      >
        {createProvider.isPending ? 'Creating...' : 'Create Provider'}
      </Button>
    </form>
  );
}
```

## 🔄 Real-time Updates with WebSockets

### WebSocket Service

```typescript
// lib/api/websocket.ts
import { EventEmitter } from 'events';

class WebSocketService extends EventEmitter {
  private socket: WebSocket | null = null;
  private url: string;

  constructor(url: string) {
    super();
    this.url = url;
  }

  connect() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return;
    }

    this.socket = new WebSocket(this.url);

    this.socket.onopen = () => {
      this.emit('connected');
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.emit('message', data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.socket.onclose = () => {
      this.emit('disconnected');
      // Attempt to reconnect after 3 seconds
      setTimeout(() => this.connect(), 3000);
    };

    this.socket.onerror = (error) => {
      this.emit('error', error);
    };
  }

  send(data: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}

export const webSocketService = new WebSocketService(
  process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8000'
);
```

### Using WebSocket in Components

```tsx
// components/providers/ProviderStatus.tsx
import React, { useEffect, useState } from 'react';
import { webSocketService } from '@/lib/api/websocket';
import { Badge } from '@/components/ui/Badge';

interface ProviderStatusProps {
  providerId: string;
}

export function ProviderStatus({ providerId }: ProviderStatusProps) {
  const [status, setStatus] = useState<'connected' | 'disconnected' | 'error'>('disconnected');

  useEffect(() => {
    const handleMessage = (data: any) => {
      if (data.type === 'provider_status' && data.providerId === providerId) {
        setStatus(data.status);
      }
    };

    webSocketService.on('message', handleMessage);

    // Request initial status
    webSocketService.send({
      type: 'get_provider_status',
      providerId,
    });

    return () => {
      webSocketService.off('message', handleMessage);
    };
  }, [providerId]);

  useEffect(() => {
    webSocketService.connect();
    return () => {
      webSocketService.disconnect();
    };
  }, []);

  return (
    <Badge variant={status === 'connected' ? 'success' : status === 'error' ? 'danger' : 'warning'}>
      {status}
    </Badge>
  );
}
```

## 🛡️ Error Handling

### Global Error Handler

```typescript
// lib/api/errorHandler.ts
import { AxiosError } from 'axios';

export interface ApiError {
  message: string;
  status?: number;
  details?: any;
}

export function handleApiError(error: unknown): ApiError {
  if (error instanceof AxiosError) {
    const status = error.response?.status;
    const message = error.response?.data?.message || error.message || 'An error occurred';
    const details = error.response?.data?.details;

    return {
      message,
      status,
      details,
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message || 'An unexpected error occurred',
    };
  }

  return {
    message: 'An unknown error occurred',
  };
}
```

### Error Boundary Integration

```tsx
// components/ErrorBoundary.tsx
import React, { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-600">Something went wrong</h1>
            <p className="text-gray-600 mt-2">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: undefined })}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

## 📝 API Documentation

### OpenAPI Integration

```typescript
// lib/api/openapi.ts
import { OpenAPI } from 'openapi-typescript-fetch';

// Configure OpenAPI client
OpenAPI.BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
OpenAPI.WITH_CREDENTIALS = true;

// Configure authentication
OpenAPI.interceptors.push({
  onRequest: (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
});

// Generate types from OpenAPI spec
export const api = OpenAPI;
```

### API Mocking for Development

```typescript
// lib/api/mock.ts
import { MockedFunction, vi } from 'vitest';

// Mock API responses for development/testing
export const mockApi = {
  providers: {
    get: vi.fn().mockResolvedValue([
      { id: '1', name: 'OpenAI', type: 'openai', status: 'active' },
      { id: '2', name: 'Anthropic', type: 'anthropic', status: 'active' },
    ]),
    create: vi.fn().mockResolvedValue({ id: '3', name: 'Test Provider', type: 'openai', status: 'active' }),
  },
};
```

## 🚀 Performance Optimization

### Request Caching

```typescript
// lib/api/cache.ts
import { QueryClient } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      gcTime: 15 * 60 * 1000, // 15 minutes
    },
  },
});

// Prefetch data
export const prefetchProvider = (id: string) => {
  queryClient.prefetchQuery({
    queryKey: ['providers', id],
    queryFn: () => providerService.getProvider(id),
  });
};
```

### Request Deduplication

```typescript
// lib/api/deduplicate.ts
import { QueryClient } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 0, // Always consider data stale
      gcTime: 1000, // Garbage collect immediately
    },
  },
});
```

## 🧪 Testing API Integration

### Mocking API Calls

```tsx
// components/providers/ProviderList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useProviders } from '@/lib/api/queries/providerQueries';
import { ProviderList } from './ProviderList';

// Mock the API hook
jest.mock('@/lib/api/queries/providerQueries', () => ({
  useProviders: jest.fn(),
}));

const mockUseProviders = useProviders as jest.MockedFunction<typeof useProviders>;

describe('ProviderList', () => {
  const queryClient = new QueryClient();

  beforeEach(() => {
    mockUseProviders.mockReturnValue({
      data: [
        { id: '1', name: 'OpenAI', type: 'openai', status: 'active' },
        { id: '2', name: 'Anthropic', type: 'anthropic', status: 'active' },
      ],
      isLoading: false,
      error: null,
    });
  });

  it('renders provider list', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ProviderList />
      </QueryClientProvider>
    );

    expect(screen.getByText('OpenAI')).toBeInTheDocument();
    expect(screen.getByText('Anthropic')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockUseProviders.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <ProviderList />
      </QueryClientProvider>
    );

    expect(screen.getByText('Loading providers...')).toBeInTheDocument();
  });
});
```

## 📚 Best Practices

### 1. Type Safety

- Always define TypeScript interfaces for API responses
- Use strict typing for all API interactions
- Validate API responses at runtime in development

### 2. Error Handling

- Implement global error handling for API calls
- Provide user-friendly error messages
- Log errors for debugging purposes

### 3. Caching Strategy

- Use appropriate cache times based on data volatility
- Implement cache invalidation when data changes
- Prefetch data for better user experience

### 4. Performance

- Implement request deduplication
- Use pagination for large datasets
- Consider virtualization for long lists

### 5. Security

- Never expose sensitive data in API responses
- Implement proper authentication and authorization
- Validate all input data on the backend

## 🔗 Additional Resources

- [Axios Documentation](https://axios-http.com/docs/intro)
- [React Query Documentation](https://tanstack.com/query/v4/docs/react/overview)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [OpenAPI Specification](https://swagger.io/specification/)
