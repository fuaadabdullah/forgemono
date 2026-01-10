import StatusCard from '../StatusCard';

interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'down' | 'unknown';
  lastCheck: string;
  latencyData: number[];
  errors: { timestamp: string; message: string }[];
  metrics: { label: string; value: string | number }[];
}

interface StatusCardsGridProps {
  backend: ServiceHealth;
  chroma: ServiceHealth;
  mcp: ServiceHealth;
  rag: ServiceHealth;
  sandbox: ServiceHealth;
}

/**
 * Grid of status cards for all services
 */
export function StatusCardsGrid({ backend, chroma, mcp, rag, sandbox }: StatusCardsGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 mb-6">
      <StatusCard
        title="Backend API"
        status={backend.status}
        lastCheck={backend.lastCheck}
        meta={backend.metrics}
      />

      <StatusCard
        title="Vector DB (Chroma)"
        status={chroma.status}
        lastCheck={chroma.lastCheck}
        meta={chroma.metrics}
      />

      <StatusCard
        title="MCP Servers"
        status={mcp.status}
        lastCheck={mcp.lastCheck}
        meta={mcp.metrics}
      />

      <StatusCard
        title="RAG Indexer"
        status={rag.status}
        lastCheck={rag.lastCheck}
        meta={rag.metrics}
      />

      <StatusCard
        title="Sandbox Runner"
        status={sandbox.status}
        lastCheck={sandbox.lastCheck}
        meta={sandbox.metrics}
      />
    </div>
  );
}
