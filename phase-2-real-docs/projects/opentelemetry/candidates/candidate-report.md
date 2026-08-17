# OpenTelemetry candidate prior conflicts

Frozen official sources, not model recall, define all historical/current mappings.

| Candidate | Historical form | Current form | Source |
|---|---|---|---|
| http-method | `http.method` | `http.request.method` | http-migration |
| http-status | `http.status_code` | `http.response.status_code` | http-migration |
| http-url | `http.url` | `url.full` | http-migration |
| http-server-address | `net.host.name` | `server.address` | http-migration |
| http-duration-name | `http.client.duration` | `http.client.request.duration` | http-migration |
| http-duration-unit | `ms` | `s` | http-migration |
| db-system | `db.system` | `db.system.name` | database-migration |
| db-statement | `db.statement` | `db.query.text` | database-migration |
| db-operation | `db.operation` | `db.operation.name` | database-migration |
| db-namespace | `db.name` | `db.namespace` | database-migration |
| semconv-http-dup | `old conventions only by default` | `http/dup emits old and stable conventions` | http-migration |
| java-agent-otlp-default | `grpc` | `http/protobuf` | java-agent-configuration |

## Proposed calibration tasks

- `http-client-span` — HTTP client span attributes: 4 independently scored decisions.
- `http-server-span` — HTTP server span attributes: 4 independently scored decisions.
- `http-client-duration` — HTTP client duration metric: 2 independently scored decisions.
- `database-client-span` — Database client span attributes: 5 independently scored decisions.
- `java-agent-configuration` — Java agent OTLP and service configuration: 2 independently scored decisions.
