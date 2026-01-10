import React from 'react';

interface CostStreamingProps {
  streaming: boolean;
  streamLines: string[];
}

export const CostStreaming: React.FC<CostStreamingProps> = ({ streaming, streamLines }) => {
  if (!streaming || streamLines.length === 0) return null;

  return (
    <div className="streaming-output">
      <h5>Streaming Output (live)</h5>
      <div className="stream-lines">
        {streamLines.map((line, i) => (
          <div key={`stream-${i}`} className="stream-line">
            {line}
          </div>
        ))}
      </div>
    </div>
  );
};
