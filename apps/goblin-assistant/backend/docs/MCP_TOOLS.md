# MCP Tools (Fetch + HTTP + SQL)

Goblin Assistant is set up to use Docker's MCP Gateway (via `.vscode/mcp.json`) to expose a small set of practical MCP tools:

- `fetch` (web page fetch + markdown extraction)
- `curl` (generic HTTP client for REST: GET/POST, headers, auth, JSON)
- `database-server` (SQL connector for Postgres/SQLite/MySQL: connect + execute SQL + inspect tables)

## Prereqs

- Docker Desktop must be running (the `docker mcp` CLI depends on it).

## Enabled Tools

The gateway is configured in `.vscode/mcp.json` to enable:

- `fetch`
- `curl`
- `connect_to_database`
- `execute_sql`
- `query_database`
- `list_tables`
- `describe_table`
- `get_connection_examples`
- `get_current_database_info`

## Usage Notes

### HTTP

- Use `fetch` when you want readable page content (markdown) for docs.
- Use `curl` when you need full control (method, headers, auth, JSON payloads).

Example `curl` args for JSON POST:

```json
{
  "args": [
    "-sS",
    "-X",
    "POST",
    "https://example.internal/api/v1/foo",
    "-H",
    "Content-Type: application/json",
    "-H",
    "Authorization: Bearer $TOKEN",
    "--data",
    "{\"hello\":\"world\"}"
  ]
}
```

### SQL (Postgres / SQLite)

Use `connect_to_database` once, then run `execute_sql` / `list_tables` / `describe_table`.

Example Postgres connection string:

```
postgresql://user:password@host:5432/dbname
```

SQLite works too, but the file path must be accessible to the MCP server runtime (container). If you need a persistent local SQLite file, consider running a dedicated SQLite MCP server with an explicit volume mount.

## Security

- Treat DB connection strings and API tokens as secrets.
- Prefer secrets managers over pasting credentials into prompts when possible.
- Be cautious with `curl` output: it can include sensitive data.

