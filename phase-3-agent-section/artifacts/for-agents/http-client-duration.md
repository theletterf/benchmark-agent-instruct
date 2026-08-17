# Documentation bundle — HTTP client duration histogram

Frozen authoritative OpenTelemetry documentation. Source sections are preserved in source order.

Sources:
- Semantic conventions for HTTP metrics — https://opentelemetry.io/docs/specs/semconv/http/http-metrics/ (Semantic conventions 1.44.0; references OpenTelemetry specification 1.59.0, retrieved 2026-08-17)
- HTTP semantic convention stability migration — https://opentelemetry.io/docs/specs/semconv/non-normative/http-migration/ (Stable HTTP migration from semantic conventions 1.23.1, retrieved 2026-08-17)


<!-- phase-3-for-agents:start -->
## For agents

For the current standard HTTP client request-duration metric, create a `Histogram` named `http.client.request.duration` with unit `s`. Record `http.request.method` and `server.address` as required attributes, using the values for the operation being measured. The server address is the domain name when it is available without a reverse DNS lookup; otherwise use the available IP address or UNIX domain socket name. Do not emit the historical `http.client.duration` metric, use milliseconds, or fall back to the older `http.method` and `net.peer.name` attribute names. The request-body and response-body size metrics documented alongside it are separate instruments, not substitutes for request duration.
<!-- phase-3-for-agents:end -->
---

<!-- source: http-metrics#__intro__ -->
# Semantic conventions for HTTP metrics

**Status**: Mixed

The conventions described in this section are HTTP specific. When HTTP operations occur, metric events about those operations will be generated and reported to provide insight into the operations. By adding HTTP attributes to metric events it allows for finely tuned filtering.

**Disclaimer:** These are initial HTTP metric instruments and attributes but more may be added in the future.
- HTTP server
- Metric: `http.server.request.duration`
- Metric: `http.server.active_requests`
- Metric: `http.server.request.body.size`
- Metric: `http.server.response.body.size`
- HTTP client
- Metric: `http.client.request.duration`
- Metric: `http.client.request.body.size`
- Metric: `http.client.response.body.size`
- Metric: `http.client.open_connections`
- Metric: `http.client.connection.duration`
- Metric: `http.client.active_requests`Important

Existing HTTP instrumentations that are using v1.20.0 of this document (or prior):
- SHOULD NOT change the version of the HTTP or networking conventions that they emit by default until the HTTP semantic conventions are marked stable (HTTP stabilization will include stabilization of a core set of networking conventions which are also used in HTTP instrumentations). Conventions include, but are not limited to, attributes, metric and span names, and unit of measure.
- SHOULD introduce an environment variable `OTEL_SEMCONV_STABILITY_OPT_IN` in the existing major version as a comma-separated list of category-specific values (e.g., http, databases, messaging). The list of values includes:
- `http` - emit the new, stable HTTP and networking conventions, and stop emitting the old experimental HTTP and networking conventions that the instrumentation emitted previously.
- `http/dup` - emit both the old and the stable HTTP and networking conventions, allowing for a seamless transition.
- The default behavior (in the absence of one of these values) is to continue emitting whatever version of the old experimental HTTP and networking conventions the instrumentation was emitting previously.
- Note: `http/dup` has higher precedence than `http` in case both values are present
- SHOULD maintain (security patching at a minimum) the existing major version for at least six months after it starts emitting both sets of conventions.
- SHOULD drop the environment variable in the next major version.

---

<!-- source: http-metrics#http-client -->
## HTTP client

### Metric: `http.client.request.duration`

This metric is recommended.

When this metric is reported alongside an HTTP client span, the metric value SHOULD be the same as the HTTP client span duration.

This metric SHOULD be specified with `ExplicitBucketBoundaries` advisory parameter of `[ 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10 ]`.

| Name | Instrument Type | Unit (UCUM) | Description | Stability | Entity Associations |
| --- | --- | --- | --- | --- | --- |
| `http.client.request.duration` | Histogram | `s` | Duration of HTTP client requests. | | |

**Attributes:**

