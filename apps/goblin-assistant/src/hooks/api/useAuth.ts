import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client-axios';
import { useAuthStore } from '../../store/authStore';
import { LoginRequest, RefreshTokenRequest, RevokeSessionRequest } from '../../types/api';

/**
 * Hook for user registration
 * Returns mutation result - components should handle state updates
 */
export const useRegister = () => {
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      apiClient.register(email, password),
  });
};

/**
 * Hook for user login
 * Returns mutation result - components should handle state updates
 */
export const useLogin = () => {
  const { setAuth } = useAuthStore();

  return useMutation({
    mutationFn: (data: LoginRequest) => apiClient.login(data),
    onSuccess: (response) => {
      setAuth(response.user);
    },
  });
};

/**
 * Hook for token refresh
 * Returns mutation result - components should handle state updates
 */
export const useRefreshToken = () => {
  const { updateLastRefresh } = useAuthStore();

  return useMutation({
    mutationFn: (data: RefreshTokenRequest) => apiClient.refreshToken(data),
    onSuccess: () => {
      updateLastRefresh();
    },
  });
};

/**
 * Hook for getting user sessions
 * Returns query result with sessions data
 */
export const useSessions = () => {
  const { setSessions } = useAuthStore();

  return useQuery({
    queryKey: ['auth', 'sessions'],
    queryFn: () => apiClient.getSessions(),
    onSuccess: (response) => {
      setSessions(response.sessions);
    },
    enabled: useAuthStore.getState().isAuthenticated,
  });
};

/**
 * Hook for revoking a user session
 * Returns mutation result
 */
export const useRevokeSession = () => {
  const queryClient = useQueryClient();
  const { removeSession } = useAuthStore();

  return useMutation({
    mutationFn: (data: RevokeSessionRequest) => apiClient.revokeSession(data),
    onSuccess: (_, variables) => {
      removeSession(variables.session_id);
      queryClient.invalidateQueries({ queryKey: ['auth', 'sessions'] });
    },
  });
};

/**
 * Hook for emergency logout (revoke all sessions)
 * Returns mutation result
 */
export const useEmergencyLogout = () => {
  const { clearAuth } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiClient.emergencyLogout(),
    onSuccess: () => {
      clearAuth();
      queryClient.clear();
    },
  });
};

/**
 * Hook for user logout
 * Returns mutation result - components should handle state updates
 */
export const useLogout = () => {
  const { clearAuth } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => apiClient.logout(),
    onSuccess: () => {
      clearAuth();
      queryClient.clear();
    },
  });
};

/**
 * Hook for Google OAuth
 * Returns mutation result - components should handle redirects
 */
export const useGoogleAuth = () => {
  return useMutation({
    mutationFn: () => apiClient.getGoogleAuthUrl(),
    onSuccess: (data) => {
      window.location.href = data.url;
    },
  });
};

/**
 * Hook for passkey authentication
 * Returns mutation result - components should handle state updates
 */
export const usePasskeyAuth = () => {
  const { setAuth } = useAuthStore();

  return useMutation({
    mutationFn: ({ email, assertion }: { email: string; assertion: unknown }) =>
      apiClient.passkeyAuth(email, assertion),
    onSuccess: (response) => {
      setAuth(response.user);
    },
  });
};
