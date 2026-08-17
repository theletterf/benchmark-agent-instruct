# Documentation bundle — Database client query telemetry

Frozen authoritative OpenTelemetry documentation. Source sections are preserved in source order.

Sources:
- Semantic conventions for database client spans — https://opentelemetry.io/docs/specs/semconv/db/database-spans/ (Semantic conventions 1.44.0; references OpenTelemetry specification 1.59.0, retrieved 2026-08-17)
- Database semantic convention stability migration guide — https://opentelemetry.io/docs/specs/semconv/non-normative/db-migration/ (Stable database migration from semantic conventions 1.33.0, retrieved 2026-08-17)

---

<!-- source: database-spans#__intro__ -->
# Semantic conventions for database client spans

**Status**: Stable, Unless otherwise specified.
- Name
- Span definition
- Notes and well-known identifiers for `db.system.name`
- Database client span duration
- Sanitization of `db.query.text`
- Generating a summary of the query
- Context propagation
- SQL commenter
- Semantic conventions for specific database technologiesImportant

Existing database instrumentations that are using v1.24.0 of this document (or prior):
- SHOULD NOT change the version of the database conventions that they emit by default in their existing major version. Conventions include (but are not limited to) attributes, metric and span names, and unit of measure.
- SHOULD introduce an environment variable `OTEL_SEMCONV_STABILITY_OPT_IN` in their existing major version as a comma-separated list of category-specific values (e.g., http, databases, messaging). The list of values includes:
- `database` - emit the stable database conventions, and stop emitting the experimental database conventions that the instrumentation emitted previously.
- `database/dup` - emit both the experimental and stable database conventions, allowing for a phased rollout of the stable semantic conventions.
- The default behavior (in the absence of one of these values) is to continue emitting whatever version of the old experimental database conventions the instrumentation was emitting previously.
- Note: `database/dup` has higher precedence than `database` in case both values are present
- SHOULD maintain (security patching at a minimum) their existing major version for at least six months after it starts emitting both sets of conventions.
- MAY drop the environment variable in their next major version and emit only the stable database conventions.

---

<!-- source: database-spans#span-definition -->
## Span definition

**Status:**

This span describes database client call.

Instrumentations SHOULD, when possible, record database spans that represent the logical database operation as observed by the caller (such as client application).

When a database client provides higher-level convenience APIs for specific operations (e.g., calling a stored procedure), which internally generate and execute a generic query, it is RECOMMENDED to instrument the higher-level convenience APIs. These often allow setting `db.operation.*` attributes, which usually are not readily available at the generic query level.

**Span name** is covered in the Name section.

**Span duration** is covered in the Database client span duration section.

**Span kind** SHOULD be `CLIENT`. It MAY be set to `INTERNAL` on spans representing in-memory database calls. It’s RECOMMENDED to use `CLIENT` kind when database system being instrumented usually runs in a different process than its client or when database calls happen over instrumented protocol such as HTTP.

**Span status** SHOULD follow the Recording Errors document. Semantic conventions for individual systems SHOULD specify which values of `db.response.status_code` classify as errors.

**Attributes:**

