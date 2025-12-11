import React from 'react';
import { ErrorTestingPanel } from '@/components/ErrorTestingPanel';
import Layout from '@/components/Layout';

const ErrorTestingPage: React.FC = () => {
  return (
    <Layout>
      <div className="container mx-auto py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Error Testing & Datadog Validation
          </h1>
          <p className="text-gray-600">
            Test Datadog RUM error tracking by generating various types of errors.
            This page is for development and testing purposes only.
          </p>
        </div>

        <ErrorTestingPanel />
      </div>
    </Layout>
  );
};

export default ErrorTestingPage;
