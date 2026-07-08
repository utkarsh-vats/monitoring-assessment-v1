# Observable AI Backend Service

An observable, production-grade AI backend service built with **Python 3.11**, **FastAPI**, **Prometheus**, **Grafana**, and **Structured JSON Logging with End-to-End Request Correlation IDs (`X-Request-ID`)**. Designed for the **AI Platform Engineer – Observability – 60-Minute Build Challenge**.

---

## Key Engineering & Observability Features

1. **Mandatory Real Engineering Improvement:**
   - **Dashboard-Ready Custom Metrics & End-to-End Request Correlation (`X-Request-ID`)**: Every HTTP request is enriched with a correlation ID propagated across asynchronous tasks and JSON logs via Python `contextvars`.
   - Custom Prometheus metrics implement **RED (Rate, Errors, Duration)** and **USE (Utilization, Saturation, Errors)** methodologies.

2. **AI Workflow & Business Action:**
   - Implements an **SRE/DevOps Incident Analyzer** that processes natural language alerts and automatically triggers a business action (`create_incident_ticket`) when an issue requires mitigation.
   - Built using an OpenAI SDK + Pydantic Tool-Calling loop supporting **Google Gemini API (`GEMINI_API_KEY`)**, **OpenRouter (`OPENROUTER_API_KEY`)**, **OpenAI (`OPENAI_API_KEY`)**, and a **Smart Mock Engine** for deterministic offline testing.

3. **Pre-Configured One-Click Observability Stack:**
   - Includes a full `docker-compose.yml` with **FastAPI**, **Prometheus (v2.51)**, and **Grafana (v10.4)** pre-loaded with a customized AI Service Observability Dashboard.

---

## Quick Start (Locally or with Docker Compose)

### 1. Configure Environment Secrets (`.env.local`)
A pre-configured [`.env.local`](file:///f:/Obtuse/Projects/FluidAI/assessment/.env.local) file (with a matching [`.env.example`](file:///f:/Obtuse/Projects/FluidAI/assessment/.env.example) template) is provided for API keys and local configuration. Populate any required LLM API keys in `.env.local`:
```dotenv
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
FORCE_MOCK_MODE=false
```
> [!NOTE]
> `.env.local` is automatically loaded by both local Python runs (`app.config`) and Docker Compose (`env_file`). It is excluded from Git via `.gitignore`.

### 2. Run via Docker Compose (Recommended for Demo)
```bash
docker-compose up --build
```
- **FastAPI Service:** `http://localhost:8002`
- **Prometheus Metrics:** `http://localhost:8002/metrics`
- **Grafana Dashboard:** `http://localhost:3002` (User: `admin` / Password: `admin`)

### 3. Run Python Test Suite
```bash
# Using installed virtualenv
pytest -v
```

### 4. API Testing with Postman
A complete, pre-configured Postman collection is included in the `docs/` directory:
- **Postman Collection:** [`docs/FuildAI_Assessment.postman_collection.json`](file:///f:/Obtuse/Projects/FluidAI/assessment/docs/FuildAI_Assessment.postman_collection.json)

Import this collection directly into Postman to test all API endpoints (`/ask`, `/health`, `/metrics`) with pre-filled request headers (`X-Request-ID`, `X-Inject-Fault`) and structured payloads.

---

## Observability Dashboard Showcase

The pre-configured Grafana instance (`http://localhost:3002`) automatically provisions the **AI Service Observability Dashboard** visualizing RED/USE custom metrics, LLM latency histograms, token usage, and business actions:

![Grafana Observability Dashboard](docs/screenshots/Grafana-Dashboard.png)

---

## Test Inputs & Demo Guide

### Scenario A: Successful Request (Golden Path)
```bash
curl -i -X POST http://localhost:8002/ask \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: demo-req-golden-001" \
  -d '{
    "question": "High memory utilization alerts on worker pod order-processor-8f4b after latest deployment.",
    "context": {"environment": "production", "service": "order-processor"}
  }'
```
**Observability Verification:**
- Returns `HTTP 200 OK` with header `X-Request-ID: demo-req-golden-001`.
- Structured JSON logs display exact execution timing and `request_id`.
- Prometheus counter `business_actions_total{action_type="CREATE_INCIDENT_TICKET"}` increments.

![Ask Endpoint Success](docs/screenshots/ENDPOINT-'ask'-SUCCESS.png)

---

### Scenario B: Failing / Fault-Injected Request (Incident Debugging)
```bash
curl -i -X POST http://localhost:8002/ask \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: demo-req-fault-500" \
  -H "X-Inject-Fault: llm_timeout" \
  -d '{
    "question": "Database connection pool exhausted on checkout service."
  }'
```
**Observability Verification:**
- Returns `HTTP 500 Internal Server Error` with header `X-Request-ID: demo-req-fault-500`.
- Structured error log includes the stacktrace tagged with `request_id`.
- Prometheus counter `app_exceptions_total{exception_type="TimeoutError"}` increments.

![Ask Endpoint Failure](docs/screenshots/ENDPOINT-'ask'-FAILURE.png)

---

## Project Structure
```text
assessment/
├── DESIGN.md                          # Comprehensive architecture & tradeoff documentation
├── project-plan.md                    # Roadmap & complete 8-10 min video demo script
├── pyproject.toml                     # Modern project config & dependencies
├── docker-compose.yml                 # Local development stack with hot-reload
├── docker-compose.prod.yml            # Production deployment stack
├── Dockerfile                         # Production container build
├── docs/                              # API collections and visual evidence
│   ├── FuildAI_Assessment.postman_collection.json  # Complete Postman API collection
│   └── screenshots/                   # Demo screenshots & Grafana dashboard visualizations
├── app/
│   ├── main.py                        # FastAPI endpoints (/ask, /health, /metrics)
│   ├── config.py                      # Multi-provider settings & environment config
│   ├── middleware/correlation.py      # X-Request-ID contextvars correlation middleware
│   ├── observability/
│   │   ├── logger.py                  # Structured JSON logging formatter
│   │   └── metrics.py                 # Prometheus RED/USE custom metrics registry
│   ├── schemas/                       # Pydantic schemas for API & AI Tool calling
│   └── services/                      # AI Tool-Calling Engine & Incident Ticket Business Action
├── observability/
│   ├── prometheus.yml                 # Prometheus scrape configurations
│   └── grafana/                       # Auto-provisioned Grafana datasource & dashboard JSON
└── tests/
    └── test_api.py                    # Complete Pytest verification suite
```