| Key | Stability | Requirement Level | Value Type | Description | Example Values |
| --- | --- | --- | --- | --- | --- |
| `db.system.name` | | `Required` | string | The database management system (DBMS) product as identified by the client instrumentation. [1] | `other_sql`; `softwareag.adabas`; `actian.ingres` |
| `db.collection.name` | | `Conditionally Required` [2] | string | The name of a collection (table, container) within the database. [3] | `public.users`; `customers` |
| `db.namespace` | | `Conditionally Required` If available. | string | The name of the database, fully qualified within the server address and port. [4] | `customers`; `test.users` |
| `db.operation.name` | | `Conditionally Required` [5] | string | The name of the operation or command being executed. [6] | `findAndModify`; `HMSET`; `SELECT` |
| `db.response.status_code` | | `Conditionally Required` [7] | string | Database response status code. [8] | `102`; `ORA-17002`; `08P01`; `404` |
| `error.type` | | `Conditionally Required` If and only if the operation failed. | string | Describes a class of error the operation ended with. [9] | `timeout`; `java.net.UnknownHostException`; `server_certificate_invalid`; `500` |
| `server.port` | | `Conditionally Required` [10] | int | Server port number. [11] | `80`; `8080`; `443` |
| `db.operation.batch.size` | | `Recommended` | int | The number of database operations included in a batch operation. [12] | `2`; `3`; `4` |
| `db.query.summary` | | `Recommended` [13] | string | Low cardinality summary of a database query. [14] | `SELECT wuser_table`; `INSERT shipping_details SELECT orders`; `get user by id` |
| `db.query.text` | | `Recommended` [15] | string | The database query being executed. [16] | `SELECT * FROM wuser_table where username = ?`; `SET mykey ?` |
| `db.stored_procedure.name` | | `Recommended` [17] | string | The name of a stored procedure within the database. [18] | `GetCustomer` |
| `network.peer.address` | | `Recommended` If applicable for this database system. | string | Peer address of the database node where the operation was performed. [19] | `10.1.2.80`; `/tmp/my.sock` |
| `network.peer.port` | | `Recommended` if and only if `network.peer.address` is set. | int | Peer port number of the network connection. | `65123` |
| `server.address` | | `Recommended` | string | Name of the database host. [20] | `example.com`; `10.1.2.80`; `/tmp/my.sock` |
| `db.query.parameter.<key>` | | `Opt-In` | string | A database query parameter, with `<key>` being the parameter name, and the attribute value being a string representation of the parameter value. [21] | `someval`; `55` |
| `db.response.returned_rows` | | `Opt-In` | int | Number of rows returned by the operation. [22] | `10`; `30`; `1000` |

**[1] `db.system.name`:** The actual DBMS may differ from the one identified by the client. For example, when using PostgreSQL client libraries to connect to a CockroachDB, the `db.system.name` is set to `postgresql` based on the instrumentation’s best knowledge.

**[2] `db.collection.name`:** If readily available and if a database call is performed on a single collection.

**[3] `db.collection.name`:** It is RECOMMENDED to capture the value as provided by the application without attempting to do any case normalization.

The collection name SHOULD NOT be extracted from `db.query.text`, when the database system supports query text with multiple collections in non-batch operations.

For batch operations, if the individual operations are known to have the same collection name then that collection name SHOULD be used.

**[4] `db.namespace`:** If a database system has multiple namespace components, they SHOULD be concatenated from the most general to the most specific namespace component, using `|` as a separator between the components. Any missing components (and their associated separators) SHOULD be omitted. Semantic conventions for individual database systems SHOULD document what `db.namespace` means in the context of that system. It is RECOMMENDED to capture the value as provided by the application without attempting to do any case normalization.

**[5] `db.operation.name`:** If readily available and if there is a single operation name that describes the database call.

**[6] `db.operation.name`:** It is RECOMMENDED to capture the value as provided by the application without attempting to do any case normalization.

The operation name SHOULD NOT be extracted from `db.query.text`, when the database system supports query text with multiple operations in non-batch operations.

If spaces can occur in the operation name, multiple consecutive spaces SHOULD be normalized to a single space.

For batch operations, if the individual operations are known to have the same operation name then that operation name SHOULD be used prepended by `BATCH `, otherwise `db.operation.name` SHOULD be `BATCH` or some other database system specific term if more applicable.

**[7] `db.response.status_code`:** If the operation failed and status code is available.

**[8] `db.response.status_code`:** The status code returned by the database. Usually it represents an error code, but may also represent partial success, warning, or differentiate between various types of successful outcomes. Semantic conventions for individual database systems SHOULD document what `db.response.status_code` means in the context of that system.

**[9] `error.type`:** The `error.type` SHOULD match the `db.response.status_code` returned by the database or the client library, or the canonical name of exception that occurred. When using canonical exception type name, instrumentation SHOULD do the best effort to report the most relevant type. For example, if the original exception is wrapped into a generic one, the original exception SHOULD be preferred. Instrumentations SHOULD document how `error.type` is populated.

