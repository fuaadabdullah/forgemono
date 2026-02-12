# Code Citations

## License: unknown
<https://github.com/laitanop/TodoList/blob/6988314aba3466f2e38bd7e5ac4369a5ff86a91a/src/Services/Auth.ts>

```
export const signUp = async (email: string, password: string) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  });
  return { data, error };
};

export const signIn = async (email: string, password: string) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });
  return { data, error };
};

export const signOut = async () => {
  const { error } = await supabase.auth.signOut();
```

