# AegisOne: Industrial Behavioral Intelligence Platform

AegisOne (Aegis = protection/shield in Greek mythology and
One = unified platform) is an enterprise-grade Industrial Behavioral Intelligence Platform designed to secure Operational Technology (OT), Industrial IoT (IIoT), SCADA systems, PLCs, industrial control systems, manufacturing plants, and critical infrastructure. 

Unlike traditional signature-based cybersecurity systems, AegisOne continuously models the behavioral patterns of users, industrial devices, applications, and connected assets to detect insider threats, compromised accounts, unauthorized access, abnormal industrial operations, and cyberattacks in real time.

---

## 1. Architecture Overview

AegisOne follows **Clean Architecture** principles to separate concerns, enforce maintainability, and allow future modules (such as Machine Learning anomaly detection and threat classifiers) to plug in without modifying core components.

```
       [ Client React SPA (Port 5173 / 80) ]
                       |
                       |  REST HTTPS (JSON)
                       v
     [ FastAPI Gateway Controller (Port 8000) ]
                       |
        +--------------+--------------+
        |                             |
        v                             v
[ Service Layer ] &lt;--------&gt; [ Simulation Engine (Background Loop) ]
        |
        v
[ Repository CRUD ]
        |
        v
[ SQLAlchemy ORM (Base Model) ]
        |
        v
 [ PostgreSQL Database (Port 5442) ]
```

- **API Layer**: FastAPI routes receive payloads, execute validation (via Pydantic), and return responses. No business logic lives in this layer.
- **Service Layer**: Handles orchestrations, checks permissions, constructs domain models, and manages background tasks. The background **Simulation Engine** runs here.
- **Repository Layer**: Encapsulates raw database queries (via SQLAlchemy 2.0 select/insert) to abstract data access away from business services.
- **Model Layer**: Defines mapping contracts to the database via SQLAlchemy declarative base mapping.

---

## 2. Folder Structure Explanation

```
aegisone/
├── docker-compose.yml           # Multi-container orchestration (App + DB)
├── .env.example                 # Template for configuration parameters
├── database/
│   └── migrations/             # Alembic migration scripts and history
│       ├── env.py              # Configuration mapping models to DB
│       ├── script.py.mako      # Migration generation template
│       └── versions/           # Auto-generated database migration scripts
├── docker/
│   ├── backend.Dockerfile       # Python container definition
│   ├── frontend.Dockerfile      # Multi-stage Node + Nginx container definition
│   └── nginx.conf               # Nginx server configuration for React routing
├── backend/
│   ├── requirements.txt         # Backend Python dependencies
│   ├── alembic.ini              # Alembic config mapping to migrations directory
│   └── app/
│       ├── main.py              # FastAPI entry point & exception middleware
│       ├── api/
│       │   └── v1/
│       │       ├── api.py       # Main API routes aggregator
│       │       └── endpoints/   # Individual controllers (health, assets, simulation, etc.)
│       ├── core/
│       │   └── config.py        # Centralized app configuration (Pydantic Settings)
│       ├── database/
│       │   └── session.py       # SQLAlchemy engine & session pool setup
│       ├── models/              # SQLAlchemy model definitions (ORM)
│       ├── schemas/             # Pydantic schemas (Serialization & Request Validation)
│       ├── repositories/        # Repository pattern classes (SQL CRUD)
│       ├── services/            # Business services (simulation engine, seeding)
│       └── middleware/          # Request logging and RFC-7807 error formatting
├── frontend/
│   ├── package.json             # React node packages definition
│   ├── vite.config.ts           # Vite bundler options with Tailwind CSS v4 compiler
│   └── src/
│       ├── api/                 # Axios clients and HTTP interfaces
│       ├── context/             # Global health & polling monitors
│       ├── types/               # TypeScript interface configurations
│       ├── components/          # Reusable UI cards, headers, sidebars
│       └── pages/               # Main sub-views (Dashboard, Assets, Alerts, etc.)
```

---

## 3. Database Design

AegisOne utilizes a normalized PostgreSQL database designed for future industrial security analytics:
- **Departments**: Mapped organizational branches (Production, QA, Maintenance, IT, HR, etc.).
- **Users**: Employees, roles, working hour boundaries, shift bindings (Morning/Afternoon/Night), and managers.
- **Devices**: Network hosts (Engineering Workstations, Office PCs, PLCs, Badge Readers) mapped by IP, MAC, zone (DMZ, OT-Control, OT-Field), status (Authorized/Quarantined), and assigned user.
- **Industrial Assets**: Factory hardware (Boiler, Robotic Arm, Conveyor) maintaining real-time `operational_state` parameters (temperature, pressure, rpm).
- **Behavior Profiles**: Baseline signatures representing normal login schedules, typical apps, normal devices used, and network frequencies.
- **Events**: Serialized protocol stream logs (Modbus, S7comm, OPC-UA) containing timestamp, source/destination IPs, operational payloads, and severity.
- **Alerts**: Security anomaly records cataloged by severity, status, and affected assets.
- **Risk Scores**: Dynamic vulnerability indexes (0-100) calculated based on alert events.

---

## 4. API Reference Documentation

All endpoints are exposed under `/api/v1`.

### Health Check
- **`GET /health`**
  Returns connection state to the database and overall API health.

### Simulation Controls
- **`GET /simulation/status`**
  Fetches status (IDLE, RUNNING, PAUSED, STOPPED), counts of active twin assets, and the virtual time clock.
- **`POST /simulation/start`**
  Spins up the background simulator thread.