**[10] `server.port`:** If using a port other than the default port for this DBMS and if `server.address` is set.

**[11] `server.port`:** When observed from the client side, and when communicating through an intermediary, `server.port` SHOULD represent the server port behind any intermediaries, for example proxies, if it’s available.

**[12] `db.operation.batch.size`:** Except for empty batch requests described below, a batch operation contains two or more database operations explicitly submitted as separate operations in a single client call, protocol message, or database command.

Requests to batch APIs that contain only one operation SHOULD be modeled as single operations, not as batch operations.

A database call is not a batch operation solely because one operation accepts multiple operands, such as keys, rows, documents, points, or other data elements, including Redis `MGET` with multiple keys.

In batch APIs that execute the same parameterized operation with parameter sets, each parameter set represents one database operation for determining whether the request is a batch operation. Requests with only one parameter set SHOULD be modeled as single operations, not as batch operations.

`db.operation.batch.size` SHOULD be set to the number of operations in the batch. It SHOULD NOT be set for non-batch operations.

A request to execute a batch operation with no operations SHOULD also be treated as a batch operation, and `db.operation.batch.size` SHOULD be set to `0`.

**[13] `db.query.summary`:** if available through instrumentation hooks or if the instrumentation supports generating a query summary.

**[14] `db.query.summary`:** The query summary describes a class of database queries and is useful as a grouping key, especially when analyzing telemetry for database calls involving complex queries.

Summary may be available to the instrumentation through instrumentation hooks or other means. If it is not available, instrumentations that support query parsing SHOULD generate a summary following Generating query summary section.

For batch operations, if the individual operations are known to have the same query summary then that query summary SHOULD be used prepended by `BATCH `, otherwise `db.query.summary` SHOULD be `BATCH` or some other database system specific term if more applicable.

**[15] `db.query.text`:** Non-parameterized query text SHOULD NOT be collected by default unless there is sanitization that excludes sensitive data, e.g. by redacting all literal values present in the query text. See Sanitization of `db.query.text`. Parameterized query text SHOULD be collected by default (the query parameter values themselves are opt-in, see `db.query.parameter.<key>`).

**[16] `db.query.text`:** For sanitization see Sanitization of `db.query.text`. For batch operations, if the individual operations are known to have the same query text then that query text SHOULD be used, otherwise all of the individual query texts SHOULD be concatenated with separator `; `or some other database system specific separator if more applicable. Parameterized query text SHOULD NOT be sanitized. Even though parameterized query text can potentially have sensitive data, by using a parameterized query the user is giving a strong signal that any sensitive data will be passed as parameter values, and the benefit to observability of capturing the static part of the query text by default outweighs the risk.

**[17] `db.stored_procedure.name`:** If operation applies to a specific stored procedure.

**[18] `db.stored_procedure.name`:** It is RECOMMENDED to capture the value as provided by the application without attempting to do any case normalization.

For batch operations, if the individual operations are known to have the same stored procedure name then that stored procedure name SHOULD be used.

**[19] `network.peer.address`:** Semantic conventions for individual database systems SHOULD document whether `network.peer.*` attributes are applicable. Network peer address and port are useful when the application interacts with individual database nodes directly. If a database operation involved multiple network calls (for example retries), the address of the last contacted node SHOULD be used.

**[20] `server.address`:** When observed from the client side, and when communicating through an intermediary, `server.address` SHOULD represent the server address behind any intermediaries, for example proxies, if it’s available.

**[21] `db.query.parameter.<key>`:** If a query parameter has no name and instead is referenced only by index, then `<key>` SHOULD be the 0-based index.

`db.query.parameter.<key>` SHOULD match up with the parameterized placeholders present in `db.query.text`.

It is RECOMMENDED to capture the value as provided by the application without attempting to do any case normalization or sanitization.

Instrumentations SHOULD NOT capture `db.query.parameter.<key>` by default since values may contain PII or sensitive details. Application operators are expected to enable specific keys depending on their privacy and security considerations.