| Key | Stability | Requirement Level | Value Type | Description | Example Values |
| --- | --- | --- | --- | --- | --- |
| `http.request.method` | | `Required` | string | HTTP request method. [1] | `GET`; `POST`; `HEAD` |
| `server.address` | | `Required` | string | Server domain name if available without reverse DNS lookup; otherwise, IP address or UNIX domain socket name. [2] | `example.com`; `10.1.2.80`; `/tmp/my.sock` |
| `server.port` | | `Required` | int | Server port number. [3] | `80`; `8080`; `443` |
| `error.type` | | `Conditionally Required` If request has ended with an error. | string | Describes a class of error the operation ended with. [4] | `timeout`; `java.net.UnknownHostException`; `server_certificate_invalid`; `500` |
| `http.response.status_code` | | `Conditionally Required` If and only if one was received/sent. | int | HTTP response status code. | `200` |
| `network.protocol.name` | | `Conditionally Required` [5] | string | OSI application layer or non-OSI equivalent. [6] | `http`; `spdy` |
| `network.protocol.version` | | `Recommended` | string | The actual version of the protocol used for network communication. [7] | `1.0`; `1.1`; `2`; `3` |
| `url.scheme` | | `Opt-In` | string | The URI scheme component identifying the used protocol. | `http`; `https` |
| `url.template` | | `Opt-In` | string | The low-cardinality template of an absolute path reference. [8] | `/users/{id}`; `/users/:id`; `/users?id={id}` |

**[1] `http.request.method`:** HTTP request method value SHOULD be “known” to the instrumentation. By default, this convention defines “known” methods as the ones listed in RFC9110, the PATCH method defined in RFC5789 and the QUERY method defined in httpbis-safe-method-w-body.

If the HTTP request method is not known to instrumentation, it MUST set the `http.request.method` attribute to `_OTHER`.

If the HTTP instrumentation could end up converting valid HTTP request methods to `_OTHER`, then it MUST provide a way to override the list of known HTTP methods. If this override is done via environment variable, then the environment variable MUST be named OTEL_INSTRUMENTATION_HTTP_KNOWN_METHODS and support a comma-separated list of case-sensitive known HTTP methods.

 If this override is done via declarative configuration, then the list MUST be configurable via the `known_methods` property (an array of case-sensitive strings with minimum items 0) under `.instrumentation/development.general.http.client` and/or `.instrumentation/development.general.http.server`.

In either case, this list MUST be a full override of the default known methods, it is not a list of known methods in addition to the defaults.

HTTP method names are case-sensitive and `http.request.method` attribute value MUST match a known HTTP method name exactly. Instrumentations for specific web frameworks that consider HTTP methods to be case insensitive, SHOULD populate a canonical equivalent. Tracing instrumentations that do so, MUST also set `http.request.method_original` to the original value.

**[2] `server.address`:** In HTTP/1.1, when the request target is passed in its absolute-form, the `server.address` SHOULD match the host component of the request target.

In all other cases, `server.address` SHOULD match the host component of the `Host` header in HTTP/1.1 or the `:authority` pseudo-header in HTTP/2 and HTTP/3.

**[3] `server.port`:** In the case of HTTP/1.1, when the request target is passed in its absolute-form, the `server.port` SHOULD match the port component of the request target.

In all other cases, `server.port` SHOULD match the port component of the `Host` header in HTTP/1.1 or the `:authority` pseudo-header in HTTP/2 and HTTP/3.

**[4] `error.type`:** If the request fails with an error before response status code was sent or received, `error.type` SHOULD be set to exception type (its fully-qualified class name, if applicable) or a component-specific low cardinality error identifier.

If response status code was sent or received and status indicates an error according to HTTP span status definition, `error.type` SHOULD be set to the status code number (represented as a string), an exception type (if thrown) or a component-specific error identifier.

The `error.type` value SHOULD be predictable and SHOULD have low cardinality. Instrumentations SHOULD document the list of errors they report.

The cardinality of `error.type` within one instrumentation library SHOULD be low, but telemetry consumers that aggregate data from multiple instrumentation libraries and applications should be prepared for `error.type` to have high cardinality at query time, when no additional filters are applied.

If the request has completed successfully, instrumentations SHOULD NOT set `error.type`.

**[5] `network.protocol.name`:** If not `http` and `network.protocol.version` is set.

**[6] `network.protocol.name`:** The value SHOULD be normalized to lowercase.

**[7] `network.protocol.version`:** If protocol version is subject to negotiation (for example using ALPN), this attribute SHOULD be set to the negotiated version. If the actual protocol version is not known, this attribute SHOULD NOT be set.

**[8] `url.template`:** The `url.template` MUST have low cardinality. It is not usually available on HTTP clients, but may be known by the application or specialized HTTP instrumentation.

`error.type` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `_OTHER` | A fallback error value to be used when the instrumentation doesn’t define a custom value. | |

`http.request.method` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `_OTHER` | Any HTTP method that the instrumentation has no prior knowledge of. | |
| `CONNECT` | CONNECT method. | |
| `DELETE` | DELETE method. | |
| `GET` | GET method. | |
| `HEAD` | HEAD method. | |
| `OPTIONS` | OPTIONS method. | |
| `PATCH` | PATCH method. | |
| `POST` | POST method. | |
| `PUT` | PUT method. | |
| `QUERY` | QUERY method. | |
| `TRACE` | TRACE method. | |

