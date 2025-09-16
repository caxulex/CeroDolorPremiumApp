# MCP Message Patterns (Draft)

This document summarizes the intended message flow and payload shapes between agents per the MVP.

## Reference Repos (defaults)
We scaffold against public MCP examples so anyone can replicate locally:
- Server (reference servers): https://github.com/modelcontextprotocol/servers
- Studio (inspector/web UI): https://github.com/modelcontextprotocol/inspector
- Agent examples (Python/Node): https://github.com/lastmile-ai/mcp-agent

Use `scripts/setup_coral_repos.ps1` with no parameters to clone these defaults under `external/`.

## Ping-Pong Validation (Local)
- Router sends `{ "type": "ping" }` to AIP
- AIP responds with `{ "type": "pong" }`
- ASD and AIPer acknowledge and enrich payloads
- Run locally:
  ```pwsh
  ./scripts/run_backend_demo.ps1
  ```

## Contracts (From specs/contracts)
- AIP → ASD: `aip_to_asd.json`
- ASD → AIPer: `asd_to_aiper.json`

## Next Steps
- Replace local subprocess calls with Coral MCP transport
- Map ping/pong fields to real contract fields
- Add correlation IDs and error envelopes

## Envelope (Mock MCP)
We use a simple envelope to prepare for real MCP:
```json
{
  "id": "uuid",
  "ts": 1690000000000,
  "source": "AIP",
  "target": "ASD",
  "payload": { /* contract-shaped content */ }
}
```

Example transcript item:
```json
{ "send": { "id": "...", "source": "router", "target": "AIP", "payload": { "type": "ping" } } }
{ "recv": { "from": "AIP", "payload": { "type": "pong", "echo": { "type": "ping" } } } }
```

## Mapping to MCP Concepts
- Our `id` maps to MCP request IDs; `source`/`target` map to client/server roles.
- The `payload` content should conform to our JSON Schemas; in MCP this would be the `result` or tool `arguments`.
- Errors should be wrapped in an envelope with `type: error` analogous to MCP error responses.
- Correlation: carry contract fields and `id` through hops to trace end-to-end.

Next iteration will swap the local subprocess/mock transport for real MCP:
1. Launch a reference server and studio (inspector) from the repos above.
2. Adapt our agents to MCP client contracts or run example agents and call them through the server.
3. Replace `router.py` IO with MCP client calls while keeping schema validation.
