# Project Plan & Video Recording Script – 60-Minute Build Challenge

## 1. Challenge Overview & Objectives
* **Challenge:** AI Platform Engineer – Observability – 60-Minute Build Challenge
* **Goal:** Build, instrument, test, and demonstrate an observable AI-powered backend service using FastAPI, structured logging, Prometheus metrics, Grafana dashboards, and end-to-end request correlation IDs.

---

## 2. 60-Minute Execution Roadmap

```
00:00 - 10:00 | Phase 1: Core Service Scaffold & Request Correlation Middleware
10:00 - 25:00 | Phase 2: Observability Engine (Structured JSON Logs & Prometheus Metrics)
25:00 - 40:00 | Phase 3: AI Engine & Business Action Workflow (SRE Triage + Ticket Creation)
40:00 - 50:00 | Phase 4: Docker Compose Stack & Pre-Provisioned Grafana Dashboard
50:00 - 60:00 | Phase 5: Verification, Fault Injection Testing & Video Recording Prep
```

### Milestone Checklist
- [x] **Milestone 1:** Architecture & Design Specification (`DESIGN.md` & `project-plan.md`)
- [ ] **Milestone 2:** Application Code Base
  - [ ] Correlation ID Middleware (`contextvars`-driven `X-Request-ID`)
  - [ ] Structured JSON Logger with automatic context enrichment
  - [ ] Prometheus Custom Metrics Collector (`/metrics`)
  - [ ] AI Tool-Calling Engine (OpenRouter / OpenAI SDK + Pydantic Tool Schema Validation)
  - [ ] Business Action Tool Executor (`create_incident_ticket`)
  - [ ] FastAPI Endpoints (`POST /ask`, `GET /health`, `GET /metrics`)
- [ ] **Milestone 3:** Observability Stack Infrastructure
  - [ ] `docker-compose.yml` (FastAPI app + Prometheus + Grafana)
  - [ ] Automated Prometheus config (`prometheus.yml`) & Grafana Dashboard provisioning
- [ ] **Milestone 4:** Automated Verification & Demo Script
  - [ ] End-to-end test suite (`test_observability.py`) covering success & failure flows

---

## 3. Planned Project File Structure

```text
assessment/
├── DESIGN.md                          # System design, architecture & tradeoffs
├── project-plan.md                    # Roadmap, verification & video recording script
├── docker-compose.yml                 # One-click observability stack (App + Prom + Grafana)
├── pyproject.toml                     # Modern Python project configuration & dependencies
├── Dockerfile                         # Production container definition
├── observability/
│   ├── prometheus.yml                 # Prometheus scrape configurations
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/prom.yml   # Auto-register Prometheus datasource
│       │   └── dashboards/dash.yml    # Auto-load dashboard provider
│       └── dashboards/ai_service.json # Pre-built AI Platform Observability Dashboard
├── app/
│   ├── __init__.py
│   ├── main.py                        # FastAPI application & router mounting
│   ├── config.py                      # Application settings & environment configuration
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── correlation.py             # X-Request-ID contextvar middleware
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── logger.py                  # Structured JSON logging formatter
│   │   └── metrics.py                 # Prometheus custom metrics registry
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── ask.py                     # API Request/Response Pydantic models
│   │   └── tools.py                   # Pydantic schemas for AI Tool Calling (CreateTicketToolInput)
│   └── services/
│       ├── __init__.py
│       ├── ai_engine.py               # OpenRouter/OpenAI tool-calling agent loop + hybrid fallback
│       └── ticket_service.py          # Business action executor: create_incident_ticket tool
└── tests/
    └── test_api.py                    # Pytest verification suite
```

---

## 4. Test Inputs & Verification Guide

### Test Input 1: Successful Request (Golden Path)
```bash
curl -i -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-golden-req-001" \
  -d '{
    "question": "High memory utilization alerts on worker pod order-processor-8f4b after latest deployment.",
    "context": {"environment": "production"}
  }'
```
**Expected Outcome:**
* `HTTP/1.1 200 OK` with header `X-Request-ID: test-golden-req-001`.
* JSON Response containing `ticket_id` (e.g., `INC-104921`) and `status: "CREATED"`.
* Structured JSON log line emitted with `request_id: "test-golden-req-001"`.
* Prometheus counter `business_actions_total{action_type="CREATE_INCIDENT_TICKET",status="CREATED"}` incremented.