### Metric: `http.client.request.body.size`

This metric is opt-in.

| Name | Instrument Type | Unit (UCUM) | Description | Stability | Entity Associations |
| --- | --- | --- | --- | --- | --- |
| `http.client.request.body.size` | Histogram | `By` | Size of HTTP client request bodies. [1] | | |

**[1]:** The size of the request payload body in bytes. This is the number of bytes transferred excluding headers and is often, but not always, present as the Content-Length header. For requests using transport encoding, this should be the compressed size.

**Attributes:**

| Key | Stability | Requirement Level | Value Type | Description | Example Values |
| --- | --- | --- | --- | --- | --- |
| `http.request.method` | | `Required` | string | HTTP request method. [1] | `GET`; `POST`; `HEAD` |
| `server.address` | | `Required` | string | Server domain name if available without reverse DNS lookup; otherwise, IP address or UNIX domain socket name. [2] | `example.com`; `10.1.2.80`; `/tmp/my.sock` |
| `server.port` | | `Required` | int | Server port number. [3] | `80`; `8080`; `443` |
| `error.type` | | `Conditionally Required` If request has ended with an error. | string | Describes a class of error the operation ended with. [4] | `timeout`; `java.net.UnknownHostException`; `server_certificate_invalid`; `500` |
| `http.response.status_code` | | `Conditionally Required` If and only if one was received/sent. | int | HTTP response status code. | `200` |
| `network.protocol.name` | | `Conditionally Required` [5] | string | OSI application layer or non-OSI equivalent. [6] | `http`; `spdy` |
| `url.template` | | `Conditionally Required` If available. | string | The low-cardinality template of an absolute path reference. [7] | `/users/{id}`; `/users/:id`; `/users?id={id}` |
| `network.protocol.version` | | `Recommended` | string | The actual version of the protocol used for network communication. [8] | `1.0`; `1.1`; `2`; `3` |
| `url.scheme` | | `Opt-In` | string | The URI scheme component identifying the used protocol. | `http`; `https` |

**[1] `http.request.method`:** HTTP request method value SHOULD be “known” to the instrumentation. By default, this convention defines “known” methods as the ones listed in RFC9110, the PATCH method defined in RFC5789 and the QUERY method defined in httpbis-safe-method-w-body.

If the HTTP request method is not known to instrumentation, it MUST set the `http.request.method` attribute to `_OTHER`.

If the HTTP instrumentation could end up converting valid HTTP request methods to `_OTHER`, then it MUST provide a way to override the list of known HTTP methods. If this override is done via environment variable, then the environment variable MUST be named OTEL_INSTRUMENTATION_HTTP_KNOWN_METHODS and support a comma-separated list of case-sensitive known HTTP methods.

 If this override is done via declarative configuration, then the list MUST be configurable via the `known_methods` property (an array of case-sensitive strings with minimum items 0) under `.instrumentation/development.general.http.client` and/or `.instrumentation/development.general.http.server`.

In either case, this list MUST be a full override of the default known methods, it is not a list of known methods in addition to the defaults.

HTTP method names are case-sensitive and `http.request.method` attribute value MUST match a known HTTP method name exactly. Instrumentations for specific web frameworks that consider HTTP methods to be case insensitive, SHOULD populate a canonical equivalent. Tracing instrumentations that do so, MUST also set `http.request.method_original` to the original value.

**[2] `server.address`:** In HTTP/1.1, when the request target is passed in its absolute-form, the `server.address` SHOULD match the host component of the request target.

In all other cases, `server.address` SHOULD match the host component of the `Host` header in HTTP/1.1 or the `:authority` pseudo-header in HTTP/2 and HTTP/3.

**[3] `server.port`:** In the case of HTTP/1.1, when the request target is passed in its absolute-form, the `server.port` SHOULD match the port component of the request target.

In all other cases, `server.port` SHOULD match the port component of the `Host` header in HTTP/1.1 or the `:authority` pseudo-header in HTTP/2 and HTTP/3.

**[4] `error.type`:** If the request fails with an error before response status code was sent or received, `error.type` SHOULD be set to exception type (its fully-qualified class name, if applicable) or a component-specific low cardinality error identifier.

If response status code was sent or received and status indicates an error according to HTTP span status definition, `error.type` SHOULD be set to the status code number (represented as a string), an exception type (if thrown) or a component-specific error identifier.

The `error.type` value SHOULD be predictable and SHOULD have low cardinality. Instrumentations SHOULD document the list of errors they report.