`db.query.parameter.<key>` SHOULD NOT be captured on batch operations.

Examples:
-

For a query `SELECT * FROM users where username = %s` with the parameter `"jdoe"`, the attribute `db.query.parameter.0` SHOULD be set to `"jdoe"`.
-

For a query `"SELECT * FROM users WHERE username = %(userName)s;` with parameter `userName = "jdoe"`, the attribute `db.query.parameter.userName` SHOULD be set to `"jdoe"`.

**[22] `db.response.returned_rows`:** The number of rows returned by the database operation as observed by the instrumentation at the time the span ends.

The following attributes can be important for making sampling decisions and SHOULD be provided **at span creation time** (if provided at all):
- `db.collection.name`
- `db.namespace`
- `db.operation.name`
- `db.query.summary`
- `db.query.text`
- `db.system.name`
- `server.address`
- `server.port`

`db.system.name` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `actian.ingres` | Actian Ingres | |
| `aws.dynamodb` | Amazon DynamoDB | |
| `aws.redshift` | Amazon Redshift | |
| `azure.cosmosdb` | Azure Cosmos DB | |
| `cassandra` | Apache Cassandra | |
| `clickhouse` | ClickHouse | |
| `cockroachdb` | CockroachDB | |
| `couchbase` | Couchbase | |
| `couchdb` | Apache CouchDB | |
| `derby` | Apache Derby | |
| `elasticsearch` | Elasticsearch | |
| `firebirdsql` | Firebird | |
| `gcp.spanner` | Google Cloud Spanner | |
| `geode` | Apache Geode | |
| `h2database` | H2 Database | |
| `hbase` | Apache HBase | |
| `hive` | Apache Hive | |
| `hsqldb` | HyperSQL Database | |
| `ibm.db2` | IBM Db2 | |
| `ibm.informix` | IBM Informix | |
| `ibm.netezza` | IBM Netezza | |
| `influxdb` | InfluxDB | |
| `instantdb` | Instant | |
| `intersystems.cache` | InterSystems Caché | |
| `mariadb` | MariaDB | |
| `memcached` | Memcached | |
| `microsoft.sql_server` | Microsoft SQL Server | |
| `mongodb` | MongoDB | |
| `mysql` | MySQL | |
| `neo4j` | Neo4j | |
| `opensearch` | OpenSearch | |
| `oracle.db` | Oracle Database | |
| `other_sql` | Some other SQL database. Fallback only. | |
| `postgresql` | PostgreSQL | |
| `redis` | Redis | |
| `sap.hana` | SAP HANA | |
| `sap.maxdb` | SAP MaxDB | |
| `softwareag.adabas` | Adabas (Adaptable Database System) | |
| `sqlite` | SQLite | |
| `teradata` | Teradata | |
| `trino` | Trino | |

`error.type` has the following list of well-known values. If one of them applies, then the respective value MUST be used; otherwise, a custom value MAY be used.

| Value | Description | Stability |
| --- | --- | --- |
| `_OTHER` | A fallback error value to be used when the instrumentation doesn’t define a custom value. | |

### Notes and well-known identifiers for `db.system.name`

The list above is a non-exhaustive list of well-known identifiers to be specified for `db.system.name`.

If a value defined in this list applies to the DBMS to which the request is sent, this value MUST be used. If no value defined in this list is suitable, a custom value MUST be provided. This custom value MUST be the name of the DBMS in lowercase and without a version number to stay consistent with existing identifiers.

It is encouraged to open a PR towards this specification to add missing values to the list, especially when instrumentations for those missing databases are written. This allows multiple instrumentations for the same database to be aligned and eases analyzing for backends.

The value `other_sql` is intended as a fallback and MUST only be used if the DBMS is known to be SQL-compliant but the concrete product is not known to the instrumentation. If the concrete DBMS is known to the instrumentation, its specific identifier MUST be used.

Backends could, for example, use the provided identifier to determine the appropriate SQL dialect for parsing the `db.query.text`.

When additional attributes are added that only apply to a specific DBMS, its identifier SHOULD be used as a namespace in the attribute key as for the attributes in the sections below.

