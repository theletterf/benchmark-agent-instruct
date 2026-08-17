# Documentation bundle — Java agent and SDK defaults

Frozen authoritative OpenTelemetry documentation. Source sections are preserved in source order.

Sources:
- Java agent configuration — https://opentelemetry.io/docs/zero-code/java/agent/configuration/ (OpenTelemetry Java agent 2.x documentation, retrieved 2026-08-17)
- Environment Variable Specification — https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/ (OpenTelemetry specification 1.60.0, retrieved 2026-08-17)

---

<!-- source: java-agent-configuration#__intro__ -->
# ConfigurationFor more information

This page describes the various ways in which configuration can be supplied to the Java agent. For information on the configuration options themselves, see Configure the SDK.

---

<!-- source: java-agent-configuration#agent-configuration -->
## Agent Configuration

The agent can consume configuration from one or more of the following sources (ordered from highest to lowest priority):
- System properties
- Environment variables
- Configuration file
- Properties provided by the `AutoConfigurationCustomizer#addPropertiesSupplier()` function; using the `AutoConfigurationCustomizerProvider` SPI

---

<!-- source: java-agent-configuration#configuring-with-environment-variables -->
## Configuring with Environment Variables

In certain environments, configuring settings through environment variables is often preferred. Any setting that can be configured using a system property can also be set using an environment variable. While many of the settings below provide examples for both formats, for those that do not, use the following steps to determine the correct name mapping for the desired system property:
- Convert the system property name to uppercase.
- Replace all `.` and `-` characters with `_`.

For example `otel.instrumentation.common.default-enabled` would convert to `OTEL_INSTRUMENTATION_COMMON_DEFAULT_ENABLED`.

---

<!-- source: java-agent-configuration#configuration-file -->
## Configuration file

You can provide a path to an agent configuration file by setting the following property:System property: `otel.javaagent.configuration-file`Environment variable: `OTEL_JAVAAGENT_CONFIGURATION_FILE`

Description: Path to a valid Java properties file which contains the agent configuration.

---

<!-- source: java-agent-configuration#sdk-configuration -->
## SDK Configuration

The SDK’s autoconfiguration module is used for basic configuration of the agent. Read the docs to find settings such as configuring export or sampling.Important

Unlike the SDK autoconfiguration, versions 2.0+ of the Java agent and OpenTelemetry Spring Boot starter use `http/protobuf` as the default protocol, not `grpc`.

---

<!-- source: sdk-environment-variables#__intro__ -->
# Environment Variable Specification

**Status**: Stable except where otherwise specified

The goal of this specification is to unify the environment variable names and value parsing between different OpenTelemetry implementations.

Implementations MAY choose to allow configuration via the environment variables in this specification, but are not required to. If they do, they SHOULD use the names and value parsing behavior specified in this document. They SHOULD also follow the common configuration specification.

---

<!-- source: sdk-environment-variables#implementation-guidelines -->
## Implementation guidelines

Environment variables MAY be handled (implemented) directly by a component, in the SDK, or in a separate component (e.g. environment-based autoconfiguration component).

The environment-based configuration MUST have a direct code configuration equivalent.

---

<!-- source: sdk-environment-variables#parsing-empty-value -->
## Parsing empty value

The SDK MUST interpret an empty value of an environment variable the same way as when the variable is unset.

---

<!-- source: sdk-environment-variables#type-specific-guidance -->
## Type-specific guidance

### Boolean

Any value that represents a Boolean MUST be set to true only by the case-insensitive string `"true"`, meaning `"True"` or `"TRUE"` are also accepted, as true. An implementation MUST NOT extend this definition and define additional values that are interpreted as true. Any value not explicitly defined here as a true value, including unset and empty values, MUST be interpreted as false. If any value other than a true value, case-insensitive string `"false"`, empty, or unset is used, a warning SHOULD be logged to inform users about the fallback to false being applied. All Boolean environment variables SHOULD be named and defined such that false is the expected safe default behavior. Renaming or changing the default value MUST NOT happen without a major version upgrade.

### Numeric

The following guidance applies to all numeric types and extends the common configuration specification ‘Numeric’ guidance.

The following paragraph was added after stabilization and the requirements are thus qualified as “SHOULD” to allow implementations to avoid breaking changes. For new implementations, these should be treated as MUST requirements.

For variables accepting a numeric value, if the user provides a value the implementation cannot parse, the implementation SHOULD generate a warning and gracefully ignore the setting, i.e., treat them as not set.

### String

String values are sub-classified into:
- Enum.

#### Enum

The following guidance extends the common configuration specification ‘Enum’ guidance.

Enum values SHOULD be interpreted in a case-insensitive manner.

For sources accepting an enum value, if the user provides a value the implementation does not recognize, the implementation MUST generate a warning and gracefully ignore the setting.

---

<!-- source: sdk-environment-variables#general-sdk-configuration -->
## General SDK Configuration