The cardinality of `error.type` within one instrumentation library SHOULD be low, but telemetry consumers that aggregate data from multiple instrumentation libraries and applications should be prepared for `error.type` to have high cardinality at query time, when no additional filters are applied.

If the request has completed successfully, instrumentations SHOULD NOT set `error.type`.

**[5] `network.protocol.name`:** If not `http` and `network.protocol.version` is set.

**[6] `network.protocol.name`:** The value SHOULD be normalized to lowercase.

**[7] `url.template`:** The `url.template` MUST have low cardinality. It is not usually available on HTTP clients, but may be known by the application or specialized HTTP instrumentation.

**[8] `network.protocol.version`:** If protocol version is subject to negotiation (for example using ALPN), this attribute SHOULD be set to the negotiated version. If the actual protocol version is not known, this attribute SHOULD NOT be set.

`error.type` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `_OTHER` | A fallback error value to be used when the instrumentation doesn’t define a custom value. | |

`http.request.method` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `_OTHER` | Any HTTP method that the instrumentation has no prior knowledge of. | |
| `CONNECT` | CONNECT method. | |
| `DELETE` | DELETE method. | |
| `GET` | GET method. | |
| `HEAD` | HEAD method. | |
| `OPTIONS` | OPTIONS method. | |
| `PATCH` | PATCH method. | |
| `POST` | POST method. | |
| `PUT` | PUT method. | |
| `QUERY` | QUERY method. | |
| `TRACE` | TRACE method. | |

### Metric: `http.client.response.body.size`

This metric is opt-in.

| Name | Instrument Type | Unit (UCUM) | Description | Stability | Entity Associations |
| --- | --- | --- | --- | --- | --- |
| `http.client.response.body.size` | Histogram | `By` | Size of HTTP client response bodies. [1] | | |

**[1]:** The size of the response payload body in bytes. This is the number of bytes transferred excluding headers and is often, but not always, present as the Content-Length header. For requests using transport encoding, this should be the compressed size.

**Attributes:**

| Key | Stability | Requirement Level | Value Type | Description | Example Values |
| --- | --- | --- | --- | --- | --- |
| `http.request.method` | | `Required` | string | HTTP request method. [1] | `GET`; `POST`; `HEAD` |
| `server.address` | | `Required` | string | Server domain name if available without reverse DNS lookup; otherwise, IP address or UNIX domain socket name. [2] | `example.com`; `10.1.2.80`; `/tmp/my.sock` |
| `server.port` | | `Required` | int | Server port number. [3] | `80`; `8080`; `443` |
| `error.type` | | `Conditionally Required` If request has ended with an error. | string | Describes a class of error the operation ended with. [4] | `timeout`; `java.net.UnknownHostException`; `server_certificate_invalid`; `500` |
| `http.response.status_code` | | `Conditionally Required` If and only if one was received/sent. | int | HTTP response status code. | `200` |
| `network.protocol.name` | | `Conditionally Required` [5] | string | OSI application layer or non-OSI equivalent. [6] | `http`; `spdy` |
| `url.template` | | `Conditionally Required` If available. | string | The low-cardinality template of an absolute path reference. [7] | `/users/{id}`; `/users/:id`; `/users?id={id}` |
| `network.protocol.version` | | `Recommended` | string | The actual version of the protocol used for network communication. [8] | `1.0`; `1.1`; `2`; `3` |
| `url.scheme` | | `Opt-In` | string | The URI scheme component identifying the used protocol. | `http`; `https` |

**[1] `http.request.method`:** HTTP request method value SHOULD be “known” to the instrumentation. By default, this convention defines “known” methods as the ones listed in RFC9110, the PATCH method defined in RFC5789 and the QUERY method defined in httpbis-safe-method-w-body.

If the HTTP request method is not known to instrumentation, it MUST set the `http.request.method` attribute to `_OTHER`.

If the HTTP instrumentation could end up converting valid HTTP request methods to `_OTHER`, then it MUST provide a way to override the list of known HTTP methods. If this override is done via environment variable, then the environment variable MUST be named OTEL_INSTRUMENTATION_HTTP_KNOWN_METHODS and support a comma-separated list of case-sensitive known HTTP methods.

 If this override is done via declarative configuration, then the list MUST be configurable via the `known_methods` property (an array of case-sensitive strings with minimum items 0) under `.instrumentation/development.general.http.client` and/or `.instrumentation/development.general.http.server`.

In either case, this list MUST be a full override of the default known methods, it is not a list of known methods in addition to the defaults.

HTTP method names are case-sensitive and `http.request.method` attribute value MUST match a known HTTP method name exactly. Instrumentations for specific web frameworks that consider HTTP methods to be case insensitive, SHOULD populate a canonical equivalent. Tracing instrumentations that do so, MUST also set `http.request.method_original` to the original value.

