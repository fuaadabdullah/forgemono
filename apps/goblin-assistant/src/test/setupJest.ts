import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import React from 'react';

console.log('setupJest.ts loaded - jest-dom imported');

// jest runs in Node environment, setup global mocks and cleanup
afterEach(() => {
  cleanup();
  jest.clearAllMocks();
  jest.clearAllTimers();
});

// Mock environment variables
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
});

// Mock ResizeObserver
(global as any).ResizeObserver = class ResizeObserver {
  constructor(_cb: ResizeObserverCallback) {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock IntersectionObserver
(global as any).IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Polyfills for Node.js environment
import { TextEncoder, TextDecoder } from 'util';
(global as any).TextEncoder = TextEncoder;
(global as any).TextDecoder = TextDecoder;

// Mock fetch API with a simple implementation for basic testing
(global as any).fetch = jest.fn((input: string | URL | Request) => {
  const url = typeof input === 'string' ? input : input.toString();

  // Mock different endpoints
  if (url.includes('/health')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ status: 'healthy' }),
      text: () => Promise.resolve('{"status":"healthy"}'),
    });
  }
  if (url.includes('/execute/')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          status: 'completed',
          result: 'Task completed successfully',
        }),
      text: () => Promise.resolve('{"status":"completed","result":"Task completed successfully"}'),
    });
  }
  // Default response
  return Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve('{}'),
  });
});

// Mock XMLHttpRequest for libraries that might use it
(global as any).XMLHttpRequest = jest.fn(() => ({
  open: jest.fn(),
  send: jest.fn(),
  setRequestHeader: jest.fn(),
  getResponseHeader: jest.fn(),
  getAllResponseHeaders: jest.fn(),
  abort: jest.fn(),
  readyState: 4,
  status: 200,
  statusText: 'OK',
  responseText: '',
  response: null,
  onload: null,
  onerror: null,
  onreadystatechange: null,
}));

// Mock clipboard API
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: jest.fn().mockResolvedValue(undefined),
  },
  writable: true,
});

// Centralized mocks for 3rd-party UI libraries that ship ESM/CJS bundles which can
// cause node environment issues in Jest (like displayName being undefined). We mock
// these here to avoid per-test boilerplate and to stabilize rendering in unit tests.
// These are intentionally minimal and only implement shape + forwarding refs where
// components are expected within the app UI.
/* eslint-disable @typescript-eslint/no-explicit-any */
jest.mock('@radix-ui/react-select', () => {
  const React = require('react');

  const RadixSelectContext = React.createContext({ value: undefined });

  const Root = ({ value, children, onValueChange, ...props }: any) =>
    React.createElement(
      RadixSelectContext.Provider,
      { value: { value } },
      React.createElement('div', { 'data-value': value, ...props }, children)
    );

  const Trigger = React.forwardRef(({ className, children, ...props }: any, ref: any) =>
    React.createElement('button', { role: 'combobox', ref, className, ...props }, children)
  );

  const Value = ({ placeholder, children, ...props }: any) => {
    const ctx = React.useContext(RadixSelectContext);
    const text = ctx?.value ?? children ?? placeholder ?? '';
    return React.createElement('div', props, text);
  };

  const forward = (tag = 'div') =>
    React.forwardRef((props: any, ref: any) =>
      React.createElement(tag, { ...props, ref }, props.children)
    );

  const Icon = ({ asChild, children }: any) =>
    asChild ? children : React.createElement('span', null, children);

  const ScrollUpButton = React.forwardRef((props: any, ref: any) =>
    React.createElement('button', { ...props, ref }, props.children)
  );
  const ScrollDownButton = React.forwardRef((props: any, ref: any) =>
    React.createElement('button', { ...props, ref }, props.children)
  );

  return {
    Root,
    Group: forward('div'),
    Value,
    Trigger,
    Icon,
    ScrollUpButton,
    ScrollDownButton,
    Content: forward('div'),
    Portal: ({ children }: any) => React.createElement(React.Fragment, null, children),
    Viewport: forward('div'),
    Label: React.forwardRef((props: any, ref: any) =>
      React.createElement('label', { ...props, ref }, props.children)
    ),
    Item: React.forwardRef((props: any, ref: any) =>
      React.createElement('div', { ...props, ref }, props.children)
    ),
    ItemIndicator: (props: any) => React.createElement('span', props, props.children),
    ItemText: (props: any) => React.createElement('div', props, props.children),
    Separator: (props: any) => React.createElement('hr', props),
  };
});

jest.mock('lucide-react', () => {
  const React = require('react');
  const Icon = ({ className, children, ...props }: any) =>
    React.createElement('svg', { className, ...props }, children);
  return {
    Check: Icon,
    ChevronDown: Icon,
    ChevronUp: Icon,
  };
});

// Minimal mock for react-query - returning noop hooks used in the codebase to avoid
// library runtime issues during unit testing. Tests can override this mock per-suite
// when they require actual behavior.
jest.mock('@tanstack/react-query', () => ({
  useQuery: () => ({ data: undefined, isLoading: false, error: undefined }),
  useMutation: () => ({ mutate: () => {} }),
  QueryClient: function () {},
  QueryClientProvider: ({ children }: any) => children,
}));

// Mock zustand to avoid React import issues in Node environment
jest.mock('zustand', () => ({
  create: jest.fn(() => jest.fn()),
  createStore: jest.fn(() => ({
    getState: jest.fn(),
    setState: jest.fn(),
    subscribe: jest.fn(),
    destroy: jest.fn(),
  })),
}));

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  BrowserRouter: ({ children }: any) => React.createElement('div', null, children),
  Routes: ({ children }: any) => React.createElement('div', null, children),
  Route: () => null,
  Link: ({ children, to, ...props }: any) =>
    React.createElement('a', { href: to, ...props }, children),
  useNavigate: () => jest.fn(),
  useLocation: () => ({ pathname: '/', search: '', hash: '', state: null }),
  useParams: () => ({}),
}));

// Mock fetch API
global.fetch = jest.fn();

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn(),
};
global.sessionStorage = sessionStorageMock;
