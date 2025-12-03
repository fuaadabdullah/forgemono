interface LoginHeaderProps {
  isRegister: boolean;
}

export default function LoginHeader({ isRegister }: LoginHeaderProps) {
  return (
    <div className="text-center mb-8">
      <div className="flex items-center justify-center mb-4">
        <span className="text-5xl">🤖</span>
      </div>
      <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-primary via-accent to-primary mb-3">
        GoblinOS Assistant
      </h1>
      <h2 className="text-2xl font-bold text-text mb-2">
        {isRegister ? 'Create Account' : 'Welcome Back'}
      </h2>
      <p className="text-muted">
        {isRegister
          ? 'Sign up to access intelligent development automation'
          : 'Sign in to continue your automation journey'}
      </p>
    </div>
  );
}
