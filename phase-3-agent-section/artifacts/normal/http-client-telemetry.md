# Documentation bundle — HTTP client request telemetry

Frozen authoritative OpenTelemetry documentation. Source sections are preserved in source order.

Sources:
- Semantic conventions for HTTP spans — https://opentelemetry.io/docs/specs/semconv/http/http-spans/ (Semantic conventions 1.44.0; references OpenTelemetry specification 1.59.0, retrieved 2026-08-17)
- HTTP semantic convention stability migration — https://opentelemetry.io/docs/specs/semconv/non-normative/http-migration/ (Stable HTTP migration from semantic conventions 1.23.1, retrieved 2026-08-17)

---

<!-- source: http-spans#__intro__ -->
# Semantic conventions for HTTP spans

**Status**: Stable, Unless otherwise specified.

This document defines semantic conventions for HTTP client and server Spans. They can be used for HTTP and HTTPS schemes and various HTTP versions like 1.1, 2 and SPDY.
- Name
- Status
- HTTP client span
- HTTP client span duration
- HTTP request retries and redirects
- HTTP server
- HTTP server definitions
- Setting `server.address` and `server.port` attributes
- Simple client/server example
- Client/server example with reverse proxy
- HTTP server span
- Examples
- HTTP client-server example
- HTTP client retries examples
- HTTP client authorization retry examples
- HTTP client redirects examples
- HTTP client call: DNS error
- HTTP client call: Internal Server Error
- HTTP server call: connection dropped before response body was sentImportant

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

<!-- source: http-spans#name -->
## Name

HTTP spans MUST follow the overall guidelines for span names.

HTTP span names SHOULD be `{method} {target}` if there is a (low-cardinality) `target` available. If there is no (low-cardinality) `{target}` available, HTTP span names SHOULD be `{method}`.

(see below for the exact definition of the `{method}` and `{target}` placeholders).

The `{method}` MUST be `{http.request.method}` if the method represents the original method known to the instrumentation. In other cases (when `{http.request.method}` is set to `_OTHER`), `{method}` MUST be `HTTP`.

The `{target}` SHOULD be one of the following:
- `http.route` for HTTP Server spans
- `url.template` for HTTP Client spans if enabled and available ()
- Other value MAY be provided through custom hooks at span start time or later.

Instrumentation MUST NOT default to using URI path as a `{target}`.

---

<!-- source: http-spans#status -->
## Status

Span Status MUST be left unset if HTTP status code was in the 1xx, 2xx or 3xx ranges, unless there was another error (e.g., network error receiving the response body; or 3xx codes with max redirects exceeded), in which case status MUST be set to `Error`.Note

The classification of an HTTP status code as an error depends on the context. For example, a 404 “Not Found” status code indicates an error if the application expected the resource to be available. However, it is not an error when the application is simply checking whether the resource exists.

Instrumentations that have additional context about a specific request MAY use this context to set the span status more precisely. Instrumentations that don’t have any additional context MUST follow the guidelines in this section.

For HTTP status codes in the 4xx range span status MUST be left unset in case of `SpanKind.SERVER` and SHOULD be set to `Error` in case of `SpanKind.CLIENT`.

For HTTP status codes in the 5xx range, as well as any other code the client failed to interpret, span status SHOULD be set to `Error`.

Don’t set the span status description if the reason can be inferred from `http.response.status_code`.

HTTP request may fail if an error occurred preventing the client or server from sending/receiving the request/response fully.

When instrumentation detects such errors it SHOULD set span status to `Error` and SHOULD set the `error.type` attribute.

If the HTTP client instrumentation can detect that the request was cancelled intentionally by the caller (e.g., via context cancellation or an abort signal), the cancellation SHOULD NOT be treated as an error: the span status SHOULD be left unset and `error.type` SHOULD NOT be set.

**Status**: Development - Refer to the Recording Errors document for general considerations on how to record span status.

---

<!-- source: http-spans#http-client-span -->
## HTTP client span

**Status:**

This span represents an outbound HTTP request.

There are two ways HTTP client spans can be implemented in an instrumentation:
-