---

<!-- source: database-spans#database-client-span-duration -->
## Database client span duration

Database client spans SHOULD, when possible, cover the duration of the corresponding API call as observed by the caller (such as the client application). For example, if a transient issue happened and was retried within this database call, the corresponding span should cover the duration of the logical operation with all retries.

If there is any possibility for application code to not fully consume the database response (and for the database client library to then have to clean up the database response asynchronously), the database client span SHOULD NOT be ended in this cleanup phase, and instead SHOULD end at some point after the initial call returns to the caller. This avoids the span being ended asynchronously later on at a time which is no longer directly associated with the application code which made the database request.

---

<!-- source: database-spans#sanitization-of-dbquerytext -->
## Sanitization of `db.query.text`

The `db.query.text` SHOULD be collected by default only if there is sanitization that excludes sensitive information. Sanitization SHOULD replace all literals with a placeholder value. Such literals include, but are not limited to, String, Numeric, Date and Time, Boolean, Interval, Binary, and Hexadecimal literals. The placeholder value SHOULD be `?`, unless it already has a defined meaning in the given database system, in which case the instrumentation MAY choose a different placeholder.

Parameterized query text SHOULD NOT be sanitized. Even though parameterized query text can potentially have sensitive data, by using a parameterized query the user is giving a strong signal that any sensitive data will be passed as parameter values, and the benefit to observability of capturing the static part of the query text by default outweighs the risk.

IN-clauses MAY be collapsed during sanitization, e.g. from `IN (?, ?, ?, ?)` to `IN (?)`, as this can help with extremely long IN-clauses, and can help control cardinality for users who choose to (optionally) add `db.query.text` to their metric attributes.

When performing sanitization, instrumentation MAY truncate the sanitized value for performance considerations (since sanitizing has a performance cost).

---

<!-- source: database-spans#generating-a-summary-of-the-query -->
## Generating a summary of the query

The `db.query.summary` attribute can be used to capture a shortened representation of the query. It SHOULD have low-cardinality and SHOULD NOT contain any dynamic or sensitive data.Note

The `db.query.text` attribute is intended to identify individual queries. Even though it is sanitized if captured by default, it could still have high cardinality and might reach hundreds of lines.

The `db.query.summary` is intended to provide a less granular grouping key that can be used as a span name or a metric attribute in common cases. It SHOULD only contain information that has a significant impact on the query, database, or application performance.

Instrumentation SHOULD set the query summary if it is readily available through instrumentation hooks or other sources.

Otherwise:
-

When instrumenting higher-level APIs that build queries internally - for example, those that create a table or execute a stored procedure - instrumentations SHOULD generate a `db.query.summary` from available operation(s) and target(s) using the format described in this section.
-

When instrumenting APIs that operate at the query level, instrumentations that support query parsing SHOULD generate a query summary based on the `db.query.text`.

The summary SHOULD preserve the following parts of query in the order they were provided:
- operations such as SQL SELECT, INSERT, UPDATE, DELETE, and other commands
- operation targets such as collections, stored procedures, database names, etc

Instrumentations that support query parsing SHOULD parse the query and extract a list of operations and targets from the query. It SHOULD set `db.query.summary` attribute to the value formatted in the following way:

```text
{operation1} {target1} {operation2} {target2} {target3} ...

```

Instrumentations SHOULD capture the values of operations and targets as provided by the application without attempting to do any case normalization. If the operation and target value is populated on `db.operation.name`, `db.collection.name`, or other attributes, it SHOULD match the value used in the `db.query.summary`.

Instrumentations that parse the query to set `db.query.summary` SHOULD truncate the summary to 255 characters (ensuring truncation does not occur within an operation name or target).

**Examples**:
-

Query that consist of a single operation:

```text
SELECT *
FROM wuser_table
WHERE username = ?

```

the corresponding `db.query.summary` is `SELECT wuser_table`.
-

Query that performs multiple operations:

```text
INSERT INTO shipping_details
 (order_id,
 address)
SELECT order_id,
 address
FROM orders
WHERE order_id = ?

```

