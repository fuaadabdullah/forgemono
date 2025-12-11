<!--
This file lists the currently skipped tests (20) and provides ready-to-paste
Jira ticket summaries, descriptions, labels, priority and acceptance criteria
to track missing implementations or environment gaps.

Usage:

- Copy each "Summary" and "Description" into a Jira ticket form or use the
  REST API to create tickets in bulk. Do NOT commit credentials into the repo.

- Suggested labels and assignees are provided as placeholders. Adjust to your
  team's workflow.
-->

# Skipped tests -> Jira tickets

Generated: automatically by the dev assistant to track skipped/disabled tests so
CI can be unblocked. Each section below corresponds to one ticket.

---

1. Test file: `apps/goblin-assistant/backend/tests/test_auth_resilience.py`

Summary: Implement `auth.challenge_store` used by auth resilience tests

Description:
The module `auth.challenge_store` is referenced by the auth resilience tests but
the implementation is missing, causing the tests to be skipped. Implement the
challenge store API used by the auth stack (create/read/delete challenge tokens,
TTL, and any persistence required). Update DI wiring and test fixtures.

Suggested labels: `backend`, `auth`, `tests`, `blocked-ci`
Priority: Major

Acceptance criteria:

- A concrete `auth.challenge_store` module exists and matches the interface
  expected by `tests/test_auth_resilience.py`.

- Unit tests that were previously skipped are re-enabled and pass locally.
- Add a minimal memory-backed implementation for CI and a production-backed
  implementation (e.g., Redis/Supabase) documented in README.


---

2. Test file: `apps/goblin-assistant/backend/tests/test_consolidated_auth.py`

Summary: Implement `SupabaseAuthService` or adapt auth_service for tests

Description:
`test_consolidated_auth.py` is skipped because `SupabaseAuthService` hasn't
been implemented in `auth_service`. Implement the service (or a test double)
that provides the authentication flow used by the consolidated auth tests.

Suggested labels: `backend`, `auth`, `supabase`, `tests`
Priority: Major

Acceptance criteria:

- `SupabaseAuthService` or an equivalent pluggable implementation exists and is
  wireable via configuration for tests.

- Consolidated auth tests can be re-enabled and pass in the CI test matrix.


---

3. Test file: `apps/goblin-assistant/backend/tests/test_settings.py`

Summary: Fix relative-imports for `models.settings` and re-enable tests

Description:
Tests are skipped due to relative import issues with `models/settings`. Update
package imports to use project-root absolute imports (or add package
initializers) so tests can import application models correctly.

Suggested labels: `backend`, `tests`, `import-fix`
Priority: Minor

Acceptance criteria:

- Import errors for `models.settings` are resolved in test runs.
- Tests are re-enabled and validated locally.


---

4. Test file: `apps/goblin-assistant/backend/tests/unit/test_auth.py`

Summary: Implement `auth.challenge_store` used by unit auth tests

Description:
Unit tests in `tests/unit/test_auth.py` are skipped for the same missing
`auth.challenge_store` module. Implement the interface and provide a test
fixture to exercise the logic in unit tests.

Suggested labels: `unit-tests`, `auth`, `backend`
Priority: Major

Acceptance criteria:

- Unit tests re-enabled and passing with memory-backed test fixture.


---

5. Test file: `apps/goblin-assistant/backend/tests/unit/test_chat_validation.py`

Summary: Fix chat router relative import issues and re-enable validation tests

Description:
Chat validation unit tests are skipped due to relative import problems when
importing the chat router. Make the router importable in test context (package
layout or absolute imports) and ensure fixtures are available.

Suggested labels: `backend`, `chat`, `tests`
Priority: Minor

Acceptance criteria:

- Chat router imports correctly in tests and validation tests pass locally.


---

6. Test file: `apps/goblin-assistant/backend/test_latency_integration.py`

Summary: Re-enable latency integration tests after resolving chat router imports

Description:
Latency integration tests were skipped because of chat router import issues.
Make the integration harness import modules reliably for both SQLite and
Postgres test configurations.

Suggested labels: `integration`, `performance`, `tests`
Priority: Minor

