---
title: "MODULAR CODE PRINCIPLE"
description: "Documentation for MODULAR CODE PRINCIPLE"
---

## Modular Code Principle

This file provides a short guide and a checklist to help developers design modular code in the ForgeMonorepo projects.

Principles:

- Single responsibility per file/module: Each module (file or folder) should have a single responsibility.
- Minimal, well-documented public API: Export only what consumers need. Provide typed interfaces for components and functions.
- Pure utilities, side-effect free: Keep utilities pure and free of DOM or runtime dependencies where possible.
- Small, importable utilities: Export helper functions from utility files instead of keeping them hidden inside components.
- Tests and examples: Each module should have minimal tests showing expected usage and edge cases.
- Clear directory layout:
  - index.tsx or index.ts for public exports
  - component/ for UI pieces
  - utils.ts for helper functions
  - index.test.tsx to exercise APIs and the component
  - styles.css for component styles

Contract (example)

- Inputs: typed props for React components or typed parameters for functions
- Outputs: deterministic values or React elements
- Error handling: return null / undefined or throw consistent, documented errors
- Side effects: explicit and documented (e.g. calling navigator.clipboard)

Checklist for new modules

1. Create a small, focused module folder (component/utils/css/test)
2. Add an index file that exports the public API
3. Add unit tests for public functions and the component
4. Keep mutation minimal and document side effects
5. Add a short README or comments explaining the API

Reference Example: See `apps/goblin-assistant/src/components/modular/` for an example scaffold.

Tips and conventions

- When a utility is shared across features, place it in `src/utils/` and export it from the `index` barrel (if needed).
- Use descriptive names; avoid default exports unless a module is providing a single default component with supporting named utilities.
- Prefer named exports for utilities to make tree-shaking and explicit usage clearer.

Example: StreamingView refactor

- Component: `apps/goblin-assistant/src/components/streaming/StreamingView.tsx`
- Utilities: `apps/goblin-assistant/src/components/streaming/streamingUtils.ts`
- Barrel export: `apps/goblin-assistant/src/components/streaming/index.ts`

This refactor extracts text parsing and token detection logic into `streamingUtils.ts` while keeping the component focused on rendering and UI state.

Next steps

- Adopt a PR checklist that includes a modular principle review.
- Add a codegen scaffold for new modules (optional) to speed up adoption.

Scaffold tool usage (optional)

- `./tools/modular_scaffold.sh components/<module-name>` - creates a new module scaffold under `apps/goblin-assistant/src/components/<module-name>` with component file, utils, style, index and test.

-- ForgeMonorepo Team