**[2] `server.address`:** In HTTP/1.1, when the request target is passed in its absolute-form, the `server.address` SHOULD match the host component of the request target.

In all other cases, `server.address` SHOULD match the host component of the `Host` header in HTTP/1.1 or the `:authority` pseudo-header in HTTP/2 and HTTP/3.

**[3] `server.port`:** In the case of HTTP/1.1, when the request target is passed in its absolute-form, the `server.port` SHOULD match the port component of the request target.

In all other cases, `server.port` SHOULD match the port component of the `Host` header in HTTP/1.1 or the `:authority` pseudo-header in HTTP/2 and HTTP/3.

**[4] `error.type`:** If the request fails with an error before response status code was sent or received, `error.type` SHOULD be set to exception type (its fully-qualified class name, if applicable) or a component-specific low cardinality error identifier.

If response status code was sent or received and status indicates an error according to HTTP span status definition, `error.type` SHOULD be set to the status code number (represented as a string), an exception type (if thrown) or a component-specific error identifier.

The `error.type` value SHOULD be predictable and SHOULD have low cardinality. Instrumentations SHOULD document the list of errors they report.

The cardinality of `error.type` within one instrumentation library SHOULD be low, but telemetry consumers that aggregate data from multiple instrumentation libraries and applications should be prepared for `error.type` to have high cardinality at query time, when no additional filters are applied.

If the request has completed successfully, instrumentations SHOULD NOT set `error.type`.

**[5] `network.protocol.name`:** If not `http` and `network.protocol.version` is set.

**[6] `network.protocol.name`:** The value SHOULD be normalized to lowercase.

**[7] `url.template`:** The `url.template` MUST have low cardinality. It is not usually available on HTTP clients, but may be known by the application or specialized HTTP instrumentation.

**[8] `network.protocol.version`:** If protocol version is subject to negotiation (for example using ALPN), this attribute SHOULD be set to the negotiated version. If the actual protocol version is not known, this attribute SHOULD NOT be set.

`error.type` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `_OTHER` | A fallback error value to be used when the instrumentation doesn’t define a custom value. | |

`http.request.method` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `_OTHER` | Any HTTP method that the instrumentation has no prior knowledge of. | |
| `CONNECT` | CONNECT method. | |
| `DELETE` | DELETE method. | |
| `GET` | GET method. | |
| `HEAD` | HEAD method. | |
| `OPTIONS` | OPTIONS method. | |
| `PATCH` | PATCH method. | |
| `POST` | POST method. | |
| `PUT` | PUT method. | |
| `QUERY` | QUERY method. | |
| `TRACE` | TRACE method. | |

### Metric: `http.client.open_connections`

This metric is opt-in.

| Name | Instrument Type | Unit (UCUM) | Description | Stability | Entity Associations |
| --- | --- | --- | --- | --- | --- |
| `http.client.open_connections` | UpDownCounter | `{connection}` | Number of outbound HTTP connections that are currently active or idle on the client. | | |

**Attributes:**

| Key | Stability | Requirement Level | Value Type | Description | Example Values |
| --- | --- | --- | --- | --- | --- |
| `http.connection.state` | | `Required` | string | State of the HTTP connection in the HTTP connection pool. | `active`; `idle` |
| `server.address` | | `Required` | string | Server domain name if available without reverse DNS lookup; otherwise, IP address or UNIX domain socket name. [1] | `example.com`; `10.1.2.80`; `/tmp/my.sock` |
| `server.port` | | `Required` | int | Server port number. [2] | `80`; `8080`; `443` |
| `network.protocol.version` | | `Recommended` | string | The actual version of the protocol used for network communication. [3] | `1.1`; `2` |
| `network.peer.address` | | `Opt-In` | string | Peer address of the network connection - IP address or UNIX domain socket name. | `10.1.2.80`; `/tmp/my.sock` |
| `url.scheme` | | `Opt-In` | string | The URI scheme component identifying the used protocol. | `http`; `https` |

**[1] `server.address`:** When observed from the client side, and when communicating through an intermediary, `server.address` SHOULD represent the server address behind any intermediaries, for example proxies, if it’s available.

**[2] `server.port`:** When observed from the client side, and when communicating through an intermediary, `server.port` SHOULD represent the server port behind any intermediaries, for example proxies, if it’s available.

**[3] `network.protocol.version`:** If protocol version is subject to negotiation (for example using ALPN), this attribute SHOULD be set to the negotiated version. If the actual protocol version is not known, this attribute SHOULD NOT be set.