Acceptance criteria:

- Integration test imports succeed and the latency integration test runs in
  the CI matrix (optionally gated to a slower/integration job).

---

7. Test file: `apps/goblin-assistant/backend/test_scheduler_no_pytest.py`

Summary: Provide scheduler test environment or adapt tests to not require Redis

Description:
Scheduler tests are skipped because Redis dependencies are not available in
the test environment. Provide a memory-backed scheduler stub, or mark these as
integration tests and move them to a separate CI job with Redis available.

Suggested labels: `scheduler`, `integration`, `redis`, `tests`
Priority: Minor

Acceptance criteria:

- Local unit tests run without requiring Redis by using a stub or fixture.
- Integration tests that require Redis are documented and moved to a gated job
  if necessary.

---

8. Test file: `apps/goblin-assistant/backend/test_chat_api.py`

Summary: Provide test dependencies for Chat API or move tests to integration job

Description:
Chat API tests are skipped because the necessary external dependencies and
service mocks aren't present. Add lightweight mocks or mark these tests as
integration tests that run in a separate CI job with required services.

Suggested labels: `chat`, `integration`, `tests`
Priority: Minor

Acceptance criteria:

- Chat API tests pass in a local development environment with a documented
  test harness, or are moved to an integration pipeline that supplies mocks.

---

9. Test file: `apps/goblin-assistant/backend/test_mock_local_proxy.py`

Summary: Remove or replace deprecated mock-local-proxy tests

Description:
This file contains deprecated mock tests. The project now prefers local model
integration tests. Review and either remove these deprecated tests or update
them to the new integration approach (`test_local_model_integration.py`).

Suggested labels: `tests`, `cleanup`, `models`
Priority: Trivial

Acceptance criteria:

- Deprecated tests are removed or replaced. No skipped tests remain for this
  file.

---

10. Test file: `apps/goblin-assistant/backend/test_jwt_auth_router.py`

Summary: Add test support for JWT auth router dependencies

Description:
JWT auth router tests are skipped because supporting dependencies are not
available. Provide required fixtures or refactor the router so it can be
unit-tested in isolation using dependency injection and mocks.

Suggested labels: `auth`, `jwt`, `tests`
Priority: Minor

Acceptance criteria:

- JWT router unit tests re-enabled and passing with injected mocks.

---

11. Test file: `apps/goblin-assistant/backend/test_scheduler.py`

Summary: Make scheduler code unit-testable without external queue backends

Description:
Scheduler tests are skipped due to missing dependencies. Add a testable
abstraction layer for scheduling (in-memory) or provide test fixtures to mock
external queue systems so unit tests can run in CI.

Suggested labels: `scheduler`, `tests`, `ci`
Priority: Minor

Acceptance criteria:

- Scheduler unit tests run in CI using in-memory implementations or mocks.

---

12. Test file: `apps/goblin-assistant/backend/tests/load_test.py`

Summary: Provide load-testing harness or mark as optional that requires Locust

Description:
Load tests are skipped because Locust isn't installed in the test environment.
Either add a dev-only dependency and mark these tests as optional, or move the
load tests to a separate performance testing pipeline.

Suggested labels: `load-test`, `performance`, `locust`
Priority: Trivial

Acceptance criteria:

- Load tests are not blocking CI. If kept, they run in a separate performance
  pipeline with required tools installed.

---

13. Test file: `apps/goblin-assistant/backend/tests/test_provider_client.py`

Summary: Add HTTP mocking dependency (respx) or adapt provider client tests

Description:
Provider client tests are skipped due to missing `respx`. Add `respx` to the
test requirements or use `requests-mock`/unittest.mock to isolate HTTP calls.

Suggested labels: `providers`, `http`, `tests`
Priority: Minor

Acceptance criteria:

- Provider client tests run locally and in CI with the HTTP mocking library
  available.

---

14. Test file: `apps/goblin-assistant/backend/providers/tests/test_provider_interface.py`

Summary: Provide provider interface dependencies or mocks for unit tests

