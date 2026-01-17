---
description: "Goblin Node TUI"
---



# Goblin Node TUI

Simple Node-based TUI for quick repository maintainer commands.

## Installation & Usage

Install dependencies in the tool folder and run:

```bash
pnpm -C tools/tui-node install
pnpm -C tools/tui-node start
```

By default the tool reads `tools/tui/config.json` (or `tools/tui/config.json.example`).
For non-interactive tests you can set `GOBLIN_CMD=1` to pick the first command.

## Architecture

The application has been refactored into separate modules for better maintainability:

### Modules

- **`lib/config.js`** - Configuration loading and parsing
- **`lib/command-selector.js`** - Interactive and non-interactive command selection
- **`lib/path-resolver.js`** - Working directory path resolution and templating
- **`lib/command-runner.js`** - Command execution using execa
- **`index.js`** - Main orchestration file

### Benefits

- **Separation of Concerns**: Each module has a single responsibility
- **Testability**: Individual modules can be unit tested
- **Maintainability**: Changes to specific functionality are isolated
- **Reusability**: Modules can be reused in other parts of the application
