# OpenTelemetry prior calibration

Model: google/gemini-2.5-flash-lite

Decision-level currentness is primary; fully-current responses are reported separately.

| Task | Responses | Current decisions | Fully current | Mixed responses |
|---|---:|---:|---:|---:|
| http-client-span | 3 | 12/12 (100.0%) | 3/3 (100.0%) | 0 |
| http-server-span | 3 | 5/12 (41.7%) | 0/3 (0.0%) | 0 |
| http-client-duration | 3 | 3/6 (50.0%) | 0/3 (0.0%) | 3 |
| database-client-span | 3 | 2/15 (13.3%) | 0/3 (0.0%) | 2 |
| java-agent-configuration | 3 | 0/6 (0.0%) | 0/3 (0.0%) | 0 |

This diagnostic is not Experiment 0.
