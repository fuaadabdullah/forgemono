import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '../../api/client-axios';
import { queryKeys } from '../../lib/queryClient';

/**
 * Hook to fetch available chat models
 */
export const useChatModels = () => {
  return useQuery({
    queryKey: queryKeys.models,
    queryFn: () => apiClient.getAvailableModels(),
  });
};

/**
 * Hook to fetch routing information
 */
export const useRoutingInfo = () => {
  return useQuery({
    queryKey: queryKeys.routingInfo,
    queryFn: () => apiClient.getRoutingInfo(),
  });
};

/**
 * Hook to send a chat completion request
 */
export const useChatCompletion = () => {
  return useMutation({
    mutationFn: ({
      messages,
      model,
      stream,
    }: {
      messages: any[];
      model?: string;
      stream?: boolean;
    }) => apiClient.chatCompletion(messages, model, stream),
  });
};
