import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/contexts/ToastContext';
import { sentryErrorTracking } from '@/utils/sentry';

class CustomError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CustomError';
  }
}

export const ErrorTestingPanel: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<string[]>([]);
  const { showSuccess } = useToast();

  const addResult = (message: string) => {
    setResults(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const testJavaScriptError = () => {
    try {
      // This will throw a ReferenceError
      console.log(nonExistentVariable);
    } catch (error) {
      addResult(`JavaScript Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      throw error; // Re-throw so Datadog can catch it
    }
  };

  const testAsyncError = async () => {
    try {
      // Simulate an async error
      await new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Async operation failed')), 100);
      });
    } catch (error) {
      addResult(`Async Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      throw error; // Re-throw for Datadog
    }
  };

  const testNetworkError = async () => {
    try {
      // Try to fetch from a non-existent endpoint
      const response = await fetch('https://httpstat.us/500');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      addResult(`Network Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      throw error; // Re-throw for Datadog
    }
  };

  const testUnhandledPromiseRejection = () => {
    // Create an unhandled promise rejection
    Promise.reject(new Error('Unhandled promise rejection test')).catch(() => {
      // Intentionally don't handle it to test unhandled rejections
      addResult('Unhandled promise rejection created');
    });
  };

  const testTypeError = () => {
    try {
      // This will throw a TypeError
      const obj = null;
      obj.someProperty; // TypeError: Cannot read property 'someProperty' of null
    } catch (error) {
      addResult(`Type Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      throw error; // Re-throw for Datadog
    }
  };

  const testCustomError = () => {
    try {
      throw new CustomError('This is a custom error for testing');
    } catch (error) {
      addResult(`Custom Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      throw error; // Re-throw for Datadog
    }
  };

  const testSentryError = () => {
    try {
      // Test Sentry error capture
      const error = new Error('Sentry test error - should appear in Datadog via Sentry intake');
      sentryErrorTracking.captureException(error, {
        testType: 'sentry-direct',
        component: 'ErrorTestingPanel',
        timestamp: new Date().toISOString(),
      });
      addResult('Sentry error captured successfully');
    } catch (error) {
      addResult(`Sentry error test failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const testSentryMessage = () => {
    try {
      // Test Sentry message capture
      sentryErrorTracking.captureMessage('Test message from Sentry to Datadog', 'warning', {
        testType: 'sentry-message',
        component: 'ErrorTestingPanel',
        severity: 'warning',
      });
      addResult('Sentry message captured successfully');
    } catch (error) {
      addResult(`Sentry message test failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const testSentryBreadcrumb = () => {
    try {
      // Test Sentry breadcrumb
      sentryErrorTracking.addBreadcrumb('User clicked error test button', 'user-action', 'info');
      sentryErrorTracking.captureMessage('Breadcrumb test completed', 'info', {
        testType: 'sentry-breadcrumb',
      });
      addResult('Sentry breadcrumb added successfully');
    } catch (error) {
      addResult(`Sentry breadcrumb test failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
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
        if (test.name === 'Sentry Error' || test.name === 'Sentry Message' || test.name === 'Sentry Breadcrumb') {
          test.fn();
        } else {
          await test.fn();
        }
      } catch (error) {
        // Errors are expected and handled above
      }
      await new Promise(resolve => setTimeout(resolve, 500)); // Small delay between tests
    }

    // Test async and network errors separately
    try {
      await testAsyncError();
    } catch (error) {
      // Expected
    }

    try {
      await testNetworkError();
    } catch (error) {
      // Expected
    }

    setIsLoading(false);
    showSuccess('Error testing completed! Check Datadog dashboard for captured errors.');
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>Datadog Error Testing Panel</CardTitle>
        <CardDescription>
          Generate various types of errors to test Datadog RUM error tracking.
          All errors will be captured and sent to your Datadog dashboard.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert>
          <AlertDescription>
            ⚠️ This panel is for testing purposes only. It will intentionally generate errors
            that should appear in your Datadog RUM dashboard.
          </AlertDescription>
        </Alert>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Button
            onClick={testJavaScriptError}
            variant="destructive"
            className="w-full"
          >
            Test JavaScript Error
          </Button>

          <Button
            onClick={testTypeError}
            variant="destructive"
            className="w-full"
          >
            Test Type Error
          </Button>

          <Button
            onClick={testCustomError}
            variant="destructive"
            className="w-full"
          >
            Test Custom Error
          </Button>

          <Button
            onClick={testAsyncError}
            variant="destructive"
            className="w-full"
          >
            Test Async Error
          </Button>

          <Button
            onClick={testNetworkError}
            variant="destructive"
            className="w-full"
          >
            Test Network Error
          </Button>

          <Button
            onClick={testUnhandledPromiseRejection}
            variant="destructive"
            className="w-full"
          >
            Test Unhandled Promise
          </Button>

          <Button
            onClick={testSentryError}
            variant="outline"
            className="w-full"
          >
            Test Sentry Error
          </Button>

          <Button
            onClick={testSentryMessage}
            variant="outline"
            className="w-full"
          >
            Test Sentry Message
          </Button>

          <Button
            onClick={testSentryBreadcrumb}
            variant="outline"
            className="w-full"
          >
            Test Sentry Breadcrumb
          </Button>
        </div>

        <div className="flex gap-4">
          <Button
            onClick={runAllTests}
            disabled={isLoading}
            className="flex-1"
          >
            {isLoading ? 'Running Tests...' : 'Run All Error Tests'}
          </Button>

          <Button
            onClick={() => setResults([])}
            variant="outline"
          >
            Clear Results
          </Button>
        </div>

        {results.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Test Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {results.map((result, index) => (
                  <div key={index} className="text-sm font-mono bg-gray-100 p-2 rounded">
                    {result}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        <Alert>
          <AlertDescription>
            📊 After running tests, check your Datadog RUM dashboard under &quot;Error Tracking&quot;
            to see if the errors were captured. Look for errors with source &quot;browser&quot; and
            check the error details and stack traces.
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
};
