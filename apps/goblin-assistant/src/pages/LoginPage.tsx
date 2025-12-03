import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ModularLoginForm from '../components/Auth/ModularLoginForm';

export default function LoginPage() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const handleSuccess = () => {
    setError(null);
    navigate('/');
  };

  const handleError = (message: string) => {
    setError(message);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-accent/10 to-cta/10 px-4">
      <div className="w-full max-w-md">
        {error && (
          <div className="mb-4 p-4 bg-surface border border-danger text-danger rounded-lg text-sm flex items-start gap-2">
            <span className="text-lg">⚠️</span>
            <div>
              <p className="font-semibold">Authentication Error</p>
              <p className="text-xs mt-1">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-danger hover:text-danger/80"
              type="button"
              aria-label="Dismiss error"
            >
              ✕
            </button>
          </div>
        )}

        <ModularLoginForm onSuccess={handleSuccess} onError={handleError} />
      </div>
    </div>
  );
}