`http.connection.state` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `active` | active state. | |
| `idle` | idle state. | |

### Metric: `http.client.connection.duration`

This metric SHOULD be specified with `ExplicitBucketBoundaries` advisory parameter of `[ 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 30, 60, 120, 300 ]`.

This metric is opt-in.

| Name | Instrument Type | Unit (UCUM) | Description | Stability | Entity Associations |
| --- | --- | --- | --- | --- | --- |
| `http.client.connection.duration` | Histogram | `s` | The duration of the successfully established outbound HTTP connections. | | |

**Attributes:**

| Key | Stability | Requirement Level | Value Type | Description | Example Values |
| --- | --- | --- | --- | --- | --- |
| `server.address` | | `Required` | string | Server domain name if available without reverse DNS lookup; otherwise, IP address or UNIX domain socket name. [1] | `example.com`; `10.1.2.80`; `/tmp/my.sock` |
| `server.port` | | `Required` | int | Server port number. [2] | `80`; `8080`; `443` |
| `network.protocol.version` | | `Recommended` | string | The actual version of the protocol used for network communication. [3] | `1.1`; `2` |
| `network.peer.address` | | `Opt-In` | string | Peer address of the network connection - IP address or UNIX domain socket name. | `10.1.2.80`; `/tmp/my.sock` |
| `url.scheme` | | `Opt-In` | string | The URI scheme component identifying the used protocol. | `http`; `https` |

**[1] `server.address`:** When observed from the client side, and when communicating through an intermediary, `server.address` SHOULD represent the server address behind any intermediaries, for example proxies, if it’s available.

**[2] `server.port`:** When observed from the client side, and when communicating through an intermediary, `server.port` SHOULD represent the server port behind any intermediaries, for example proxies, if it’s available.

**[3] `network.protocol.version`:** If protocol version is subject to negotiation (for example using ALPN), this attribute SHOULD be set to the negotiated version. If the actual protocol version is not known, this attribute SHOULD NOT be set.

### Metric: `http.client.active_requests`

**Status**: Development

This metric is opt-in.

| Name | Instrument Type | Unit (UCUM) | Description | Stability | Entity Associations |
| --- | --- | --- | --- | --- | --- |
| `http.client.active_requests` | UpDownCounter | `{request}` | Number of active HTTP requests. | | |

**Attributes:**

| Key | Stability | Requirement Level | Value Type | Description | Example Values |
| --- | --- | --- | --- | --- | --- |
| `server.address` | | `Required` | string | Server domain name if available without reverse DNS lookup; otherwise, IP address or UNIX domain socket name. [1] | `example.com`; `10.1.2.80`; `/tmp/my.sock` |
| `server.port` | | `Required` | int | Server port number. [2] | `80`; `8080`; `443` |
| `url.template` | | `Conditionally Required` If available. | string | The low-cardinality template of an absolute path reference. [3] | `/users/{id}`; `/users/:id`; `/users?id={id}` |
| `http.request.method` | | `Recommended` | string | HTTP request method. [4] | `GET`; `POST`; `HEAD` |
| `url.scheme` | | `Opt-In` | string | The URI scheme component identifying the used protocol. | `http`; `https` |

**[1] `server.address`:** In HTTP/1.1, when the request target is passed in its absolute-form, the `server.address` SHOULD match the host component of the request target.

In all other cases, `server.address` SHOULD match the host component of the `Host` header in HTTP/1.1 or the `:authority` pseudo-header in HTTP/2 and HTTP/3.

**[2] `server.port`:** In the case of HTTP/1.1, when the request target is passed in its absolute-form, the `server.port` SHOULD match the port component of the request target.

In all other cases, `server.port` SHOULD match the port component of the `Host` header in HTTP/1.1 or the `:authority` pseudo-header in HTTP/2 and HTTP/3.

**[3] `url.template`:** The `url.template` MUST have low cardinality. It is not usually available on HTTP clients, but may be known by the application or specialized HTTP instrumentation.

**[4] `http.request.method`:** HTTP request method value SHOULD be “known” to the instrumentation. By default, this convention defines “known” methods as the ones listed in RFC9110, the PATCH method defined in RFC5789 and the QUERY method defined in httpbis-safe-method-w-body.

If the HTTP request method is not known to instrumentation, it MUST set the `http.request.method` attribute to `_OTHER`.

If the HTTP instrumentation could end up converting valid HTTP request methods to `_OTHER`, then it MUST provide a way to override the list of known HTTP methods. If this override is done via environment variable, then the environment variable MUST be named OTEL_INSTRUMENTATION_HTTP_KNOWN_METHODS and support a comma-separated list of case-sensitive known HTTP methods.

 If this override is done via declarative configuration, then the list MUST be configurable via the `known_methods` property (an array of case-sensitive strings with minimum items 0) under `.instrumentation/development.general.http.client` and/or `.instrumentation/development.general.http.server`.

