# Observability, Auditing, & Production Readiness

This document describes the operational components, logging architecture, health checks, and deployment guidelines for AegisOne.

---

## 1. Centralized Audit Log Flow

Every administrative modification or security execution maps to PostgreSQL-persisted audit trails:

```
    [SOC Operator]
          |
          | (starts threat scenario / resets engine / updates thresholds)
          v
    [FastAPI Endpoint]
          |
          | (calls audit_service.log_action)
          v
    [audit_service] ----> (persists to PostgreSQL "audit_logs" table)
          |
          +-------------> (publishes via SSE "AUDIT_LOG_CREATED" payload)
          |
          v
    [Operations Console] (renders record in table, trigger audio/toast alert)
```

---

## 2. API Metrics & Latency Tracking

A custom HTTP middleware (`log_request_metrics`) intercepts client calls:
- **Latencies**: Measures execution delta in seconds.
- **Aggregations**: Normalizes path parameter variables (e.g., replaces UUID identifiers with `{id}` templates) to yield clean endpoint stats.
- **Slow Requests**: Counts any connection taking >1.0 seconds.
- **Active SSE Connections**: Monitors client stream attachments.

---

## 3. Operational Endpoints

1. **`GET /health/details`**:
   Returns details of backend status, DB connection, AI models Manifest, task queues size, and host hardware resources (CPU, Memory, Disk usage).
2. **`GET /metrics`**:
   Exposes core counts (Total requests, slow requests, SSE listeners) for visualization engines or Prometheus scraper agents.
3. **`GET /config` & `PUT /config`**:
   Exposes system thresholds, alerting configurations, and simulation multipliers.
4. **`GET /audit/export` & `GET /alerts/export`**:
   Streams CSV or JSON file downloads for offline inspection.

---

## 4. Production Readiness Deployment Checklist

Ensure the following boundaries are configured before deploying to industrial subnets:
- [ ] **DB Connection Pooling**: Enforce SQLAlchemy limits to match high transaction volumes on historian servers.
- [ ] **No Internet Fallback Mode**: Verify that `FallbackProvider` is default when `OPENAI_API_KEY` is not present, avoiding connection drop errors inside sandboxed ICS loops.
- [ ] **Strict Port Bindings**: White-list Modbus/S7Comm TCP ports (502, 102) only on specific Engineering switch segments.
- [ ] **CORS Origins Whitelisting**: Set `BACKEND_CORS_ORIGINS` to specific operator station hosts.