Instrumentations SHOULD create an HTTP span for each attempt to send an HTTP request over the wire. In case the request is resent, the resend attempts MUST follow the HTTP resend spec. In this case, instrumentations SHOULD NOT (also) emit a logical encompassing HTTP client span.
-

If for some reason it is not possible to emit a span for each send attempt (because e.g. the instrumented library does not expose hooks that would allow this), instrumentations MAY create an HTTP span for the top-most operation of the HTTP client. In this case, the `url.full` MUST be the absolute URL that was originally requested, before any HTTP-redirects that may happen when executing the request.

**Span name:** refer to the Span Name section.

**Span kind** MUST be `CLIENT`.

**Span status:** refer to the Span Status section.

**Attributes:**

| Key | Stability | Requirement Level | Value Type | Description | Example Values |
| --- | --- | --- | --- | --- | --- |
| `http.request.method` | | `Required` | string | HTTP request method. [1] | `GET`; `POST`; `HEAD` |
| `server.address` | | `Required` | string | Server domain name if available without reverse DNS lookup; otherwise, IP address or UNIX domain socket name. [2] | `example.com`; `10.1.2.80`; `/tmp/my.sock` |
| `server.port` | | `Required` | int | Server port number. [3] | `80`; `8080`; `443` |
| `url.full` | | `Required` | string | Absolute URL describing a network resource according to RFC3986 [4] | `https://www.foo.bar/search?q=OpenTelemetry#SemConv`; `//localhost` |
| `error.type` | | `Conditionally Required` If request has ended with an error. | string | Describes a class of error the operation ended with. [5] | `timeout`; `java.net.UnknownHostException`; `server_certificate_invalid`; `500` |
| `http.request.method_original` | | `Conditionally Required` [6] | string | Original HTTP method sent by the client in the request line. | `GeT`; `ACL`; `foo` |
| `http.response.status_code` | | `Conditionally Required` If and only if one was received/sent. | int | HTTP response status code. | `200` |
| `network.protocol.name` | | `Conditionally Required` [7] | string | OSI application layer or non-OSI equivalent. [8] | `http`; `spdy` |
| `http.request.resend_count` | | `Recommended` if and only if request was retried. | int | The ordinal number of request resending attempt (for any reason, including redirects). [9] | `3` |
| `network.peer.address` | | `Recommended` | string | Peer address of the network connection - IP address or UNIX domain socket name. | `10.1.2.80`; `/tmp/my.sock` |
| `network.peer.port` | | `Recommended` If `network.peer.address` is set. | int | Peer port number of the network connection. | `65123` |
| `network.protocol.version` | | `Recommended` | string | The actual version of the protocol used for network communication. [10] | `1.0`; `1.1`; `2`; `3` |
| `http.request.body.size` | | `Opt-In` | int | The size of the request payload body in bytes. This is the number of bytes transferred excluding headers and is often, but not always, present as the Content-Length header. For requests using transport encoding, this should be the compressed size. | `3495` |
| `http.request.header.<key>` | | `Opt-In` | string[] | HTTP request headers, `<key>` being the normalized HTTP Header name (lowercase), the value being the header values. [11] | `["application/json"]`; `["1.2.3.4", "1.2.3.5"]` |
| `http.request.size` | | `Opt-In` | int | The total size of the request in bytes. This should be the total number of bytes sent over the wire, including the request line (HTTP/1.1), framing (HTTP/2 and HTTP/3), headers, and request body if any. | `1437` |
| `http.response.body.size` | | `Opt-In` | int | The size of the response payload body in bytes. This is the number of bytes transferred excluding headers and is often, but not always, present as the Content-Length header. For requests using transport encoding, this should be the compressed size. | `3495` |
| `http.response.header.<key>` | | `Opt-In` | string[] | HTTP response headers, `<key>` being the normalized HTTP Header name (lowercase), the value being the header values. [12] | `["application/json"]`; `["abc", "def"]` |
| `http.response.size` | | `Opt-In` | int | The total size of the response in bytes. This should be the total number of bytes sent over the wire, including the status line (HTTP/1.1), framing (HTTP/2 and HTTP/3), headers, and response body and trailers if any. | `1437` |
| `network.transport` | | `Opt-In` | string | OSI transport layer or inter-process communication method. [13] | `tcp`; `udp` |
| `url.scheme` | | `Opt-In` | string | The URI scheme component identifying the used protocol. | `http`; `https` |
| `url.template` | | `Opt-In` | string | The low-cardinality template of an absolute path reference. [14] | `/users/{id}`; `/users/:id`; `/users?id={id}` |
| `user_agent.original` | | `Opt-In` | string | Value of the HTTP User-Agent header sent by the client. | `CERN-LineMode/2.15 libwww/2.17b3`; `Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1`; `YourApp/1.0.0 grpc-java-okhttp/1.27.2` |
| `user_agent.synthetic.type` | | `Opt-In` | string | Specifies the category of synthetic traffic, such as tests or bots. [15] | `bot`; `test` |

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