In either case, this list MUST be a full override of the default known methods, it is not a list of known methods in addition to the defaults.

HTTP method names are case-sensitive and `http.request.method` attribute value MUST match a known HTTP method name exactly. Instrumentations for specific web frameworks that consider HTTP methods to be case insensitive, SHOULD populate a canonical equivalent. Tracing instrumentations that do so, MUST also set `http.request.method_original` to the original value.

`http.request.method` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `_OTHER` | Any HTTP method that the instrumentation has no prior knowledge of. | |
| `CONNECT` | CONNECT method. | |
| `DELETE` | DELETE method. | |
| `GET` | GET method. | |
| `HEAD` | HEAD method. | |
| `OPTIONS` | OPTIONS method. | |
| `PATCH` | PATCH method. | |
| `POST` | POST method. | |
| `PUT` | PUT method. | |
| `QUERY` | QUERY method. | |
| `TRACE` | TRACE method. | |

.feedback--answer{display:inline-block}.feedback--answer-no{margin-left:1em}.feedback--response{display:none;margin-top:1em}.feedback--response__visible{display:block}

---

<!-- source: http-migration#__intro__ -->
# HTTP semantic convention stability migration

Due to the significant number of modifications and the extensive user base affected by them, existing HTTP instrumentations published by OpenTelemetry are required to implement a migration plan that will assist users in transitioning to the stable HTTP semantic conventions.

Specifically, when existing HTTP instrumentations published by OpenTelemetry are updated to the stable HTTP semantic conventions, they:
- SHOULD introduce an environment variable `OTEL_SEMCONV_STABILITY_OPT_IN` in their existing major version, which accepts:
- `http` - emit the stable HTTP and networking conventions, and stop emitting the old HTTP and networking conventions that the instrumentation emitted previously.
- `http/dup` - emit both the old and the stable HTTP and networking conventions, allowing for a phased rollout of the stable semantic conventions.
- The default behavior (in the absence of one of these values) is to continue emitting whatever version of the old HTTP and networking conventions the instrumentation was emitting previously.
- Need to maintain (security patching at a minimum) their existing major version for at least six months after it starts emitting both sets of conventions.
- May drop the environment variable in their next major version and emit only the stable HTTP and networking conventions.Note

`OTEL_SEMCONV_STABILITY_OPT_IN` is only intended to be used when migrating from an experimental semantic convention to its initial stable version.

---

<!-- source: http-migration#summary-of-changes -->
## Summary of changes

This section summarizes the changes made to the HTTP semantic conventions from v1.20.0 to v1.23.1 (stable).

### Common attributes across HTTP client and server spans

| Change | Comments |
| --- | --- |
| `http.method` → `http.request.method` | Now captures only 9 common HTTP methods by default (configurable) plus `_OTHER` |
| `http.status_code` → `http.response.status_code` | |
| `http.request.header.<key>` | • Dash (`"-"`) to underscore (`"_"`) normalization in `<key>` has been removed • On HTTP server spans: now must be provided to sampler |
| `http.response.header.<key>` | Dash (`"-"`) to underscore (`"_"`) normalization in `<key>` has been removed |
| `http.request_content_length` → `http.request.body.size` | • Recommended → Opt-In • *Not marked stable yet* |
| `http.response_content_length` → `http.response.body.size` | • Recommended → Opt-In • *Not marked stable yet* |
| `user_agent.original` | • On HTTP client spans: Recommended → Opt-In • On HTTP server spans: now must be provided to sampler • See note if migrating from <= v1.18.0 |
| `net.protocol.name` → `network.protocol.name` | Recommended → Conditionally required if not `http` and `network.protocol.version` is set |
| `net.protocol.version` → `network.protocol.version` | • Examples fixed: `2.0` → `2` and `3.0` → `3` • See note if migrating from <= v1.19.0 |
| `net.sock.family` | Removed |
| `net.sock.peer.addr` → `network.peer.address` | On HTTP server spans: if `http.client_ip` was unknown, then also `net.sock.peer.addr` → `client.address`; `client.address` must be provided to sampler |
| `net.sock.peer.port` → `network.peer.port` | Now captured even if same as `server.port` |
| `net.sock.peer.name` | Removed |
| New: `http.request.method_original` | Only captured when `http.request.method` is `_OTHER` |
| New: `error.type` | |

References:
- Common attributes v1.20.0
- Common attributes v1.23.1 (stable)

### HTTP client span attributes