the corresponding `db.query.summary` is `INSERT shipping_details SELECT orders`.
-

Query that performs an operation that’s applied to multiple collections:

```text
SELECT *
FROM songs,
 artists
WHERE songs.artist_id == artists.id

```

the corresponding `db.query.summary` is `SELECT songs artists`.
-

Query that performs an operation on an anonymous table:

```text
SELECT order_date
FROM (SELECT *
 FROM orders o
 JOIN customers c
 ON o.customer_id = c.customer_id)

```

the corresponding `db.query.summary` is `SELECT SELECT orders customers`.
-

Query that performs an operation on multiple collections with double-quotes or other punctuation:

```text
SELECT *
FROM "song list",
 'artists'

```

the corresponding `db.query.summary` is `SELECT "song list" 'artists'`.
-

Stored procedure is executed using a convenience API such as one available in JDBC:

```text
connection.prepareCall("{call some_stored_procedure}");

```

the corresponding `db.query.summary` is `call some_stored_procedure`, `db.query.text` is not populated. Note that `CALL` is the SQL standard keyword to invoke a stored procedure.
-

Stored procedure is executed using Microsoft SQL Server driver’s convenience API Microsoft.Data.SqlClient:

```text
var command = new SqlCommand();
command.CommandType = CommandType.StoredProcedure;
command.CommandText = "some_stored_procedure";

```

the corresponding `db.query.summary` is `EXECUTE some_stored_procedure`, `db.query.text` is not populated. Note that Microsoft SQL Server does not support the SQL Standard `CALL` keyword, but uses instead `EXECUTE` to invoke a stored procedure.

Semantic conventions for individual database systems or specialized instrumentations MAY specify a different `db.query.summary` format as long as produced summary remains relatively short and its cardinality remains low comparing to the `db.query.text`.

---

<!-- source: database-migration#__intro__ -->
# Database semantic convention stability migration guide

Due to the significant number of modifications and the extensive user base affected by them, existing database instrumentations published by OpenTelemetry are required to implement a migration plan that will assist users in transitioning to the stable database semantic conventions.

Specifically, when existing database instrumentations published by OpenTelemetry are updated to the stable database semantic conventions, they:
- SHOULD NOT change the version of the database conventions that they emit by default in their existing major version. Conventions include (but are not limited to) attributes, metric and span names, and unit of measure.
- SHOULD introduce an environment variable `OTEL_SEMCONV_STABILITY_OPT_IN` in their existing major version, which accepts:
- `database` - emit the stable database conventions, and stop emitting the old database conventions that the instrumentation emitted previously.
- `database/dup` - emit both the old and the stable database conventions, allowing for a phased rollout of the stable semantic conventions.
- The default behavior (in the absence of one of these values) is to continue emitting whatever version of the old database conventions the instrumentation was emitting previously.
- Need to maintain (security patching at a minimum) their existing major version for at least six months after it starts emitting both sets of conventions.
- May drop the environment variable in their next major version and emit only the stable database conventions.Note

`OTEL_SEMCONV_STABILITY_OPT_IN` is only intended to be used when migrating from an experimental semantic convention to its initial stable version.

---

<!-- source: database-migration#summary-of-changes -->
## Summary of changes

This section summarizes the changes made to the HTTP semantic conventions from v1.24.0. to v1.33.0.

### Database client span attributes

