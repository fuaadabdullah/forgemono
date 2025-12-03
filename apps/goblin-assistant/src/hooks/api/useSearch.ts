import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client-axios';
import { queryKeys } from '../../lib/queryClient';

/**
 * Hook to fetch all collections
 */
export const useCollections = () => {
  return useQuery({
    queryKey: queryKeys.collections,
    queryFn: () => apiClient.getCollections(),
  });
};

/**
 * Hook to create a new collection
 */
export const useCreateCollection = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ name, description }: { name: string; description?: string }) =>
      apiClient.createCollection(name, description),
    onSuccess: () => {
      // Invalidate collections list to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.collections });
    },
  });
};

/**
 * Hook to search documents
 */
export const useSearchDocuments = () => {
  return useMutation({
    mutationFn: ({
      collectionId,
      query,
      limit,
    }: {
      collectionId: number;
      query: string;
      limit?: number;
    }) => apiClient.searchDocuments(collectionId, query, limit),
  });
};

/**
 * Hook to index a new document
 */
export const useIndexDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      collectionId,
      content,
      metadata,
    }: {
      collectionId: number;
      content: string;
      metadata?: any;
    }) => apiClient.indexDocument(collectionId, content, metadata),
    onSuccess: (_, variables) => {
      // Invalidate documents for this collection
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents(variables.collectionId),
      });
    },
  });
};
