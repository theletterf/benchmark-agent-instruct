"""Frozen OpenTelemetry candidate substrate for Phase 2 calibration.

This adapter intentionally stops at task and calibration preparation.  The
nine manipulation artifacts are not generated until the two calibration stages
show that ordinary current documentation leaves decision-level headroom.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path

from ...worlds import ROOT

PROJECT = "opentelemetry"
VERSION = "OpenTelemetry documentation site snapshot 2026-08-17"
PROJECT_ROOT = ROOT / "phase-2-real-docs" / "projects" / PROJECT
SOURCES = PROJECT_ROOT / "sources"


@dataclass(frozen=True)
class DecisionSpec:
    id: str
    current: tuple[str, ...]
    historical: tuple[str, ...]
    requirement: str
    condition: str | None
    source_id: str


@dataclass(frozen=True)
class OtelTask:
    id: str
    title: str
    prompt: str
    source_ids: tuple[str, ...]
    official_excerpt: str
    decisions: tuple[DecisionSpec, ...]

    def as_dict(self):
        return asdict(self)


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data):
        value = " ".join(data.split())
        if value:
            self.parts.append(value)


def source_manifest():
    return json.loads((SOURCES / "manifest.json").read_text(encoding="utf-8"))


def source_text(source_id):
    source = next(item for item in source_manifest()["sources"] if item["id"] == source_id)
    parser = _TextExtractor()
    parser.feed((SOURCES / source["snapshot"]).read_text(encoding="utf-8"))
    return " ".join(parser.parts)


def validate_sources():
    errors = []
    manifest = source_manifest()
    if manifest.get("documentation_snapshot_version") != VERSION:
        errors.append("OpenTelemetry documentation snapshot version is not pinned")
    for item in manifest["sources"]:
        if not item.get("retrieval_date") or not item.get("title") or not item.get("url"):
            errors.append(f"source metadata incomplete: {item.get('id', '<unknown>')}")
        path = SOURCES / item["snapshot"]
        if not path.exists():
            errors.append(f"missing source snapshot: {item['snapshot']}")
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            errors.append(f"source hash mismatch: {item['snapshot']}")
    return errors


TASKS = (
    OtelTask(
        "http-client-span", "HTTP client span attributes",
        "You are instrumenting an outbound HTTP client request. Produce a compact YAML attribute mapping for a POST request to https://shop.example/orders that receives HTTP 201. Include the request method, response status, complete URL, and destination server address. Return only the mapping.",
        ("http-spans", "http-migration"),
        """# HTTP client spans

For an HTTP client span, `http.request.method`, `server.address`, and `url.full` are Required. `http.response.status_code` is Conditionally Required when the response status code was received. The HTTP migration maps `http.method` to `http.request.method`, `http.status_code` to `http.response.status_code`, `http.url` to `url.full`, and `net.peer.name` to `server.address`.""",
        (
            DecisionSpec("http-method-attribute", ("http.request.method",), ("http.method",), "Required", None, "http-migration"),
            DecisionSpec("http-status-attribute", ("http.response.status_code",), ("http.status_code",), "Conditionally Required", "when response status is received", "http-migration"),
            DecisionSpec("http-url-attribute", ("url.full",), ("http.url",), "Required", None, "http-migration"),
            DecisionSpec("http-server-address-attribute", ("server.address",), ("net.peer.name",), "Required", None, "http-migration"),
        ),
    ),
    OtelTask(
        "http-server-span", "HTTP server span attributes",
        "You are instrumenting a server that receives GET /orders/42 over HTTPS and replies with HTTP 200. Produce a compact YAML attribute mapping for the server span. Include the request method, response status, request path, scheme, and server address. Return only the mapping.",
        ("http-spans", "http-migration"),
        """# HTTP server spans

For an HTTP server span, `http.request.method`, `url.path`, and `url.scheme` are Required. `http.response.status_code` is Conditionally Required when a response status code was sent. The stable migration changes `http.method` to `http.request.method`, `http.status_code` to `http.response.status_code`, `http.target` to `url.path`, and `http.scheme` to `url.scheme`.""",
        (
            DecisionSpec("http-server-method", ("http.request.method",), ("http.method",), "Required", None, "http-migration"),
            DecisionSpec("http-server-status", ("http.response.status_code",), ("http.status_code",), "Conditionally Required", "when response status is sent", "http-migration"),
            DecisionSpec("http-server-path", ("url.path",), ("http.target",), "Required", None, "http-migration"),
            DecisionSpec("http-server-scheme", ("url.scheme",), ("http.scheme",), "Required", None, "http-migration"),
        ),
    ),
    OtelTask(
        "http-client-duration", "HTTP client duration metric",
        "Define the standard OpenTelemetry Histogram for duration of outbound HTTP client requests. State its metric name and unit in a compact YAML mapping. Return only the mapping.",
        ("http-metrics", "http-migration"),
        """# HTTP client request duration metric

