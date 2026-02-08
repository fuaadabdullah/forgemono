# Moved from GoblinOS/API_KEYS_STATUS.md

This document provides the current status of API keys.

## How to Deploy Locally

1. Ensure you have Python and virtualenv installed.
2. Navigate to the `backend/` directory.
3. Run the following commands:

   ```bash
   virtualenv venv
   source venv/bin/activate
   ./backend/scripts/deploy_backend.sh local
   ```

4. Follow the on-screen instructions.

## How to Add a New Goblin

Follow this checklist to add a new goblin (automation/agent) to GoblinOS. The goal is to keep the registry, tests, docs and ownership in sync.

Checklist

- [ ] Pick the correct guild in `GoblinOS/goblins.yaml` and add the goblin entry.
- [ ] Add a small README under `GoblinOS/docs/goblins/<goblin-id>.md` describing intent, inputs, outputs, permissions and ops runbook.
- [ ] Add unit tests and integration tests (see testing notes below).
- [ ] Update `CODEOWNERS` if the goblin has a clear owning team.
- [ ] Run role generation and local validation (commands below).
- [ ] Open a PR with description, test evidence, and link to the new doc; request reviews from owners and maintainers.
- [ ] Wait for CI to pass and reviewers to approve; merge when green.

Quick commands

```bash

# Add/update the YAML entry, then regenerate derived artifacts
cd GoblinOS
node scripts/generate-roles.js

# Run the unit test suite for GoblinOS
OVERMIND_MOCK=1 pnpm test
```

Sample `goblins.yaml` snippet

```yaml
- id: example-goblin
    name: "Example Goblin"
    guild: crafters
    owner: glyph-scribe@example.com
    description: "Runs data enrichment for watchlists"
    command: packages/example-goblin/bin/run.js
    inputs:
        - type: ticker
            required: true
```

Testing notes

- Use `OVERMIND_MOCK=1` when running tests that rely on the KPI bridge or in-memory mocks.
- Add focused unit tests for any logic you introduce. Place Node tests inside `GoblinOS/packages/<pkg>/test` and Python tests in the app's `tests/` folder.
- For integration tests that exercise tool invocation flows, use the `packages/goblins/overmind/bridge` harness to assert KPI events.

PR & Release checklist

- Title: `add: goblin <example-goblin> — short description`
- Body: include sample YAML diff, link to `docs/goblins/<goblin-id>.md`, and test run output.
- Ensure CI passes (unit, lint, and integration where applicable).
- Assign reviewers: `CODEOWNERS` entries will help; explicitly request maintainers if unsure.

Post-merge

- Confirm the goblin shows in `docs/ROLES.md` and any generated UI/registry pages.
- If the goblin requires secrets, create entries using GoblinOS vault tooling (do NOT commit secrets in the repo). Document required secrets in the goblin README with placeholders.


## Data Flow Diagram

A data flow diagram is currently missing. Placeholder: [Insert diagram here].

## Error Handling Strategy

All backend scripts should:

- Log errors to `logs/errors.log`.
- Exit with a non-zero status code on failure.
- Use the `set -e` flag in Bash scripts to stop on errors.
- Document known error cases in the script headers.

### Bash Example

```bash

set -e
trap 'echo "Error on line $LINENO" | tee -a logs/errors.log' ERR

# Example command
cp somefile.txt /tmp/
```

### Python Example

```python
import logging
logging.basicConfig(filename='logs/errors.log', level=logging.ERROR)

try:
    # Example command
    with open('somefile.txt') as f:
        data = f.read()
except Exception as e:
    logging.error(f"Error: {e}")
    exit(1)
```