Description:
Provider interface tests are skipped because provider dependencies are not
available. Add interfaces, test doubles, or fixture wiring to run these tests
in CI.

Suggested labels: `providers`, `tests`
Priority: Minor

Acceptance criteria:

- Provider interface unit tests re-enabled and passing with mocks.

---

15. Test file: `apps/goblin-assistant/backend/test_complete_auth_flow.py`

Summary: Revisit complete auth flow tests and provide required integration
dependencies

Description:
Complete auth flow tests are skipped because they require integration-level
services. Either provide an integration test environment (with DB/Redis/etc.)
or convert the tests to integration jobs that run separately from unit CI.

Suggested labels: `integration`, `auth`, `tests`
Priority: Major

Acceptance criteria:

- Complete auth flow tests are either reimplemented as unit tests with mocks
  or moved into an integration pipeline with documented preconditions.

---

16. Test file: `apps/goblin-assistant/backend/auth/tests/test_passkey_e2e.py`

Summary: Implement passkey (WebAuthn) functionality or mark as backlog

Description:
End-to-end passkey tests are skipped because passkey functionality is not
implemented. Implement the WebAuthn/passkey flow or create a feature backlog
ticket to schedule work. Provide a test double if necessary to unblock CI.

Suggested labels: `auth`, `webauthn`, `e2e`, `tests`
Priority: Major

Acceptance criteria:

- Either the passkey flow is implemented and tests pass, or the test is
  documented and tracked in the backlog with a linked feature ticket.

---

17. Test file: `apps/goblin-assistant/backend/test_routing_server.py`

Summary: Add test environment or mock for routing server dependencies

Description:
Routing server tests are skipped due to missing external dependencies. Provide
test stubs/mocks or move tests to a separate integration job with the routing
server available.

Suggested labels: `routing`, `integration`, `tests`
Priority: Minor

Acceptance criteria:

- Routing server tests either run with mocks or are moved to gated
  integration pipelines.

---

18. Test file: `apps/goblin-assistant/backend/test_rag_pipeline.py`

Summary: Provide RAG pipeline test dependencies or mock external vector DBs

Description:
RAG pipeline tests are skipped because external dependencies (vector DB,
embeddings) are not available. Provide a memory-backed vector store or mocks to
run the pipeline logic in CI.

Suggested labels: `rag`, `vector-db`, `tests`
Priority: Major

Acceptance criteria:

- RAG pipeline unit tests run with an in-memory vector store and pass in CI,
  or the tests are moved to an integration pipeline with preinstalled
  dependencies.

---

19. Test file: `apps/goblin-assistant/backend/test_model_comparison.py`

Summary: Add test mocks for model comparison dependencies

Description:
Model comparison tests are skipped since model comparison infrastructure or
external model endpoints aren't available. Create test doubles or local model
harness to exercise comparison logic.

Suggested labels: `models`, `tests`, `comparison`
Priority: Minor

Acceptance criteria:

- Model comparison unit tests run with local model stubs and pass in CI.

---

20. Test file: `/Users/fuaadabdullah/ForgeMonorepo/GoblinOS/packages/goblins/forge-smithy/tests/test_basic.py`

Summary: Add agent test environment or gate these heavy agent tests

Description:
Lines in `forge-smithy/tests/test_basic.py` contain pytest.skip("Agent
dependencies not available"). Decide whether to add the agent dependencies in
CI or mark the tests as optional/slow and gate them behind a separate job.

Suggested labels: `goblins`, `agents`, `tests`, `ci`
Priority: Minor

Acceptance criteria:

- Agent-related tests either have their dependencies provided in a separate CI
  stage or are marked as optional and moved out of the fast unit test suite.

---

# Next steps

- Use this file to copy/paste ticket payloads into Jira or use a small script
  to call the Jira REST API (don't store credentials in the repo). Example
  fields to fill: project, issue type=Task, summary, description, labels,
  priority, assignee.

- After tickets are created, update each skipped test file to include the
  created Jira issue key (e.g. `pytest.skip("... — JIRA: PROJ-123")`). This
  provides direct traceability from CI to the backlog.

---

Authored by: GitHub Copilot (assistant)
