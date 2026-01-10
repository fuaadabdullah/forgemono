import React from 'react';
import { Button } from '../ui';

interface Props {
  onJavaScriptError: () => void;
  onTypeError: () => void;
  onCustomError: () => void;
  onAsyncError: () => void;
  onNetworkError: () => void;
  onUnhandledPromiseRejection: () => void;
  onSentryError: () => void;
  onSentryMessage: () => void;
  onSentryBreadcrumb: () => void;
  onRunAll: () => void;
  running: boolean;
}

export const ErrorTestButtons: React.FC<Props> = ({
  onJavaScriptError,
  onTypeError,
  onCustomError,
  onAsyncError,
  onNetworkError,
  onUnhandledPromiseRejection,
  onSentryError,
  onSentryMessage,
  onSentryBreadcrumb,
  onRunAll,
  running,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Button onClick={onJavaScriptError} variant="danger" className="w-full">
        Test JavaScript Error
      </Button>

      <Button onClick={onTypeError} variant="danger" className="w-full">
        Test Type Error
      </Button>

      <Button onClick={onCustomError} variant="danger" className="w-full">
        Test Custom Error
      </Button>

      <Button onClick={onAsyncError} variant="danger" className="w-full">
        Test Async Error
      </Button>

      <Button onClick={onNetworkError} variant="danger" className="w-full">
        Test Network Error
      </Button>

      <Button onClick={onUnhandledPromiseRejection} variant="danger" className="w-full">
        Test Unhandled Promise
      </Button>

      <Button onClick={onSentryError} variant="ghost" className="w-full">
        Test Sentry Error
      </Button>

      <Button onClick={onSentryMessage} variant="ghost" className="w-full">
        Test Sentry Message
      </Button>

      <Button onClick={onSentryBreadcrumb} variant="ghost" className="w-full">
        Test Sentry Breadcrumb
      </Button>

      <Button onClick={onRunAll} disabled={running} className="flex-1 md:col-span-2">
        {running ? 'Running Tests...' : 'Run All Error Tests'}
      </Button>
    </div>
  );
};
