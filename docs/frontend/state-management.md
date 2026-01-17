# State Management Guide

This document describes the state management patterns and best practices used in the GoblinOS Assistant frontend application.

## 🎯 State Management Overview

We use a hybrid state management approach combining **React Query** for server state and **Zustand** for client state. This provides clear separation of concerns and optimal performance.

## 📦 State Management Architecture

```
┌─────────────────────────────────────────┐
│           React Components              │
├─────────────────────────────────────────┤
│  ┌─────────────────┐  ┌────────────────┐ │
│  │   React Query   │  │    Zustand     │ │
│  │   (Server)      │  │   (Client)     │ │
│  │   - API Data    │  │   - UI State   │ │
│  │   - Caching     │  │   - User Prefs │ │
│  │   - Sync        │  │   - Auth       │ │
│  └─────────────────┘  └────────────────┘ │
├─────────────────────────────────────────┤
│           Backend API                   │
└─────────────────────────────────────────┘
```

## 🔧 Zustand - Client State

### When to Use Zustand

Use Zustand for client-side state that doesn't need synchronization with a backend:

- **UI State**: Modal open/close, loading states, form state
- **User Preferences**: Theme, language, settings
- **Authentication**: User session, permissions
- **Local Caching**: Non-critical data that can be lost

### Store Creation

```typescript
// stores/userStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UserState {
  user: User | null;
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  setUser: (user: User | null) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSidebar: () => void;
  logout: () => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set, get) => ({
      user: null,
      theme: 'light',
      sidebarOpen: false,
      
      setUser: (user) => set({ user }),
      
      setTheme: (theme) => {
        // Apply theme to document
        if (theme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
        
        set({ theme });
      },
      
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      
      logout: () => set({ user: null, sidebarOpen: false }),
    }),
    {
      name: 'user-storage',
      partialize: (state) => ({
        user: state.user,
        theme: state.theme,
      }),
    }
  )
);
```

### Usage in Components

```tsx
// components/Header.tsx
import React from 'react';
import { useUserStore } from '@/stores/userStore';
import { Button } from '@/components/ui/Button';

export function Header() {
  const { user, theme, setTheme, logout } = useUserStore();

  return (
    <header className="bg-white dark:bg-gray-800 shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              GoblinOS Assistant
            </h1>
          </div>
          
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </Button>
            
            {user ? (
              <>
                <span className="text-gray-700 dark:text-gray-200">
                  Welcome, {user.name}
                </span>
                <Button onClick={logout} variant="danger">
                  Logout
                </Button>
              </>
            ) : (
              <Button href="/login">Login</Button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
```

### Advanced Zustand Patterns

#### Middleware

```typescript
// stores/middleware.ts
import { StateCreator } from 'zustand';

// Logger middleware
export const logger =
  (f: StateCreator<any>): StateCreator<any> =>
  (set, get, api) =>
    f((args) => {
      console.log('State update:', args);
      set(args);
      console.log('New state:', get());
    }, get, api);

// Immer middleware for immutable updates
import { produce } from 'immer';

export const withImmer =
  (f: StateCreator<any>): StateCreator<any> =>
  (set, get, api) =>
    f((fn) => set(produce(fn)), get, api);
```

#### Derived State

```typescript
// stores/calculatorStore.ts
interface CalculatorState {
  numbers: number[];
  sum: number;
  average: number;
  addNumber: (num: number) => void;
  removeNumber: (index: number) => void;
}

export const useCalculatorStore = create<CalculatorState>((set, get) => ({
  numbers: [],
  
  get sum() {
    return get().numbers.reduce((acc, num) => acc + num, 0);
  },
  
  get average() {
    const numbers = get().numbers;
    return numbers.length > 0 ? numbers.reduce((acc, num) => acc + num, 0) / numbers.length : 0;
  },
  
  addNumber: (num) => set((state) => ({ numbers: [...state.numbers, num] })),
  
  removeNumber: (index) => set((state) => ({
    numbers: state.numbers.filter((_, i) => i !== index)
  })),
}));
```

#### Async Actions

```typescript
// stores/asyncStore.ts
interface AsyncState {
  data: any[];
  loading: boolean;
  error: string | null;
  fetchData: () => Promise<void>;
}

export const useAsyncStore = create<AsyncState>((set) => ({
  data: [],
  loading: false,
  error: null,
  
  fetchData: async () => {
    set({ loading: true, error: null });
    
    try {
      const response = await fetch('/api/data');
      const data = await response.json();
      set({ data, loading: false });
    } catch (error) {
      set({ error: 'Failed to fetch data', loading: false });
    }
  },
}));
```

## 🔄 React Query - Server State

### When to Use React Query

Use React Query for server state that needs synchronization:

- **API Data**: User data, settings, dynamic content
- **Caching**: Automatic caching and background updates
- **Background Sync**: Keep data fresh without manual refresh
- **Optimistic Updates**: Immediate UI feedback
- **Error Handling**: Built-in retry and error management

### Query Hooks

```typescript
// lib/api/queries/userQueries.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client-axios';

export const useUsers = () => {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => apiClient.get('/api/users'),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useUser = (id: string) => {
  return useQuery({
    queryKey: ['users', id],
    queryFn: () => apiClient.get(`/api/users/${id}`),
    enabled: !!id,
  });
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (userData) => apiClient.post('/api/users', userData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};
```

### Mutations with Optimistic Updates

```tsx
// components/UserList.tsx
import React from 'react';
import { useUsers, useUpdateUser, useDeleteUser } from '@/lib/api/queries/userQueries';
import { Button } from '@/components/ui/Button';

export function UserList() {
  const { data: users, isLoading } = useUsers();
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  const handleToggleActive = async (user: User) => {
    // Optimistic update
    const previousUsers = users;
    
    // Update cache optimistically
    queryClient.setQueryData(['users'], (old: User[]) =>
      old.map((u) => (u.id === user.id ? { ...u, active: !u.active } : u))
    );

    try {
      await updateUser.mutateAsync({ id: user.id, active: !user.active });
    } catch (error) {
      // Rollback on error
      queryClient.setQueryData(['users'], previousUsers);
      console.error('Failed to update user:', error);
    }
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="space-y-4">
      {users?.map((user) => (
        <div key={user.id} className="flex items-center justify-between p-4 border rounded">
          <div>
            <h3 className="font-semibold">{user.name}</h3>
            <p className="text-gray-600">{user.email}</p>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant={user.active ? 'success' : 'warning'}
              onClick={() => handleToggleActive(user)}
              disabled={updateUser.isPending}
            >
              {user.active ? 'Deactivate' : 'Activate'}
            </Button>
            
            <Button
              variant="danger"
              onClick={() => deleteUser.mutate(user.id)}
              disabled={deleteUser.isPending}
            >
              Delete
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
```

### Infinite Queries

```typescript
// lib/api/queries/postQueries.ts
import { useInfiniteQuery } from '@tanstack/react-query';

export const usePosts = () => {
  return useInfiniteQuery({
    queryKey: ['posts'],
    queryFn: ({ pageParam = 1 }) => 
      apiClient.get(`/api/posts?page=${pageParam}&limit=10`),
    getNextPageParam: (lastPage, pages) => {
      if (lastPage.hasNextPage) {
        return pages.length + 1;
      }
      return undefined;
    },
  });
};
```

```tsx
// components/PostList.tsx
import { usePosts } from '@/lib/api/queries/postQueries';
import { useInView } from 'react-intersection-observer';

export function PostList() {
  const { data, fetchNextPage, hasNextPage, isFetching } = usePosts();
  const { ref, inView } = useInView();

  React.useEffect(() => {
    if (inView && hasNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, fetchNextPage]);

  return (
    <div>
      {data?.pages.map((page) => (
        <div key={page.page}>
          {page.posts.map((post) => (
            <PostItem key={post.id} post={post} />
          ))}
        </div>
      ))}
      
      <div ref={ref}>
        {isFetching && <div>Loading more...</div>}
      </div>
    </div>
  );
}
```

## 🎨 State Management Best Practices

### 1. Clear Separation

```typescript
// ✅ Good: Clear separation of concerns
// Zustand store for client state
const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  theme: 'light',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));

// React Query for server state
const useUserData = (userId: string) => {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: () => apiClient.getUser(userId),
  });
};
```

### 2. Avoid State Duplication

```typescript
// ❌ Avoid: Duplicating server state in client stores
const useBadStore = create((set) => ({
  users: [], // Don't duplicate API data
}));

// ✅ Good: Use React Query for server data
const useUsers = () => {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => apiClient.getUsers(),
  });
};
```

### 3. Proper Error Handling

```typescript
// Zustand with error handling
interface DataState {
  data: any[];
  loading: boolean;
  error: string | null;
  fetchData: () => Promise<void>;
}

const useDataStore = create<DataState>((set) => ({
  data: [],
  loading: false,
  error: null,
  
  fetchData: async () => {
    set({ loading: true, error: null });
    
    try {
      const data = await apiClient.getData();
      set({ data, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },
}));

// React Query error handling
const useUserData = (userId: string) => {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: () => apiClient.getUser(userId),
    onError: (error) => {
      console.error('Failed to fetch user:', error);
      // Show user-friendly error message
      toast.error('Failed to load user data');
    },
  });
};
```

### 4. Performance Optimization