**[4] `url.full`:** For network calls, URL usually has `scheme://host[:port][path][?query][#fragment]` format, where the fragment is not transmitted over HTTP, but if it is known, it SHOULD be included nevertheless.

`url.full` MUST NOT contain credentials passed via URL in form of `https://username:password@www.example.com/`. In such case username and password SHOULD be redacted and attribute’s value SHOULD be `https://REDACTED:REDACTED@www.example.com/`.

`url.full` SHOULD capture the absolute URL when it is available (or can be reconstructed).

Sensitive content provided in `url.full` SHOULD be scrubbed when instrumentations can identify it.

 Query string values for the following keys SHOULD be redacted by default and replaced by the value `REDACTED`:
- `X-Amz-Signature`
- `X-Amz-Credential`
- `X-Amz-Security-Token`
- `sig`
- `X-Goog-Signature`

This list is subject to change over time.

Matching of query parameter keys against the sensitive list SHOULD be case-sensitive.

 Instrumentation MAY provide a way to override this list via declarative configuration. If so, it SHOULD use the `sensitive_query_parameters` property (an array of case-sensitive strings with minimum items 0) under `.instrumentation/development.general.sanitization.url`. This list is a full override of the default sensitive query parameter keys, it is not a list of keys in addition to the defaults.

When a query string value is redacted, the query string key SHOULD still be preserved, e.g. `https://www.example.com/path?color=blue&sig=REDACTED`.

**[5] `error.type`:** If the request fails with an error before response status code was sent or received, `error.type` SHOULD be set to exception type (its fully-qualified class name, if applicable) or a component-specific low cardinality error identifier.

If response status code was sent or received and status indicates an error according to HTTP span status definition, `error.type` SHOULD be set to the status code number (represented as a string), an exception type (if thrown) or a component-specific error identifier.

The `error.type` value SHOULD be predictable and SHOULD have low cardinality. Instrumentations SHOULD document the list of errors they report.

The cardinality of `error.type` within one instrumentation library SHOULD be low, but telemetry consumers that aggregate data from multiple instrumentation libraries and applications should be prepared for `error.type` to have high cardinality at query time, when no additional filters are applied.

If the request has completed successfully, instrumentations SHOULD NOT set `error.type`.

**[6] `http.request.method_original`:** If and only if it’s different than `http.request.method`.

**[7] `network.protocol.name`:** If not `http` and `network.protocol.version` is set.

**[8] `network.protocol.name`:** The value SHOULD be normalized to lowercase.

**[9] `http.request.resend_count`:** The resend count SHOULD be updated each time an HTTP request gets resent by the client, regardless of what was the cause of the resending (e.g. redirection, authorization failure, 503 Server Unavailable, network issues, or any other).

**[10] `network.protocol.version`:** If protocol version is subject to negotiation (for example using ALPN), this attribute SHOULD be set to the negotiated version. If the actual protocol version is not known, this attribute SHOULD NOT be set.

**[11] `http.request.header.<key>`:** Instrumentations SHOULD require an explicit configuration of which headers are to be captured. Including all request headers can be a security risk - explicit configuration helps avoid leaking sensitive information.