---

### Test Input 2: Failing Request (Fault Injection Debugging)
```bash
curl -i -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-Inject-Fault: llm_timeout" \
  -d '{
    "question": "Database connection pool exhausted on checkout-service."
  }'
```
**Expected Outcome:**
* `HTTP/1.1 500 Internal Server Error` with header `X-Request-ID` generated or echoed.
* Structured error log containing error code `LLM_TIMEOUT_EXCEPTION` and stacktrace.
* Prometheus counter `app_exceptions_total{exception_type="TimeoutError"}` incremented.

---

## 5. Complete Video Submission Recording Script (8–10 Minutes)

> **Pro-Tip for Recording:** Have 3 terminal splits open or tabs:
> 1. Terminal running `docker-compose up` showing structured JSON log output.
> 2. Browser tab open to Grafana Dashboard (`http://localhost:3000`).
> 3. Terminal ready to run `curl` test scripts.

---

### Segment 1: Live Demo (3–4 Minutes)
* **[00:00 - 00:30] Introduction & Setup:**
  * *"Hello! I am demonstrating my submission for the AI Platform Engineer Observability Build Challenge. The entire stack—FastAPI service, Prometheus, and Grafana—is running locally via a single `docker-compose up` command."*
* **[00:30 - 01:45] Successful Request Demonstration:**
  * Execute Test Input 1 (`POST /ask` with an SRE memory alert query).
  * Show the JSON response containing the AI root-cause assessment and the automatically created business action ticket (`INC-XXXXXX`).
  * Point out the returned `X-Request-ID` HTTP header.
* **[01:45 - 03:30] Live Observability Verification:**
  * Switch to Terminal 1: Show the clean structured JSON logs displaying the exact same `request_id` across request start, AI inference completion, and ticket creation.
  * Switch to Grafana Dashboard: Show the real-time request rate, AI processing latency histogram, token consumption gauge, and successful business action counter.

---

### Segment 2: What Was Built – Architecture & Engineering (2–3 Minutes)
* **[03:30 - 04:30] Architecture Overview:**
  * *"I built a Python FastAPI backend structured around clean observability separation. When a request hits `/ask`, custom correlation middleware injects a unique `X-Request-ID` into Python's async `contextvars`."*
* **[04:30 - 05:30] Instrumentation Deep-Dive:**
  * *"For logging, a custom JSON logging formatter pulls the `request_id` from context on every log emission. For metrics, I engineered dashboard-ready Prometheus custom metrics covering the RED and USE methodologies—tracking API latency histograms, AI inference time, token usage counters, and business action outcomes."*

---

### Segment 3: Debugging Insight & Problem Solving (1–2 Minutes)
* **[05:30 - 07:00] Live Error Injection & Debugging Walkthrough:**
  * Execute Test Input 2 (`X-Inject-Fault: llm_timeout`).
  * Show the HTTP 500 response and grab the returned `X-Request-ID`.
  * *"In production, intermittent AI upstream latency spikes are a common failure mode. Notice how our Grafana error rate panel spikes immediately. To debug, we take the `X-Request-ID` from the client response and filter our structured logs."*
  * Demonstrate finding the exact JSON log entry showing that the AI engine timed out after 2000ms without leaving any dangling tickets or resource leaks.

---

### Segment 4: Tradeoff Discussion (1–2 Minutes)
* **[07:00 - 08:30] Architectural Tradeoffs:**
  * *"Finally, I'd like to highlight a key engineering tradeoff made in this design: **Explicit Custom Prometheus Instrumentation vs. Auto-Instrumentation**."*
  * *"While auto-instrumentation tools require fewer lines of code, explicit Prometheus custom instrumentation gives us precise control over domain-specific business tags like incident severity and ticket status. For an AI platform service where business action visibility is as critical as HTTP status codes, explicit instrumentation provides superior operational clarity."*
* **[08:30 - 09:00] Conclusion:**
  * *"Thank you for watching this demonstration of the Observable AI Backend Service!"*
