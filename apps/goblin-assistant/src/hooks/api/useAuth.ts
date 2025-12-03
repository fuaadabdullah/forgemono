import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../api/client-axios';
import { useAuthStore } from '../../store/authStore';

/**
 * Hook for user registration
 */
export const useRegister = () => {
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      apiClient.register(email, password),
    onSuccess: (data) => {
      setAuth(data.access_token, { email: '' }); // You can extract user from JWT if needed
    },
  });
};

/**
 * Hook for user login
 */
export const useLogin = () => {
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      apiClient.login(email, password),
    onSuccess: (data) => {
      setAuth(data.access_token, { email: '' });
    },
  });
};

/**
 * Hook for user logout
 */
export const useLogout = () => {
  const clearAuth = useAuthStore((state) => state.clearAuth);

  return useMutation({
    mutationFn: () => apiClient.logout(),
    onSuccess: () => {
      clearAuth();
    },
  });
};

/**
 * Hook for Google OAuth
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
 */
export const usePasskeyAuth = () => {
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: ({ email, assertion }: { email: string; assertion: any }) =>
      apiClient.passkeyAuth(email, assertion),
    onSuccess: (data) => {
      setAuth(data.access_token, { email: '' });
    },
  });
};