```typescript
// Memoize selector functions
const useSelectedUser = () => {
  return useUserStore((state) => state.user);
};

// Use select for specific data
const useUserName = () => {
  return useUserStore((state) => state.user?.name);
};

// Prevent unnecessary re-renders
const UserProfile = React.memo(({ userId }: { userId: string }) => {
  const { data: user } = useUser(userId);
  
  return (
    <div>
      <h2>{user?.name}</h2>
      <p>{user?.email}</p>
    </div>
  );
});
```

### 5. State Persistence

```typescript
// Zustand with persistence
const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'light',
      language: 'en',
      notifications: true,
      updateSettings: (settings) => set(settings),
    }),
    {
      name: 'settings-storage',
      // Custom serialization for complex data
      serialize: (state) => JSON.stringify(state),
      deserialize: (str) => JSON.parse(str),
    }
  )
);

// React Query cache persistence
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      cacheTime: 1000 * 60 * 60 * 24, // 24 hours
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});
```

## 🔄 State Synchronization

### Cross-Store Updates

```typescript
// Sync Zustand and React Query
const useSyncedUserStore = create((set, get) => ({
  user: null,
  
  // When user logs in, also invalidate React Query cache
  login: async (credentials) => {
    const user = await apiClient.login(credentials);
    set({ user });
    
    // Invalidate related queries
    queryClient.invalidateQueries({ queryKey: ['user'] });
    queryClient.invalidateQueries({ queryKey: ['profile'] });
  },
  
  // When user logs out, clear React Query cache
  logout: () => {
    set({ user: null });
    
    // Clear related queries
    queryClient.removeQueries({ queryKey: ['user'] });
    queryClient.removeQueries({ queryKey: ['profile'] });
  },
}));
```

### Event-Driven Updates

```typescript
// Use events for cross-component communication
import { createEvent } from 'zustand';

const userEvents = createEvent();

// Component A: Dispatch event
const ComponentA = () => {
  const updateUser = useUpdateUser();
  
  const handleUpdate = async (userData) => {
    await updateUser.mutateAsync(userData);
    userEvents.emit('userUpdated', userData);
  };
  
  return <button onClick={handleUpdate}>Update</button>;
};

// Component B: Listen to event
const ComponentB = () => {
  const [lastUpdate, setLastUpdate] = useState(null);
  
  useEffect(() => {
    const unsubscribe = userEvents.on('userUpdated', (userData) => {
      setLastUpdate(new Date());
    });
    
    return unsubscribe;
  }, []);
  
  return <div>Last update: {lastUpdate?.toString()}</div>;
};
```

## 🧪 Testing State Management

### Testing Zustand Stores

```typescript
// stores/userStore.test.ts
import { create } from 'zustand';
import { useUserStore } from './userStore';

// Mock the store for testing
const createMockStore = () => {
  const setState = jest.fn();
  const getState = jest.fn();
  
  return {
    setState,
    getState,
    // Your store methods
  };
};

describe('UserStore', () => {
  it('should set user', () => {
    const store = createMockStore();
    store.setState({ user: { name: 'John' } });
    
    expect(store.setState).toHaveBeenCalledWith({ user: { name: 'John' } });
  });
});
```

### Testing React Query

```typescript
// components/UserList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useUsers } from '@/lib/api/queries/userQueries';
import { UserList } from './UserList';

// Mock the query hook
jest.mock('@/lib/api/queries/userQueries');

const mockUseUsers = useUsers as jest.MockedFunction<typeof useUsers>;

describe('UserList', () => {
  const queryClient = new QueryClient();

  it('displays users', () => {
    mockUseUsers.mockReturnValue({
      data: [{ id: '1', name: 'John', email: 'john@example.com' }],
      isLoading: false,
      error: null,
    });

    render(
      <QueryClientProvider client={queryClient}>
        <UserList />
      </QueryClientProvider>
    );

    expect(screen.getByText('John')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });
});
```

## 📚 Additional Resources

### Zustand Documentation
- [Zustand Official Docs](https://github.com/pmndrs/zustand)
- [Zustand Middleware](https://github.com/pmndrs/zustand#middleware)
- [Zustand Persistence](https://github.com/pmndrs/zustand#persist)

### React Query Documentation
- [TanStack Query Docs](https://tanstack.com/query/v4/docs/react/overview)
- [Queries](https://tanstack.com/query/v4/docs/react/guides/queries)
- [Mutations](https://tanstack.com/query/v4/docs/react/guides/mutations)
- [Infinite Queries](https://tanstack.com/query/v4/docs/react/guides/infinite-queries)

### State Management Patterns
- [State Management Guide](https://react.dev/learn/state-a-components-memory)
- [When to Use Global State](https://kentcdodds.com/blog/when-to-lift-state-up)
- [Performance Optimization](https://tanstack.com/query/v4/docs/react/guides/query-invalidation)