| Change | Comments |
| --- | --- |
| `http.url` → `url.full` | |
| `http.resend_count` → `http.request.resend_count` | |
| `net.peer.name` → `server.address` | |
| `net.peer.port` → `server.port` | Now captured even when same as default port for scheme |

References:
- HTTP client span attributes v1.20.0
- HTTP client span attributes v1.23.1 (stable)

### HTTP server span attributes

| Change | Comments |
| --- | --- |
| `http.route` | No change |
| `http.target` → `url.path` and `url.query` | Split into two separate attributes |
| `http.scheme` → `url.scheme` | Now factors in X-Forwarded-Proto, Forwarded#proto headers |
| `http.client_ip` → `client.address` | If `http.client_ip` was unknown (i.e., no X-Forwarded-For, Forwarded#for headers), then `net.sock.peer.addr` → `client.address`; now must be provided to sampler |
| `net.host.name` → `server.address` | Now based only on Host, :authority, X-Forwarded-Host, Forwarded#host headers |
| `net.host.port` → `server.port` | • Now based only on Host, :authority, X-Forwarded-Host, Forwarded#host headers • Now captured even when same as default port for scheme |
| `net.sock.host.addr` → `network.local.address` | |
| `net.sock.host.port` → `network.local.port` | No longer defaults to `server.port` when `network.local.address` is set. |

References:
- HTTP server span attributes v1.20.0
- HTTP server span attributes v1.23.1 (stable)

### HTTP client and server span names

The `{http.method}` portion of span names is replace by `HTTP` when `{http.method}` is `_OTHER`.

See note if migrating from `<= v1.17.0`.

References:
- HTTP client and server span names v1.20.0
- HTTP client and server span names v1.23.1 (stable)

### HTTP client duration metric

Metric changes:
- **Name**: `http.client.duration` → `http.client.request.duration`
- **Unit**: `ms` → `s`
- **Description**: `Measures the duration of outbound HTTP requests.` → `Duration of HTTP client requests.`
- **Histogram buckets**: boundaries updated to reflect change from milliseconds to seconds, and zero bucket boundary removed
- **Attributes**: see table below

| Attribute change | Comments |
| --- | --- |
| `http.method` → `http.request.method` | Now captures only 9 common HTTP methods by default plus `_OTHER` |
| `http.status_code` → `http.response.status_code` | |
| `net.peer.name` → `server.address` | |
| `net.peer.port` → `server.port` | Now captured even when same as default port for scheme |
| `net.sock.peer.addr` | Removed |
| `net.protocol.name` → `network.protocol.name` | Recommended → Conditionally required if not `http` and `network.protocol.version` is set |
| `net.protocol.version` → `network.protocol.version` | Examples fixed: `2.0` → `2` and `3.0` → `3`; see note if migrating from `<= v1.19.0` |
| New: `error.type` | |

References:
- Metric `http.client.duration` v1.20.0
- Metric `http.client.request.duration` v1.23.1 (stable)

### HTTP server duration metric

Metric changes:
- **Name**: `http.server.duration` → `http.server.request.duration`
- **Unit**: `ms` → `s`
- **Description**: `Measures the duration of inbound HTTP requests.` → `Duration of HTTP server requests.`
- **Histogram buckets**: boundaries updated to reflect change from milliseconds to seconds, and zero bucket boundary removed
- **Attributes**: see table below

| Attribute change | Comments |
| --- | --- |
| `http.route` | No change |
| `http.method` → `http.request.method` | Now captures only 9 common HTTP methods by default plus `_OTHER` |
| `http.status_code` → `http.response.status_code` | |
| `http.scheme` → `url.scheme` | Now factors in `X-Forwarded-Proto` span, `Forwarded#proto` span headers |
| `net.protocol.name` → `network.protocol.name` | Recommended → Conditionally required if not `http` and `network.protocol.version` is set |
| `net.protocol.version` → `network.protocol.version` | Examples fixed: `2.0` → `2` and `3.0` → `3`; see note if migrating from `<= v1.19.0` |
| `net.host.name` → `server.address` | • Recommended → Opt-In (due to high-cardinality vulnerability since based on HTTP headers) • Now based only on `Host` span, `:authority` span, `X-Forwarded-Host` span, `Forwarded#host` span headers |
| `net.host.port` → `server.port` | • Recommended → Opt-In (due to high-cardinality vulnerability since based on HTTP headers) • Now based only on `Host` span, `:authority` span, `X-Forwarded-Host` span, `Forwarded#host` span headers |
| New: `error.type` | |

References:
- Metric `http.server.duration` v1.20.0
- Metric `http.server.request.duration` v1.23.1 (stable)
