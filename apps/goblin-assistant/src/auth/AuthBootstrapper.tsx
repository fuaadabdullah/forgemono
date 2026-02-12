import { useEffect } from 'react';
import { useAuthStore } from '../store/authStore';

/**
 * Hydrates auth state from localStorage/cookies on the client.
 * Middleware remains the routing gate; this is for client state only.
 */
export default function AuthBootstrapper() {
  const bootstrapFromSession = useAuthStore(state => state.bootstrapFromSession);

  useEffect(() => {
    bootstrapFromSession().catch(() => {
      // Errors are handled inside the store; avoid unhandled promise noise.
    });
  }, [bootstrapFromSession]);

  return null;
}