| Name | Description | Default | Type | Notes |
| --- | --- | --- | --- | --- |
| OTEL_SDK_DISABLED | Disable the SDK for all signals | false | Boolean | If “true”, a no-op SDK implementation will be used for all telemetry signals. Any other value or absence of the variable will have no effect and the SDK will remain enabled. This setting has no effect on propagators configured through the OTEL_PROPAGATORS variable. |
| OTEL_ENTITIES | Entity information to be associated with the resource | | String | See Entities SDK for more details. |
| OTEL_RESOURCE_ATTRIBUTES | Key-value pairs to be used as resource attributes | See Resource semantic conventions for details. | String | See Resource SDK for more details. |
| OTEL_SERVICE_NAME | Sets the value of the `service.name` resource attribute | | String | If `service.name` is also provided in `OTEL_RESOURCE_ATTRIBUTES`, then `OTEL_SERVICE_NAME` takes precedence. |
| OTEL_LOG_LEVEL | Log level used by the SDK internal logger | “info” | Enum | |
| OTEL_PROPAGATORS | Propagators to be used as a comma-separated list | “tracecontext,baggage” | Enum | Values MUST be deduplicated in order to register a `Propagator` only once. |
| OTEL_TRACES_SAMPLER | Sampler to be used for traces | “parentbased_always_on” | Enum | See Sampling |
| OTEL_TRACES_SAMPLER_ARG | Value to be used as the sampler argument | | See footnote | The specified value will only be used if OTEL_TRACES_SAMPLER is set. Each Sampler type defines its own expected input, if any. Invalid or unrecognized input MUST be logged and MUST be otherwise ignored, i.e. the implementation MUST behave as if OTEL_TRACES_SAMPLER_ARG is not set. |

Known values for `OTEL_PROPAGATORS` are:
- `"tracecontext"`: W3C Trace Context
- `"baggage"`: W3C Baggage
- `"b3"`: B3 Single
- `"b3multi"`: B3 Multi
- `"jaeger"`: Jaeger - **Status**: Deprecated
- `"xray"`: AWS X-Ray (*third party*)
- `"ottrace"`: OT Trace (*third party*) - **Status**: Deprecated
- `"none"`: No automatically configured propagator.

Known values for `OTEL_TRACES_SAMPLER` are:
- `"always_on"`: `AlwaysOnSampler`
- `"always_off"`: `AlwaysOffSampler`
- `"traceidratio"`: `TraceIdRatioBased`
- `"parentbased_always_on"`: `ParentBased(root=AlwaysOnSampler)`
- `"parentbased_always_off"`: `ParentBased(root=AlwaysOffSampler)`
- `"parentbased_traceidratio"`: `ParentBased(root=TraceIdRatioBased)`
- `"parentbased_jaeger_remote"`: `ParentBased(root=JaegerRemoteSampler)`
- `"jaeger_remote"`: `JaegerRemoteSampler`
- `"xray"`: AWS X-Ray Centralized Sampling (*third party*)

Depending on the value of `OTEL_TRACES_SAMPLER`, `OTEL_TRACES_SAMPLER_ARG` may be set as follows:
- For `traceidratio` and `parentbased_traceidratio` samplers: Sampling probability, a number in the [0..1] range, e.g. “0.25”. Default is 1.0 if unset.
- For `jaeger_remote` and `parentbased_jaeger_remote`: The value is a comma separated list:
- `endpoint`: the endpoint in form of `scheme://host:port` of gRPC server that serves the sampling strategy for the service (sampling.proto).
- `pollingIntervalMs`: in milliseconds indicating how often the sampler will poll the backend for updates to sampling strategy.
- `initialSamplingRate`: in the [0..1] range, which is used as the sampling probability when the backend cannot be reached to retrieve a sampling strategy. This value stops having an effect once a sampling strategy is retrieved successfully, as the remote strategy will be used until a new update is retrieved.
- Example: `endpoint=http://localhost:14250,pollingIntervalMs=5000,initialSamplingRate=0.25`

---

<!-- source: sdk-environment-variables#exporter-selection -->
## Exporter Selection

We define environment variables for setting one or more exporters per signal.

| Name | Description | Default | Type |
| --- | --- | --- | --- |
| OTEL_TRACES_EXPORTER | Trace exporter to be used | `otlp` | Enum |
| OTEL_METRICS_EXPORTER | Metrics exporter to be used | `otlp` | Enum |
| OTEL_LOGS_EXPORTER | Logs exporter to be used | `otlp` | Enum |

The implementation MAY accept a comma-separated list to enable setting multiple exporters.

Known values for `OTEL_TRACES_EXPORTER` are:
- `"otlp"`: OTLP
- `"zipkin"`: Zipkin (Defaults to protobuf format)
- `"console"`: Standard Output
- `"logging"`: Standard Output. It is a deprecated value left for backwards compatibility. It SHOULD NOT be supported by new implementations.
- `"none"`: No automatically configured exporter for traces.

Known values for `OTEL_METRICS_EXPORTER` are:
- `"otlp"`: OTLP
- `"prometheus"`: Prometheus
- `"console"`: Standard Output
- `"logging"`: Standard Output. It is a deprecated value left for backwards compatibility. It SHOULD NOT be supported by new implementations.
- `"none"`: No automatically configured exporter for metrics.

Known values for `OTEL_LOGS_EXPORTER` are:
- `"otlp"`: OTLP
- `"console"`: Standard Output
- `"logging"`: Standard Output. It is a deprecated value left for backwards compatibility. It SHOULD NOT be supported by new implementations.
- `"none"`: No automatically configured exporter for logs.

### In-development Exporter Selection

**Status**: Development

In addition to the above, the following environment variables are added for in-development exporter selection:

Additional known values for `OTEL_TRACES_EXPORTER` are:
- `"otlp/stdout"`: OTLP File writing to standard output

Additional known values for `OTEL_METRICS_EXPORTER` are:
- `"otlp/stdout"`: OTLP File writing to standard output

Additional known values for `OTEL_LOGS_EXPORTER` are:
- `"otlp/stdout"`: OTLP File writing to standard output
