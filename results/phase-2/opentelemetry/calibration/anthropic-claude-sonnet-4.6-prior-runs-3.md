# OpenTelemetry prior calibration

Model: anthropic/claude-sonnet-4.6

Decision-level currentness is primary; fully-current responses are reported separately.

| Task | Responses | Current decisions | Fully current | Mixed responses |
|---|---:|---:|---:|---:|
| http-client-span | 3 | 12/12 (100.0%) | 3/3 (100.0%) | 0 |
| http-server-span | 3 | 12/12 (100.0%) | 3/3 (100.0%) | 0 |
| http-client-duration | 3 | 6/6 (100.0%) | 3/3 (100.0%) | 0 |
| database-client-span | 3 | 12/15 (80.0%) | 0/3 (0.0%) | 3 |
| java-agent-configuration | 3 | 0/6 (0.0%) | 0/3 (0.0%) | 1 |

This diagnostic is not Experiment 0.
