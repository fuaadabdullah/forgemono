import { useState } from 'react';
import { apiClient } from '../../api/client-axios';
import { useAuthStore } from '../../store/authStore';
import LoginHeader from './LoginHeader';
import EmailPasswordForm from './EmailPasswordForm';
import SocialLoginButtons from './SocialLoginButtons';
import Divider from './Divider';
import PasskeyPanel from './PasskeyPanel';
import TurnstileWidget from '../TurnstileWidget';

interface ModularLoginFormProps {
  onSuccess: () => void;
  // eslint-disable-next-line no-unused-vars
  onError: (message: string) => void;
}

export default function ModularLoginForm({
  onSuccess,
  onError,
}: ModularLoginFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [showPasskey, setShowPasskey] = useState(false);
  const [email, setEmail] = useState('');
  const [turnstileToken, setTurnstileToken] = useState('');

  const handleEmailPasswordSubmit = async (email: string, password: string) => {
    setEmail(email); // Store for passkey

    // Temporarily disabled turnstile verification for backend compatibility
    // TODO: Re-enable when backend implements turnstile verification
    // if (!turnstileToken) {
    //   onError('Please complete the security verification');
    //   return;
    // }

    setIsLoading(true);

    try {
      const response = isRegister
        ? await apiClient.register(email, password, turnstileToken)
        : await apiClient.login(email, password);

      // Store token in both localStorage and Zustand
      localStorage.setItem('auth_token', response.access_token);
      useAuthStore.getState().setAuth(response.access_token, { email });
      onSuccess();
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Authentication failed');
      // Reset Turnstile on error
      setTurnstileToken('');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      const { url } = await apiClient.getGoogleAuthUrl();
      window.location.href = url;
    } catch (error) {
      onError('Failed to initiate Google login');
    }
  };

  return (
    <div className="w-full max-w-md">
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
        <LoginHeader isRegister={isRegister} />

        <EmailPasswordForm
          onSubmit={handleEmailPasswordSubmit}
          isRegister={isRegister}
          isLoading={isLoading}
        />

        {/* Turnstile Bot Protection */}
        <div className="mt-4">
          <TurnstileWidget
            siteKey={import.meta.env.VITE_TURNSTILE_SITE_KEY_MANAGED}
            onVerify={(token) => setTurnstileToken(token)}
            mode="managed"
            theme="auto"
            size="normal"
            onError={(error) => {
              console.error('Turnstile verification failed:', error);
              onError('Security verification failed. Please try again.');
            }}
          />
        </div>

        <Divider text="Or continue with" />

        <SocialLoginButtons
          onGoogleLogin={handleGoogleLogin}
          isLoading={isLoading}
        />

        <div className="mt-6 space-y-3">
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="w-full text-center text-indigo-600 hover:text-indigo-700 text-sm font-medium transition-colors"
            type="button"
          >
            {isRegister
              ? 'Already have an account? Sign in'
              : "Don't have an account? Sign up"}
          </button>

          <button
            onClick={() => setShowPasskey(!showPasskey)}
            className="w-full text-center text-purple-600 hover:text-purple-700 text-sm font-medium transition-colors"
            type="button"
          >
            {showPasskey ? 'Hide Passkey Options' : '🔐 Use Passkey (WebAuthn)'}
          </button>
        </div>

        {showPasskey && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <PasskeyPanel
              email={email}
              onError={onError}
              onSuccess={onSuccess}
            />
          </div>
        )}
      </div>

      <p className="text-xs text-center text-gray-500 mt-6">
        By signing in you agree to telemetry collection for performance and
        anomaly detection.
      </p>
    </div>
  );
}