- **`POST /simulation/pause`**
  Pauses the simulation, freezing virtual clock progression.
- **`POST /simulation/resume`**
  Resumes execution from paused state.
- **`POST /simulation/stop`**
  Stops execution, resetting elapsed timers.
- **`POST /simulation/reset`**
  Truncates telemetry history tables (Events, Alerts, AuditLogs, RiskScores) to restart testing cleanly.
- **`POST /simulation/config`**
  Updates the speed multiplier, event generation rate, and target counts.

### Telemetry Queries
- **`GET /industrial-assets`**: List OT assets and live sensor telemetry.
- **`GET /devices`**: List network host terminals and security statuses.
- **`GET /users`**: List employees, shifts, and assigned terminals.
- **`GET /events`**: List generated protocol transaction events.
- **`GET /alerts`**: List security threats and category indices.
- **`GET /behavior-profiles`**: List learned employee baselines.

---

## 5. Installation & Local Development

### Prerequisites
- Install [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/).

### Local Run Steps
1. Clone this repository to your workspace.
2. In the root directory, create a `.env` file from the template:
   ```bash
   cp .env.example .env
   ```
3. Boot up the entire stack using Docker Compose:
   ```bash
   docker compose up --build
   ```
4. Access:
   - Backend available at `http://localhost:8001` (API documentation at `http://localhost:8001/docs`)
   - Frontend available at `http://localhost:5173`

---

## 6. Production Deployment & Readiness

AegisOne is production-ready and structured to deploy seamlessly on cloud platforms:

### A. Database (Neon PostgreSQL)
1. Provision a serverless PostgreSQL instance on [Neon](https://neon.tech/).
2. Retrieve your connection string (e.g. `postgresql://user:pass@ep-host.us-east-2.aws.neon.tech/neondb?sslmode=require`).

### B. Backend (Render)
1. Link your repository to [Render](https://render.com/).
2. Select **Blueprint** to import the `render.yaml` service definition automatically, or deploy a **Web Service**:
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Expose the environment variables:
   - `SQLALCHEMY_DATABASE_URI`: Your Neon PostgreSQL connection string.
   - `ENVIRONMENT`: `production`
   - `BACKEND_CORS_ORIGINS`: `["https://your-frontend.vercel.app"]`
   - `SEED_DATABASE_ON_STARTUP`: `true`

### C. Frontend (Vercel)
1. Connect your repository to [Vercel](https://vercel.com/).
2. Set the build parameters:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
3. Configure the environment variables:
   - `VITE_API_URL`: Points to your deployed Render URL (e.g. `https://aegisone-backend.onrender.com/api/v1`).
4. Vercel will automatically read the `vercel.json` routing configuration inside `frontend/` to handle client-side path routes.

---

## 7. Live Demonstration Checklist
For details on performing a live presentation and triggering simulated scenarios, refer to the [AegisOne Demo Checklist](file:///Users/kmrinal/AegisOne/docs/demo_checklist.md).

---

## 8. Frontend SOC Dashboard Operator Guide

AegisOne features a comprehensive, dark-themed Security Operations Center (SOC) Console. Below is a breakdown of how to use the dashboard and what each sub-page is dedicated for:

### Page-by-Page Breakdown

1. **Dashboard (Operations & Topology)**
   - *Purpose*: The main console for real-time monitoring. Renders the live animated **Digital Twin Topology Map** (mapping subnets, engineering terminals, servers, and controllers) alongside metrics cards and the **Attack Injection Panel** at the footer.
   
2. **Industrial Assets**
   - *Purpose*: Tracks physical OT hardware catalog details (PLCs, HMIs, Gateways) and renders live telemetry sensors (temperature, pressure, RPM) with color-coded criticality limits.
   
3. **Devices & Hosts**
   - *Purpose*: Lists all authorized workstations, engineering PCs, laptops, and SCADA servers interacting with the ICS subnets, highlighting their OS version and network validation status.
   
4. **Behavioral Events**
   - *Purpose*: A live protocol transaction log stream collecting all S7Comm, Modbus, and OPC-UA events, allowing search/filtering by IP and protocol values.
   
5. **Threat Alerts**
   - *Purpose*: A prioritized alert queue displaying detected security events (e.g. Impossible Travel, MAC Spoofing, Stuffing sweeps) ranked by risk scores. Clicking an alert opens the **Incident Investigation Drawer**.
   
6. **Risk Analytics**
   - *Purpose*: Visualizes dynamic risk trends, vulnerability indexes (0-100), and entity threat contribution factors.
   
7. **Users & Operators**
   - *Purpose*: Catalog of employees, operators, and analysts, mapping their default geolocations, TZ parameters, and working hours constraints.
   
8. **Behavior Profiles**
   - *Purpose*: Displays learned benign profiles for each operator (usual device, average event count, normal login shifts) mapping normal baselines.
   
9. **Feature Store**
   - *Purpose*: Visualizes vectorized rolling telemetry metrics (1h, 24h, 7d) used for model scoring.
   
10. **Detection Engine**
    - *Purpose*: Retraining console for anomaly models. Lets operators retrain entity models on feature vectors and configure model contamination ratios.
    
11. **Threat Simulation**
    - *Purpose*: Launch controls to run full cyberattack timelines (Low-and-Slow Exfiltration, USB Malware, Stuffing, etc.) with real-time progression feeds.
    
12. **System Operations**
    - *Purpose*: Admin page for hardware telemetry (CPU, RAM, Disk), REST API response counters, system health details, database connection indicators, and CSV exports of audit logs.


