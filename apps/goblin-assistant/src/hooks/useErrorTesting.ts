import { useState } from 'react';
import { sentryErrorTracking } from '../utils/sentry';

class CustomError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CustomError';
  }
}

export const useErrorTesting = (showSuccess: (message: string) => void) => {
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<string[]>([]);

  const addResult = (message: string) => {
    setResults((prev) => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const testJavaScriptError = () => {
    try {
      // This will throw a ReferenceError — intentionally use a non-existing variable
      // @ts-ignore: intentionally reference a non-declared variable to emulate runtime RT error
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      nonExistentVariable();
    } catch (error) {
      addResult(`JavaScript Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      throw error; // Re-throw for global capture
    }
  };

  const testAsyncError = async () => {
    try {
      await new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Async operation failed')), 100);
      });
    } catch (error) {
      addResult(`Async Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      throw error;
    }
  };

  const testNetworkError = async () => {
    try {
      const response = await fetch('https://httpstat.us/500');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      addResult(`Network Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      throw error;
    }
  };

  const testUnhandledPromiseRejection = () => {
    // Create an unhandled promise rejection — note that we intentionally don't handle it
    Promise.reject(new Error('Unhandled promise rejection test'));
    addResult('Unhandled promise rejection created');
  };

  const testTypeError = () => {
    try {
      const testObject: any = null;
      // This will throw a TypeError
      // eslint-disable-next-line @typescript-eslint/no-unused-expressions
      testObject.someProperty;
    } catch (error) {
      addResult(`Type Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      throw error;
    }
  };

  const testCustomError = () => {
    try {
      throw new CustomError('This is a custom error for testing');
    } catch (error) {
      addResult(`Custom Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      throw error;
    }
  };

  const testSentryError = () => {
    try {
      const error = new Error('Sentry test error - should appear in RUM via Sentry intake');
      sentryErrorTracking.captureException(error, {
        testType: 'sentry-direct',
        component: 'ErrorTestingPanel',
        timestamp: new Date().toISOString(),
      });
      addResult('Sentry error captured successfully');
    } catch (error) {
      addResult(
        `Sentry error test failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  };

  const testSentryMessage = () => {
    try {
      sentryErrorTracking.captureMessage('Test message from Sentry to RUM', 'warning', {
        testType: 'sentry-message',
        component: 'ErrorTestingPanel',
        severity: 'warning',
      });
      addResult('Sentry message captured successfully');
    } catch (error) {
      addResult(
        `Sentry message test failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  };

  const testSentryBreadcrumb = () => {
    try {
      sentryErrorTracking.addBreadcrumb('User clicked error test button', 'user-action', 'info');
      sentryErrorTracking.captureMessage('Breadcrumb test completed', 'info', {
        testType: 'sentry-breadcrumb',
      });
      addResult('Sentry breadcrumb added successfully');
    } catch (error) {
      addResult(
        `Sentry breadcrumb test failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  };

  const runAllTests = async () => {
    setIsLoading(true);
    setResults([]);

    const tests = [
      { name: 'JavaScript Error', fn: testJavaScriptError },
      { name: 'Type Error', fn: testTypeError },
      { name: 'Custom Error', fn: testCustomError },
      { name: 'Unhandled Promise', fn: testUnhandledPromiseRejection },
      { name: 'Sentry Error', fn: testSentryError },
      { name: 'Sentry Message', fn: testSentryMessage },
      { name: 'Sentry Breadcrumb', fn: testSentryBreadcrumb },
    ];

    for (const test of tests) {
      try {
        if (test.name.startsWith('Sentry')) {
          test.fn();
        } else {
          // ensure awaited when required
          await (test.fn as () => Promise<void>)();
        }
      } catch (error) {
        // Expected — the tests intentionally may throw to simulate capture
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }

    // Run async and network tests separately
    try {
      await testAsyncError();
    } catch (error) {
      // expected
    }

    try {
      await testNetworkError();
    } catch (error) {
      // expected
    }

    setIsLoading(false);
    showSuccess('Error testing completed! Check RUM dashboard for captured errors.');
  };

  const clearResults = () => {
    setResults([]);
  };

  return {
    isLoading,
    results,
    testJavaScriptError,
    testAsyncError,
    testNetworkError,
    testUnhandledPromiseRejection,
    testTypeError,
    testCustomError,
    testSentryError,
    testSentryMessage,
    testSentryBreadcrumb,
    runAllTests,
    clearResults,
  };
};