The stable HTTP client request duration Histogram is named `http.client.request.duration` and uses unit `s`. The HTTP migration changes the historical metric name `http.client.duration` to `http.client.request.duration` and its unit from `ms` to `s`.""",
        (
            DecisionSpec("http-client-duration-metric", ("http.client.request.duration",), ("http.client.duration",), "Recommended", None, "http-migration"),
            DecisionSpec("http-client-duration-unit", ("unit: s", "unit: \"s\"", "unit: 's'"), ("unit: ms", "unit: \"ms\"", "unit: 'ms'"), "Required", None, "http-migration"),
        ),
    ),
    OtelTask(
        "database-client-span", "Database client span attributes",
        "You are instrumenting a PostgreSQL query against the orders collection in the shop namespace. Produce a compact YAML attribute mapping that identifies the database system, namespace, sanitized query text, operation name, and collection. Return only the mapping.",
        ("database-spans", "database-migration"),
        """# Database client spans

Current database spans use `db.system.name` (Required), `db.namespace` (Conditionally Required if available), `db.collection.name` (Conditionally Required), `db.query.text` (Opt-In and only when sanitization excludes sensitive information), and `db.operation.name` (Recommended). The migration maps `db.system`, `db.name`, `db.sql.table`, `db.statement`, and `db.operation` to those current names respectively.""",
        (
            DecisionSpec("db-system-name", ("db.system.name",), ("db.system",), "Required", None, "database-migration"),
            DecisionSpec("db-namespace", ("db.namespace",), ("db.name",), "Conditionally Required", "if available", "database-migration"),
            DecisionSpec("db-query-text", ("db.query.text",), ("db.statement",), "Opt-In", "only when sanitized", "database-migration"),
            DecisionSpec("db-operation-name", ("db.operation.name",), ("db.operation",), "Recommended", None, "database-migration"),
            DecisionSpec("db-collection-name", ("db.collection.name",), ("db.sql.table",), "Conditionally Required", None, "database-migration"),
        ),
    ),
    OtelTask(
        "java-agent-configuration", "Java agent OTLP and service configuration",
        "A service uses OpenTelemetry Java agent 2.x. Its exporter protocol is left unset. OTEL_SERVICE_NAME is checkout and OTEL_RESOURCE_ATTRIBUTES also contains service.name=cart. Produce a compact YAML configuration summary stating the exporter protocol and effective service.name. Return only the mapping.",
        ("java-agent-configuration", "sdk-environment-variables"),
        """# Java agent and SDK configuration

For Java agent 2.x, the default OTLP protocol is `http/protobuf`, not `grpc`. `OTEL_SERVICE_NAME` sets `service.name`; when `service.name` is also present in `OTEL_RESOURCE_ATTRIBUTES`, `OTEL_SERVICE_NAME` takes precedence. Therefore the effective service name in this scenario is `checkout`.""",
        (
            DecisionSpec("java-agent-otlp-protocol", ("http/protobuf",), ("grpc",), "Default", "when unset for Java agent 2.x", "java-agent-configuration"),
            DecisionSpec("service-name-precedence", ("service.name: checkout", "service.name: \"checkout\"", "service.name: 'checkout'", "effective service.name: checkout", "effective service.name is checkout", "effective_service_name: checkout", "effective_service_name: \"checkout\"", "effective_service_name: 'checkout'"), ("service.name: cart", "service.name: \"cart\"", "service.name: 'cart'", "effective service.name: cart", "effective service.name is cart", "effective_service_name: cart", "effective_service_name: \"cart\"", "effective_service_name: 'cart'"), "Precedence", None, "sdk-environment-variables"),
        ),
    ),
)


def tasks():
    return list(TASKS)


def task_ids():
    return [task.id for task in TASKS]


def get_task(task_id):
    return next(task for task in TASKS if task.id == task_id)


def candidates():
    return json.loads((PROJECT_ROOT / "candidates" / "candidates.json").read_text(encoding="utf-8"))


def scoring_manifest(task):
    return {
        "task": task.id,
        "title": task.title,
        "source_ids": list(task.source_ids),
        "decisions": [asdict(decision) for decision in task.decisions],
    }
