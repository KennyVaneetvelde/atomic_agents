# Agent Guild endpoint observation

This optional Atomic Tool asks Agent Guild for a live observation of one public
HTTP or HTTPS A2A or MCP endpoint the caller has already selected. It returns all
six expected check statuses, the validated service verdict and complete
failed/unknown/scored lists, the exact target, and caller request/completion times. Descriptions and limitations are fixed local text; arbitrary service prose
and extra fields are omitted from model-visible output.

The hosted Guild service receives the entire URL, actively probes the endpoint
and logs the request. Supply only a public operational endpoint, such as `/mcp`
or `/a2a`, with no credentials, secret query parameters or confidential path.
Use it when this disclosure and active probing are within the operator's task.
The observation is vendor-supplied data, not authorization, an independent safety
assessment or proof of successful task execution. No target task is invoked by
this tool. A favorable result never triggers delegation.

## Use

Download the `agent_guild_observation` directory through Atomic Assembler's
**Download Tools** browser, or copy its source into your project. Assembler copies
the source, tests and this README; it excludes dependency metadata. Your project
needs Python 3.12+, `atomic-agents>=2.10.2,<3`, `pydantic>=2.11,<3` and
`httpx>=0.28.1,<1`. No account or API key is required for the Guild operation.

From the copied directory:

```python
from tool.agent_guild_observation import (
    AgentGuildObservationInput,
    AgentGuildObservationTool,
)

# selected_endpoint comes from the caller's authorized workflow.
observation_tool = AgentGuildObservationTool()
request = AgentGuildObservationInput(endpoint_url=selected_endpoint)
result = observation_tool.run(request)
print(result.model_dump_json(indent=2))
```

An existing asynchronous workflow can use `await observation_tool.run_async(request)`.
Cancellation propagates through the native asynchronous HTTP client; no background
thread continues a hidden request. The synchronous interface blocks its caller.

Atomic Agents can produce `AgentGuildObservationInput` as an agent's output schema;
the host then passes that validated selection to `observation_tool.run(selection)`.
This follows the native single-tool composition pattern. The host retains the
decision to probe and the decision about any later action. No persistent agent
instructions or automatic hooks are installed.

Optional host restrictions are exact matches, not required initial setup:

```python
from tool.agent_guild_observation import AgentGuildObservationConfig

restricted_tool = AgentGuildObservationTool(
    AgentGuildObservationConfig(allowed_hosts=("partner.example.com",), timeout=8)
)
```

With `allowed_hosts=()` (the default), newly selected public-looking hosts are
accepted. Non-global IP literals and reserved/local hostnames are rejected.
Local validation does not resolve DNS or establish that a hostname maps only to
public addresses; the Guild performs its own separate target screening.

## Output and failure behavior

- `status="observed"` means a bounded JSON observation with matching target and
  consistent check summaries was received. It does not mean the checks passed.
- `observation` projects all six expected check statuses and validated summary
  lists, with fixed local descriptions. Duplicate/missing checks, duplicate summary
  entries and a verdict inconsistent with the statuses are rejected. Vendor
  headlines, details, limits prose, links and arbitrary fields are not forwarded.
  The raw-byte digest identifies the input used for the projection.
- `response_sha256` identifies accepted response bytes; it is not a signature.
- `requested_at` and `completed_at` come from the caller clock. They are not the
  service's signed observation timestamps and do not establish lasting freshness.
- Invalid input, failed transport, non-200 status, redirect, wrong content type,
  compression, oversized response, malformed JSON, missing/mismatched target or
  inconsistent check summaries produce `status="error"`, a fixed error code and
  no observation. Status arrays are never truncated and unknown is never converted into pass.
  The documented projection intentionally omits arbitrary remote prose.

Only the fixed `https://agent-guild-5d5r.onrender.com/preflight` route is requested.
TLS verification is enabled. Redirects, environment proxies and retries are
disabled. Responses are limited to 65,536 uncompressed bytes; encoded responses
are rejected. The configurable timeout bounds individual HTTP operations, not
the total wall-clock duration. The request discloses the fixed User-Agent
`agentguild-atomic-tool/0.1 (host=AtomicAgents; source=atomic-forge)`.

This tool does not register an identity, request credits, retrieve or issue a
passport, invoke `/check`, settle funds or fall back to another operation.
There is no fee or payment step in this contribution or its preflight workflow.

## Tests

From the repository root, after the documented workspace dependency setup:

```text
uv run pytest atomic-forge/tools/agent_guild_observation/tests -q
```

Tests use real Atomic Agents classes and HTTPX clients with only the HTTP/provider
completion boundary substituted. They make no live model or Guild call. The
response fixture is an Agent Guild first-party observation retained on
2026-09-11; it is not independent adoption evidence or proof of current behavior.

MIT licensed original contribution by AgentTanuki.
