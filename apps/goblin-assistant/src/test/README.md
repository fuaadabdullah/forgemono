# Testing guidance for goblin-assistant

This small guide covers the preferred testing stack for the `goblin-assistant` app.

- Test runner: Jest (migrated from Vitest). The repo previously used Vitest; Jest is now the canonical test runner for this app.
- Assertion/utilities: @testing-library/react, @testing-library/jest-dom (matchers added in `src/test/setup.ts`)

Guidelines:

- Prefer `renderHook` from `@testing-library/react` to test hooks where possible.
- Use mock module patterns: `jest.mock('path/to/module', () => ({ ... }))` to mock the `apiClient` or other modules.
- Use `jest.useFakeTimers()` if you need to simulate setTimeouts / polling loops.
- Use `waitFor(...)` to wait for asynchronous assertions.
- Keep tests small and deterministic. Avoid network calls during tests by mocking the API client.

Templates exist in `src/test/templates` for quick copying.
