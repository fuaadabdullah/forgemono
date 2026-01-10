import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface Props {
  results: string[];
}

export const ErrorTestResults: React.FC<Props> = ({ results }) => {
  if (!results || results.length === 0) return null;

  return (
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
  );
};
