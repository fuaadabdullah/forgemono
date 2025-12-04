import React, { useState, useEffect } from 'react';
import { useCollections, useSearchDocuments } from '../hooks/api/useSearch';

interface SearchResult {
  id: string;
  document: string;
  metadata?: Record<string, any>;
  distance?: number;
}

interface SearchResponse {
  results: SearchResult[];
  total_results: number;
}

const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedCollection, setSelectedCollection] = useState<string>('');

  // React Query hooks
  const { data: collectionsData, isLoading: collectionsLoading } = useCollections();
  const { mutateAsync: searchDocuments, isPending: searching } = useSearchDocuments();

  // Initialize selected collection when data arrives
  useEffect(() => {
    if (collectionsData && collectionsData.length > 0 && !selectedCollection) {
      // Assume apiClient returns array of { id, name }
      const first = collectionsData[0];
      const name = typeof first === 'string' ? first : (first.name || '');
      setSelectedCollection(name);
    }
  }, [collectionsData, selectedCollection]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !selectedCollection) return;
    setError(null);
    try {
      // We need a collectionId; if collectionsData items are objects use their id, else fallback to name mapping
      let collectionId: number | undefined;
      if (collectionsData) {
        const match = collectionsData.find((c: any) => (typeof c === 'string' ? c === selectedCollection : c.name === selectedCollection));
        if (match && typeof match === 'object') collectionId = match.id;
      }
      // If no numeric id, bail with message (backend mismatch)
      if (collectionId === undefined) {
        // Fallback: query directly via temporary fetch until api supports name-based searchDocuments
        const IS_VERCEL = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app');
        const baseUrl = IS_VERCEL ? '' : (import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:8001');
        const response = await fetch(`${baseUrl}/search/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: query.trim(),
            collection_name: selectedCollection,
            n_results: 20,
          }),
        });
        if (!response.ok) throw new Error(`Search failed: ${response.statusText}`);
        const data: SearchResponse = await response.json();
        setResults(data.results);
        return;
      }
      const searchResponse = await searchDocuments({ collectionId, query: query.trim(), limit: 20 });
      // Assume apiClient.searchDocuments returns { results }
      const out = (searchResponse as any)?.results || [];
      setResults(out);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setResults([]);
    }
  };

  return (
    <div className="min-h-screen bg-bg py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-primary mb-3">RAG Search</h1>
          <p className="text-muted">
            Search through your document collection using vector similarity
          </p>
        </div>

        {/* Search Form */}
        <div className="bg-surface rounded-xl shadow-sm border border-border p-8 mb-8">
          <form onSubmit={handleSearch} className="space-y-6">
            <div>
              <label htmlFor="query" className="block text-sm font-medium text-text mb-2">
                Search Query
              </label>
              <input
                id="query"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your search query..."
                className="w-full px-4 py-3 border border-border bg-surface-hover rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-text placeholder-muted"
                disabled={searching}
              />
            </div>
            <div>
              <label htmlFor="collection" className="block text-sm font-medium text-text mb-2">
                Collection
              </label>
              <select
                id="collection"
                value={selectedCollection}
                onChange={(e) => setSelectedCollection(e.target.value)}
                className="w-full px-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-surface-hover text-text"
                disabled={collectionsLoading || searching}
              >
                {(collectionsData || []).map((c: any) => {
                  const name = typeof c === 'string' ? c : c.name;
                  return (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  );
                })}
              </select>
            </div>
            <button
              type="submit"
              disabled={searching || !query.trim() || !selectedCollection}
              className="w-full bg-primary text-text-inverse py-3 px-6 rounded-lg hover:brightness-110 focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-glow-primary transition-all flex items-center justify-center gap-2"
            >
              {searching ? (
                <>
                  <span className="animate-spin">🔄</span>
                  Searching...
                </>
              ) : (
                <>
                  <span>🔍</span>
                  Search Documents
                </>
              )}
            </button>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-surface border-2 border-danger rounded-lg p-4 mb-6 text-center">
            <p className="text-danger">{error}</p>
          </div>
        )}

        {/* Empty State */}
  {!query && !searching && results.length === 0 && (
          <div className="text-center py-16">
            <div className="w-20 h-20 bg-surface-hover rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">🔍</span>
            </div>
            <h3 className="text-lg font-medium text-text mb-2">Search your documents</h3>
            <p className="text-muted">
              Enter a query above to search through your vector database.
            </p>
          </div>
        )}

        {/* No Results */}
  {!searching && !error && results.length === 0 && query && (
          <div className="text-center py-16">
            <div className="w-20 h-20 bg-surface-hover rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">📄</span>
            </div>
            <h3 className="text-lg font-medium text-text mb-2">No results found</h3>
            <p className="text-muted">
              Try adjusting your search query or check if documents are indexed in the selected collection.
            </p>
          </div>
        )}

        {/* Results */}
        {results.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-text mb-4">
              Search Results ({results.length})
            </h2>
            {results.map((result, index) => (
              <div
                key={result.id}
                className="bg-surface rounded-lg shadow-sm border border-border p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">📄</span>
                    <span className="text-sm font-medium text-text">
                      Document {index + 1}
                    </span>
                  </div>
                  {result.distance !== undefined && (
                    <span className="text-xs text-muted bg-surface-hover px-2 py-1 rounded">
                      Distance: {result.distance.toFixed(4)}
                    </span>
                  )}
                </div>
                <p className="text-text mb-4 leading-relaxed">
                  {result.document}
                </p>
                {result.metadata && Object.keys(result.metadata).length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(result.metadata).map(([key, value]) => (
                      <span
                        key={key}
                        className="inline-flex items-center px-3 py-1 rounded-full text-xs bg-primary/20 text-primary font-medium"
                      >
                        {key}: {String(value)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchPage;
