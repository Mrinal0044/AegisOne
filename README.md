<div align="center">

# 🛡️ AegisOne

### Industrial Behavioral Intelligence Platform

**Real-time behavioral security for OT, IIoT, SCADA & Critical Infrastructure**

*Aegis = protection/shield (Greek mythology) · One = unified platform*

[![Live Demo](https://img.shields.io/badge/Live%20Demo-View%20App-4f46e5?style=for-the-badge&logo=vercel&logoColor=white)](https://aegis-one-zeta.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?style=flat-square&logo=fastapi&logoColor=white)](#)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=flat-square&logo=postgresql&logoColor=white)](#)
[![License](https://img.shields.io/badge/status-production--ready-brightgreen?style=flat-square)](#)

**[🚀 Live Demo](https://aegis-one-zeta.vercel.app/) · [API Docs](#4-api-reference) · [Quick Start](#5-installation--local-development)**

</div>

---

## 📖 Overview

AegisOne is an enterprise-grade **Industrial Behavioral Intelligence Platform** designed to secure Operational Technology (OT), Industrial IoT (IIoT), SCADA systems, PLCs, industrial control systems, manufacturing plants, and critical infrastructure.

Unlike traditional signature-based cybersecurity systems, AegisOne continuously models the behavioral patterns of users, industrial devices, applications, and connected assets to detect **insider threats, compromised accounts, unauthorized access, abnormal industrial operations, and cyberattacks** in real time.

> 🔗 **Try it live:** [aegis-one-zeta.vercel.app](https://aegis-one-zeta.vercel.app/)

---

## 📑 Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Folder Structure](#2-folder-structure)
3. [Database Design](#3-database-design)
4. [API Reference](#4-api-reference)
5. [Installation & Local Development](#5-installation--local-development)
6. [Production Deployment](#6-production-deployment--readiness)
7. [Technology Stack](#7-technology-stack)
8. [Implementation Methodology](#8-implementation-methodology--process)
9. [SOC Dashboard Guide](#9-frontend-soc-dashboard-operator-guide)
10. [Live Demo Checklist](#10-live-demonstration-checklist)

---

## 1. Architecture Overview

AegisOne follows **Clean Architecture** principles to separate concerns, enforce maintainability, and allow future modules (such as Machine Learning anomaly detection and threat classifiers) to plug in without modifying core components.

```mermaid
flowchart TD
    Client["🖥️ Client — React SPA<br/>(Port 5173 / 80)"]
    Gateway["🚪 FastAPI Gateway Controller<br/>(Port 8000)"]
    Service["⚙️ Service Layer"]
    Sim["🔁 Simulation Engine<br/>(Background Loop)"]
    Repo["📦 Repository CRUD"]
    ORM["🗂️ SQLAlchemy ORM<br/>(Base Model)"]
    DB["🐘 PostgreSQL Database<br/>(Port 5442)"]

    Client -- "REST HTTPS (JSON)" --> Gateway
    Gateway --> Service
    Service <--> Sim
    Service --> Repo
    Repo --> ORM
    ORM --> DB
```

| Layer | Responsibility |
|---|---|
| **API Layer** | FastAPI routes receive payloads, execute validation (via Pydantic), and return responses. No business logic lives here. |
| **Service Layer** | Handles orchestrations, checks permissions, constructs domain models, and manages background tasks — including the **Simulation Engine**. |
| **Repository Layer** | Encapsulates raw database queries (via SQLAlchemy 2.0 select/insert) to abstract data access away from business services. |
| **Model Layer** | Defines mapping contracts to the database via SQLAlchemy declarative base mapping. |

---

## 2. Folder Structure

```
aegisone/
├── docker-compose.yml           # Multi-container orchestration (App + DB)
├── .env.example                 # Template for configuration parameters
├── database/
│   └── migrations/              # Alembic migration scripts and history
│       ├── env.py                # Configuration mapping models to DB
│       ├── script.py.mako        # Migration generation template
│       └── versions/             # Auto-generated database migration scripts
├── docker/
│   ├── backend.Dockerfile       # Python container definition
│   ├── frontend.Dockerfile      # Multi-stage Node + Nginx container definition
│   └── nginx.conf               # Nginx server configuration for React routing
├── backend/
│   ├── requirements.txt         # Backend Python dependencies
│   ├── alembic.ini              # Alembic config mapping to migrations directory
│   └── app/
│       ├── main.py               # FastAPI entry point & exception middleware
│       ├── api/v1/
│       │   ├── api.py             # Main API routes aggregator
│       │   └── endpoints/         # Individual controllers (health, assets, simulation, etc.)
│       ├── core/config.py        # Centralized app configuration (Pydantic Settings)
│       ├── database/session.py   # SQLAlchemy engine & session pool setup
│       ├── models/                # SQLAlchemy model definitions (ORM)
│       ├── schemas/               # Pydantic schemas (serialization & validation)
│       ├── repositories/          # Repository pattern classes (SQL CRUD)
│       ├── services/              # Business services (simulation engine, seeding)
│       └── middleware/            # Request logging & RFC-7807 error formatting
└── frontend/
    ├── package.json             # React node packages definition
    ├── vite.config.ts           # Vite bundler options with Tailwind CSS v4 compiler
    └── src/
        ├── api/                   # Axios clients and HTTP interfaces
        ├── context/               # Global health & polling monitors
        ├── types/                 # TypeScript interface configurations
        ├── components/            # Reusable UI cards, headers, sidebars
        └── pages/                 # Main sub-views (Dashboard, Assets, Alerts, etc.)
```

---

## 3. Database Design

AegisOne utilizes a normalized PostgreSQL database designed for future industrial security analytics:

| Entity | Description |
|---|---|
| **Departments** | Mapped organizational branches (Production, QA, Maintenance, IT, HR, etc.) |
| **Users** | Employees, roles, working hour boundaries, shift bindings (Morning/Afternoon/Night), and managers |
| **Devices** | Network hosts (Engineering Workstations, Office PCs, PLCs, Badge Readers) mapped by IP, MAC, zone (DMZ, OT-Control, OT-Field), status (Authorized/Quarantined), and assigned user |
| **Industrial Assets** | Factory hardware (Boiler, Robotic Arm, Conveyor) maintaining real-time `operational_state` parameters (temperature, pressure, rpm) |
| **Behavior Profiles** | Baseline signatures representing normal login schedules, typical apps, normal devices used, and network frequencies |
| **Events** | Serialized protocol stream logs (Modbus, S7comm, OPC-UA) containing timestamp, source/destination IPs, operational payloads, and severity |
| **Alerts** | Security anomaly records cataloged by severity, status, and affected assets |
| **Risk Scores** | Dynamic vulnerability indexes (0–100) calculated based on alert events |

---

## 4. API Reference

All endpoints are exposed under `/api/v1`.

### Health Check
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Returns connection state to the database and overall API health |

### Simulation Controls
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/simulation/status` | Fetches status (IDLE, RUNNING, PAUSED, STOPPED), active twin asset counts, and virtual time clock |
| `POST` | `/simulation/start` | Spins up the background simulator thread |
| `POST` | `/simulation/pause` | Pauses the simulation, freezing virtual clock progression |
| `POST` | `/simulation/resume` | Resumes execution from paused state |
| `POST` | `/simulation/stop` | Stops execution, resetting elapsed timers |
| `POST` | `/simulation/reset` | Truncates telemetry history tables (Events, Alerts, AuditLogs, RiskScores) for clean testing |
| `POST` | `/simulation/config` | Updates speed multiplier, event generation rate, and target counts |

### Telemetry Queries
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/industrial-assets` | List OT assets and live sensor telemetry |
| `GET` | `/devices` | List network host terminals and security statuses |
| `GET` | `/users` | List employees, shifts, and assigned terminals |
| `GET` | `/events` | List generated protocol transaction events |
| `GET` | `/alerts` | List security threats and category indices |
| `GET` | `/behavior-profiles` | List learned employee baselines |

---

## 5. Installation & Local Development

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Local Run Steps

```bash
# 1. Clone the repository
git clone <repo-url>
cd aegisone

# 2. Create your .env file from the template
cp .env.example .env

# 3. Boot up the entire stack
docker compose up --build
```

| Service | URL |
|---|---|
| **Backend / API Docs** | `http://localhost:8001` / `http://localhost:8001/docs` |
| **Frontend** | `http://localhost:5173` |

---

## 6. Production Deployment & Readiness

AegisOne is production-ready and structured to deploy seamlessly on cloud platforms:

```mermaid
flowchart LR
    A["🐘 Neon\nServerless PostgreSQL"] --> B["🐍 Render\nFastAPI / Uvicorn Backend"]
    B --> C["⚛️ Vercel\nReact Frontend CDN"]
    C -->|HTTPS| D["🧑‍💻 SOC Analyst Browser"]
```

### A. Database — Neon PostgreSQL
1. Provision a serverless PostgreSQL instance on [Neon](https://neon.tech/).
2. Retrieve your connection string, e.g. `postgresql://user:pass@ep-host.us-east-2.aws.neon.tech/neondb?sslmode=require`.

### B. Backend — Render
1. Link your repository to [Render](https://render.com/).
2. Select **Blueprint** to import `render.yaml` automatically, or deploy a **Web Service**:
   - **Runtime:** `Python`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Set environment variables:
   - `SQLALCHEMY_DATABASE_URI` — Neon PostgreSQL connection string
   - `ENVIRONMENT` — `production`
   - `BACKEND_CORS_ORIGINS` — `["https://your-frontend.vercel.app"]`
   - `SEED_DATABASE_ON_STARTUP` — `true`

### C. Frontend — Vercel
1. Connect your repository to [Vercel](https://vercel.com/).
2. Build settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `frontend`
3. Environment variable:
   - `VITE_API_URL` — points to your deployed Render URL (e.g. `https://aegisone-backend.onrender.com/api/v1`)
4. Vercel automatically reads `vercel.json` inside `frontend/` to handle client-side routing.

> 🌐 **Live production instance:** [https://aegis-one-zeta.vercel.app/](https://aegis-one-zeta.vercel.app/)

---

## 7. Technology Stack

### Backend
| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI (async, high concurrency, auto OpenAPI schema) |
| ASGI Server | Uvicorn |
| ORM / Driver | SQLAlchemy 2.0 + psycopg2-binary |
| Migrations | Alembic |

### Analytics & Machine Learning
| Component | Technology |
|---|---|
| Anomaly Detection | Scikit-Learn (Isolation Forest) |
| Vector Math | NumPy & SciPy (Haversine geodetic distance, vector aggregation) |

### Frontend
| Component | Technology |
|---|---|
| Framework | React 19 + TypeScript |
| Bundler | Vite |
| Styling | Tailwind CSS v4 + Vanilla CSS (dark-theme glassmorphism) |
| Icons | Lucide React |

### Data & Hosting
| Component | Technology |
|---|---|
| Database | PostgreSQL (Neon Serverless in production) |
| Real-time Streaming | Server-Sent Events (SSE) |
| Infrastructure | Render (backend) · Vercel (frontend CDN) |

---

## 8. Implementation Methodology & Process

The core behavioral intelligence loop operates on continuous event streams rather than static snapshots.

### System Data Flow Architecture

```mermaid
graph TD
    A[Digital Twin Event Stream / Threat Simulation] -->|1. Live Events Ingest| B[FastAPI /events Endpoint]
    B -->|2. Async Event Queue| C[Behavioral Intelligence Pipeline]
    C -->|3. Feature Store Rollup| D[Feature Store Database]
    D -->|4. Active 1h Feature Vector| E[Anomaly Detection Engine]
    E -->|5. ML Inference: Isolation Forest| F[Score & Criticality Fusion]
    F -->|6. Normalized Risk Score 0-100| G[Risk & Alerts Generator]
    G -->|7. SSE Push| H[SOC Dashboard Panel UI]
    G -->|8. Context Payload| I[AI Security Copilot Drawer]
```

### Anomaly Prediction & Cold Start Logic

```mermaid
flowchart TD
    A[Ingest Entity Feature Vector] --> B{Observation Count > Threshold?}
    B -- Yes --> C[Standard Inference Loop]
    B -- No --> D[Peer Category Lookup]
    D --> E[Retrieve Peer Role/Type Vectors]
    E --> F[Calculate Average Peer Vector]
    F --> G[Blend Vectors: weight = count / threshold]
    G --> C
    C --> H[Run Isolation Forest Predict]
    H --> I[Assess Advanced Rules checks]
    I --> J[Evaluate Risk Score & Criticality]
```

### Threat Simulation Engine Lifecycle

```mermaid
sequenceDiagram
    participant Analyst
    participant ThreatEngine
    participant Database
    participant BehaviorPipeline
    participant SOCDashboard
    Analyst->>ThreatEngine: Click "Run Simulation" (e.g. Credential Stuffing)
    ThreatEngine->>ThreatEngine: Resolve Target IPs, MACs, & Users
    Loop Over Scenario Steps
        ThreatEngine->>Database: Commit Event (Failed/Successful logins)
        ThreatEngine->>BehaviorPipeline: Push Event ID to Queue
        BehaviorPipeline->>SOCDashboard: Stream Event details via SSE
        Note over BehaviorPipeline: Perform advanced checks & ML inference
        BehaviorPipeline->>SOCDashboard: Stream Alert triggered via SSE
    End
```

---

## 9. Frontend SOC Dashboard Operator Guide

AegisOne features a comprehensive, dark-themed **Security Operations Center (SOC) Console**.

| # | Page | Purpose |
|---|---|---|
| 1 | **Dashboard (Operations & Topology)** | Main console for real-time monitoring. Renders the live animated **Digital Twin Topology Map** (subnets, engineering terminals, servers, controllers) alongside metrics cards and the **Attack Injection Panel** |
| 2 | **Industrial Assets** | Tracks physical OT hardware (PLCs, HMIs, Gateways) and renders live telemetry (temperature, pressure, RPM) with color-coded criticality limits |
| 3 | **Devices & Hosts** | Lists authorized workstations, engineering PCs, laptops, and SCADA servers, highlighting OS version and network validation status |
| 4 | **Behavioral Events** | Live protocol transaction log stream (S7Comm, Modbus, OPC-UA) with search/filtering by IP and protocol |
| 5 | **Threat Alerts** | Prioritized alert queue (Impossible Travel, MAC Spoofing, Stuffing sweeps) ranked by risk score, opens the **Incident Investigation Drawer** |
| 6 | **Risk Analytics** | Visualizes dynamic risk trends, vulnerability indexes (0–100), and entity threat contribution factors |
| 7 | **Users & Operators** | Catalog of employees, operators, and analysts — geolocations, TZ parameters, working hour constraints |
| 8 | **Behavior Profiles** | Learned benign profiles per operator (usual device, average event count, normal login shifts) |
| 9 | **Feature Store** | Vectorized rolling telemetry metrics (1h, 24h, 7d) used for model scoring |
| 10 | **Detection Engine** | Retraining console for anomaly models — retrain entity models, configure contamination ratios |
| 11 | **Threat Simulation** | Launch controls for full cyberattack timelines (Low-and-Slow Exfiltration, USB Malware, Stuffing, etc.) |
| 12 | **System Operations** | Admin page — hardware telemetry (CPU, RAM, Disk), REST API counters, DB connection indicators, CSV audit log exports |

---

## 10. Live Demonstration Checklist

For details on performing a live presentation and triggering simulated scenarios, refer to the AegisOne Demo Checklist (`docs/demo_checklist.md`).

---

<div align="center">

### 🔗 [**Launch AegisOne Live Demo →**](https://aegis-one-zeta.vercel.app/)

Made with ⚙️ FastAPI · ⚛️ React · 🐘 PostgreSQL

</div>