| Change | Comments |
| --- | --- |
| `db.connection_string` | Removed |
| `db.user` | Removed |
| `network.transport` | Removed |
| `network.type` | Removed |
| `db.name` | Removed, integrated into the new `db.namespace`. Clarified, it is RECOMMENDED to capture the value as provided by the application without attempting to do any case normalization |
| `db.redis.database_index` | Removed, integrated into the new `db.namespace` |
| `db.mssql.instance_name` | Removed, integrated into the new `db.namespace` |
| `db.instance.id` | Removed, replaced by `server.address` or integrated into `db.namespace` as appropriate |
| `db.system` → `db.system.name` | |
| `db.statement` → `db.query.text` | Clarified, SHOULD be collected by default only if there is sanitization that excludes sensitive information |
| `db.operation` → `db.operation.name` | Clarified, it is RECOMMENDED to capture the value as provided by the application without attempting to do any case normalization |
| `db.sql.table` → `db.collection.name` | Should not be captured if extracting the value from `db.query.text` since there could be multiple. Clarified, it is RECOMMENDED to capture the value as provided by the application without attempting to do any case normalization |
| `db.cassandra.table` → `db.collection.name` | Clarified, it is RECOMMENDED to capture the value as provided by the application without attempting to do any case normalization |
| `db.mongodb.collection` → `db.collection.name` | Clarified, it is RECOMMENDED to capture the value as provided by the application without attempting to do any case normalization |
| `db.cosmosdb.container` → `db.collection.name` | Clarified, it is RECOMMENDED to capture the value as provided by the application without attempting to do any case normalization |
| New: `db.query.summary` | |
| New: `db.operation.batch.size` | |
| New: `db.response.status_code` | |
| New: `db.stored_procedure.name` | |
| New: `error.type` | |
| New: `db.operation.parameter.<key>` | *Not marked stable yet* |
| New: `db.query.parameter.<key>` | *Not marked stable yet* |
| New: `db.response.returned_rows` | *Not marked stable yet* |

References:
- Database client span attributes v1.24.0
- Database client span attributes v1.33.0

### Database client span names

The recommended span name has changed. See Database client span names v1.33.0 for details on the new span name recommendation.

References:
- Database client span names v1.24.0
- Database client span names v1.33.0

### Database system name

The attribute `db.system` has been renamed to `db.system.name`. Along with the rename, many enum values were updated — most notably to follow a `<vendor>.<product>` naming pattern that makes vendor affiliation explicit.

The table below lists only the `db.system` values that were renamed or removed in `db.system.name`, along with the stability of the new value. Unchanged values are not listed.Note

The `db.system.name` attribute itself is `stable`. Individual enum members have their own stability level as shown below (`stable` or `development`).

| Description | Old `db.system` value | New `db.system.name` value |
| --- | --- | --- |
| Adabas (Adaptable Database System) | `adabas` | `softwareag.adabas` |
| InterSystems Caché (old alias) | `cache` | Removed |
| InterSystems Caché | `intersystems_cache` | `intersystems.cache` |
| Cloudscape | `cloudscape` | Removed |
| ColdFusion | `coldfusion` | Removed |
| Azure Cosmos DB | `cosmosdb` | `azure.cosmosdb` |
| IBM Db2 | `db2` | `ibm.db2` |
| Amazon DynamoDB | `dynamodb` | `aws.dynamodb` |
| EnterpriseDB | `edb` | Removed |
| FileMaker | `filemaker` | Removed |
| Firebird | `firebird` | `firebirdsql` |
| FirstSQL | `firstsql` | Removed |
| H2 Database | `h2` | `h2database` |
| SAP HANA | `hanadb` | `sap.hana` |
| IBM Informix | `informix` | `ibm.informix` |
| Actian Ingres | `ingres` | `actian.ingres` |
| InterBase | `interbase` | Removed |
| SAP MaxDB | `maxdb` | `sap.maxdb` |
| Microsoft SQL Server | `mssql` | `microsoft.sql_server` |
| Microsoft SQL Server Compact | `mssqlcompact` | Removed |
| IBM Netezza | `netezza` | `ibm.netezza` |
| Oracle Database | `oracle` | `oracle.db` |
| Pervasive PSQL | `pervasive` | Removed |
| PointBase | `pointbase` | Removed |
| Progress Database | `progress` | Removed |
| Amazon Redshift | `redshift` | `aws.redshift` |
| Google Cloud Spanner | `spanner` | `gcp.spanner` |
| Sybase | `sybase` | Removed |
| Vertica | `vertica` | Removed |

References:
- `db.system` enum values v1.24.0
- `db.system.name` enum values v1.33.0

### Database client operation duration metric