The `User-Agent` header is already captured in the `user_agent.original` attribute. Users MAY explicitly configure instrumentations to capture them even though it is not recommended.

The attribute value MUST consist of either multiple header values as an array of strings or a single-item array containing a possibly comma-concatenated string, depending on the way the HTTP library provides access to headers.

Examples:
- A header `Content-Type: application/json` SHOULD be recorded as the `http.request.header.content-type` attribute with value `["application/json"]`.
- A header `X-Forwarded-For: 1.2.3.4, 1.2.3.5` SHOULD be recorded as the `http.request.header.x-forwarded-for` attribute with value `["1.2.3.4", "1.2.3.5"]` or `["1.2.3.4, 1.2.3.5"]` depending on the HTTP library.

**[12] `http.response.header.<key>`:** Instrumentations SHOULD require an explicit configuration of which headers are to be captured. Including all response headers can be a security risk - explicit configuration helps avoid leaking sensitive information.

Users MAY explicitly configure instrumentations to capture them even though it is not recommended.

The attribute value MUST consist of either multiple header values as an array of strings or a single-item array containing a possibly comma-concatenated string, depending on the way the HTTP library provides access to headers.

Examples:
- A header `Content-Type: application/json` header SHOULD be recorded as the `http.request.response.content-type` attribute with value `["application/json"]`.
- A header `My-custom-header: abc, def` header SHOULD be recorded as the `http.response.header.my-custom-header` attribute with value `["abc", "def"]` or `["abc, def"]` depending on the HTTP library.

**[13] `network.transport`:** Generally `tcp` for `HTTP/1.0`, `HTTP/1.1`, and `HTTP/2`. Generally `udp` for `HTTP/3`. Other obscure implementations are possible.

**[14] `url.template`:** The `url.template` MUST have low cardinality. It is not usually available on HTTP clients, but may be known by the application or specialized HTTP instrumentation.

**[15] `user_agent.synthetic.type`:** This attribute MAY be derived from the contents of the `user_agent.original` attribute. Components that populate the attribute are responsible for determining what they consider to be synthetic bot or test traffic. This attribute can either be set for self-identification purposes, or on telemetry detected to be generated as a result of a synthetic request. This attribute is useful for distinguishing between genuine client traffic and synthetic traffic generated by bots or tests.

The following attributes can be important for making sampling decisions and SHOULD be provided **at span creation time** (if provided at all):
- `http.request.method`
- `server.address`
- `server.port`
- `url.full`

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

`network.transport` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `pipe` | Named or anonymous pipe. | |
| `quic` | QUIC | |
| `tcp` | TCP | |
| `udp` | UDP | |
| `unix` | UNIX domain socket | |

`user_agent.synthetic.type` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `bot` | Bot source. | |
| `test` | Synthetic test source. | |

### HTTP client span duration

There are some minimal constraints that SHOULD be honored:
- HTTP client spans SHOULD start sometime before the first request byte is sent. This may or may not include connection time.
- HTTP client spans SHOULD end sometime after the HTTP response headers are fully read (or when they fail to be read). This may or may not include reading the response body.

If there is any possibility for application code to not fully read the HTTP response (and for the HTTP client library to then have to clean up the HTTP response asynchronously), the HTTP client span SHOULD NOT be ended in this cleanup phase, and instead SHOULD end at some point after the HTTP response headers are fully read (or fail to be read). This avoids the span being ended asynchronously later on at a time which is no longer directly associated with the application code which made the HTTP request.

Because of the potential for confusion around this, HTTP client library instrumentations SHOULD document their behavior around ending HTTP client spans.

### HTTP request retries and redirects

Retries and redirects cause more than one physical HTTP request to be sent. A request is resent when an HTTP client library sends more than one HTTP request to satisfy the same API call. This may happen due to following redirects, authorization challenges, 503 Server Unavailable, network issues, or any other.

Each time an HTTP request is resent, the `http.request.resend_count` attribute SHOULD be added to each repeated span and set to the ordinal number of the request resend attempt.

See the examples for more details about:
- retrying a server error,
- redirects,
- authorization.

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