This is a required metric. There was no similar metric previously.

See Metric `db.client.operation.duration` v1.33.0.

### Experimental connection metrics

Database connection metrics are not stable yet, but there have been several changes in the latest release.

#### Database client connection count

Metric changes:
- **Name**: `db.client.connections.usage` → `db.client.connection.count`
- **Attributes**: see table below

| Attribute change | Comments |
| --- | --- |
| `pool.name` → `db.client.connection.pool.name` | |
| `state` → `db.client.connection.state` | |

References:
- Metric `db.client.connections.usage` v1.24.0
- Metric `db.client.connection.count` v1.33.0

#### Database client connection idle max

Metric changes:
- **Name**: `db.client.connections.idle.max` → `db.client.connection.idle.max`
- **Attributes**: see table below

| Attribute change | Comments |
| --- | --- |
| `pool.name` → `db.client.connection.pool.name` | |

References:
- Metric `db.client.connections.idle.max` v1.24.0
- Metric `db.client.connection.idle.max` v1.33.0

#### Database client connection idle min

Metric changes:
- **Name**: `db.client.connections.idle.min` → `db.client.connection.idle.min`
- **Attributes**: see table below

| Attribute change | Comments |
| --- | --- |
| `pool.name` → `db.client.connection.pool.name` | |

References:
- Metric `db.client.connections.idle.min` v1.24.0
- Metric `db.client.connection.idle.min` v1.33.0

#### Database client connection max

Metric changes:
- **Name**: `db.client.connections.max` → `db.client.connection.max`
- **Attributes**: see table below

| Attribute change | Comments |
| --- | --- |
| `pool.name` → `db.client.connection.pool.name` | |

References:
- Metric `db.client.connections.max` v1.24.0
- Metric `db.client.connection.max` v1.33.0

#### Database client connection pending requests

Metric changes:
- **Name**: `db.client.connections.pending_requests` → `db.client.connection.pending_requests`
- **Attributes**: see table below

| Attribute change | Comments |
| --- | --- |
| `pool.name` → `db.client.connection.pool.name` | |

References:
- Metric `db.client.connections.pending_requests` v1.24.0
- Metric `db.client.connection.pending_requests` v1.33.0

#### Database client connection timeouts

Metric changes:
- **Name**: `db.client.connections.timeouts` → `db.client.connection.timeouts`
- **Attributes**: see table below

| Attribute change | Comments |
| --- | --- |
| `pool.name` → `db.client.connection.pool.name` | |

References:
- Metric `db.client.connections.timeouts` v1.24.0
- Metric `db.client.connection.timeouts` v1.33.0

#### Database client connection create time

Metric changes:
- **Name**: `db.client.connections.create_time` → `db.client.connection.create_time`
- **Unit**: `ms` → `s`
- **Attributes**: see table below

| Attribute change | Comments |
| --- | --- |
| `pool.name` → `db.client.connection.pool.name` | |

References:
- Metric `db.client.connections.create_time` v1.24.0
- Metric `db.client.connection.create_time` v1.33.0

#### Database client connection wait time

Metric changes:
- **Name**: `db.client.connections.wait_time` → `db.client.connection.wait_time`
- **Unit**: `ms` → `s`
- **Attributes**: see table below

| Attribute change | Comments |
| --- | --- |
| `pool.name` → `db.client.connection.pool.name` | |

References:
- Metric `db.client.connections.wait_time` v1.24.0
- Metric `db.client.connection.wait_time` v1.33.0

#### Database client connection use time

Metric changes:
- **Name**: `db.client.connections.use_time` → `db.client.connection.use_time`
- **Unit**: `ms` → `s`
- **Attributes**: see table below

| Attribute change | Comments |
| --- | --- |
| `pool.name` → `db.client.connection.pool.name` | |

References:
- Metric `db.client.connections.use_time` v1.24.0
- Metric `db.client.connection.use_time` v1.33.0.feedback--answer{display:inline-block}.feedback--answer-no{margin-left:1em}.feedback--response{display:none;margin-top:1em}.feedback--response__visible{display:block}
