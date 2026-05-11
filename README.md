# Digital Twin — Assembly Line Simulation

> A full-stack discrete-event simulation platform for assembly line analysis.  
> Configure stations, run scenarios, watch parts move live, and export PDF/CSV reports.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, Tailwind CSS, Recharts, Zustand, React Query |
| Backend | FastAPI (Python 3.11), SimPy, SQLAlchemy, Pydantic v2 |
| Database | SQLite (development) / PostgreSQL (production) |
| Deployment | Docker, Docker Compose, Nginx reverse proxy |

---

## Features

- Configure a 5-station assembly line with custom cycle times, buffers, and operators
- Run simulations with multiple replications for statistical reliability
- Real-time WebSocket streaming of simulation events
- Live animated SVG assembly line visualizer — parts move, buffers fill, bottleneck turns red
- Metrics per scenario: throughput, lead time, station utilization, bottleneck detection
- Side-by-side scenario comparison with improvement percentages
- Export results as CSV or a formatted PDF report
- Save and reload named scenario configurations
- 46 backend tests (pytest) + 16 frontend tests (vitest) — all passing

---

## Project Structure

```
digital_twin_app/
├── backend/
│   ├── main.py                   # FastAPI app, CORS, lifespan, error handlers
│   ├── config.py                 # All settings from environment variables
│   ├── routers/
│   │   ├── simulation.py         # Run, status, results, WebSocket
│   │   ├── scenarios.py          # Save / load / delete scenarios
│   │   ├── reports.py            # CSV and PDF export
│   │   └── health.py             # Health check endpoint
│   ├── simulation/
│   │   ├── engine.py             # SimPy discrete-event engine
│   │   ├── station.py            # Station resource, buffer, breakdown logic
│   │   ├── part.py               # Part dataclass with per-station timestamps
│   │   └── metrics.py            # Aggregation across replications
│   ├── services/
│   │   ├── simulation_service.py # Background task runner
│   │   ├── report_service.py     # ReportLab PDF generation
│   │   └── export_service.py     # CSV assembly
│   ├── models/                   # Pydantic v2 request and response models
│   ├── db/                       # SQLAlchemy ORM, Alembic migrations, CRUD
│   ├── tests/                    # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx     # History table, summary stats
│   │   │   ├── Configure.jsx     # Station form, presets, validation
│   │   │   ├── RunSimulation.jsx # Live WebSocket visualizer
│   │   │   └── Reports.jsx       # Charts, comparison table, export
│   │   ├── components/
│   │   │   ├── LineVisualizer.jsx        # Animated SVG assembly line
│   │   │   ├── MetricsTable.jsx          # Scenario comparison table
│   │   │   ├── ThroughputChart.jsx       # Bar chart
│   │   │   ├── UtilizationChart.jsx      # Bar + radar chart
│   │   │   ├── LeadTimeChart.jsx         # Histogram
│   │   │   ├── StationCard.jsx
│   │   │   └── ExportPanel.jsx
│   │   ├── hooks/
│   │   │   ├── useSimulation.js   # React Query wrapper
│   │   │   ├── useWebSocket.js    # Live event stream
│   │   │   └── useExport.js       # Blob download handler
│   │   ├── api/client.js          # Axios, base URL from env
│   │   └── store/simulationStore.js  # Zustand global state + presets
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml            # Local development with hot reload
├── docker-compose.prod.yml       # Production: Gunicorn + PostgreSQL + Nginx
└── README.md
```

---

## Quick Start

### Option 1 — Docker (Recommended)

```bash
cd digital_twin_app
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/api/docs |

---

### Option 2 — Manual Setup

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`

---

## Running Tests

**Backend**

```bash
cd backend
pytest tests/ -v --cov=. --cov-report=html
```

**Frontend**

```bash
cd frontend
npm run test
npm run test:coverage
```

---

## Production Deployment

### 1. Configure environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set:

```env
APP_ENV=production
APP_SECRET_KEY=your-strong-random-key
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/digital_twin
CORS_ORIGINS=https://yourdomain.com
MAX_CONCURRENT_SIMULATIONS=5
```

### 2. Deploy

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

This starts:
- FastAPI behind Gunicorn + Uvicorn workers
- React built and served by Nginx
- PostgreSQL database
- Nginx reverse proxy on port 80

### 3. Run database migrations

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 4. Access

| Service | URL |
|---|---|
| Application | http://your-server-ip |
| API | http://your-server-ip/api |
| API Docs | http://your-server-ip/api/docs |

---

## API Reference

### Simulations

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/simulations/run` | Start a simulation, returns `job_id` |
| GET | `/api/simulations/{job_id}/status` | Poll status and progress percentage |
| GET | `/api/simulations/{job_id}/results` | Fetch full metrics when complete |
| GET | `/api/simulations/history` | List all past simulation runs |
| WS | `/api/simulations/ws/{job_id}` | Real-time event stream |

### Scenarios

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/scenarios` | Save a named scenario configuration |
| GET | `/api/scenarios` | List all saved scenarios |
| GET | `/api/scenarios/{id}` | Get a scenario by ID |
| DELETE | `/api/scenarios/{id}` | Delete a scenario |

### Reports

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/reports/{job_id}/csv` | Download metrics as CSV |
| GET | `/api/reports/{job_id}/csv/lead_times` | Download per-part lead time CSV |
| GET | `/api/reports/{job_id}/pdf` | Download formatted PDF report |

### Health

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |

---

## Environment Variables

**Backend** (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development` or `production` |
| `APP_SECRET_KEY` | — | Secret key for sessions |
| `DATABASE_URL` | SQLite path | SQLAlchemy connection string |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins |
| `MAX_CONCURRENT_SIMULATIONS` | `5` | Rate limit for parallel runs |

**Frontend** (`frontend/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL |
| `VITE_WS_URL` | `ws://localhost:8000` | WebSocket base URL |

---

## Simulation Results (Default Scenarios)

Each scenario runs 10 replications with different random seeds. Results are averaged.

| Metric | Base Case | + Extra Buffer | Bottleneck Fix |
|---|---|---|---|
| Parts produced / shift | 644 | 643 | 900 |
| Throughput (parts/hr) | 85.9 | 85.8 | 120.0 |
| Avg lead time | 10.0 min | 13.5 min | 12.5 min |
| Bottleneck station | Drilling 99.9% | Drilling 99.9% | Inspection 73.1% |
| Improvement vs base | — | −0.1% | **+39.7%** |

**Key finding:** Adding a second operator at the Drilling station shifts the bottleneck to Inspection and delivers a 40% throughput gain. Increasing buffer size alone does not help because the constraint is cycle time, not queue space.

---

## Development

**Format backend**

```bash
black backend/
isort backend/
```

**Lint frontend**

```bash
npm run lint
npm run format
```

**Create a database migration**

```bash
cd backend
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

---

## Troubleshooting

**CORS errors**
- Check `CORS_ORIGINS` in `backend/.env`
- Ensure `VITE_API_URL` in the frontend matches the backend address

**WebSocket connection fails**
- Verify `VITE_WS_URL` is correct
- Check firewall rules allow WebSocket traffic on the backend port

**Simulation hangs or never completes**
- Check backend logs: `docker-compose logs backend`
- Verify `MAX_CONCURRENT_SIMULATIONS` limit has not been reached

**Database connection error (production)**
- Confirm PostgreSQL container is healthy: `docker-compose ps`
- Check the `DATABASE_URL` format matches `postgresql+asyncpg://user:pass@host:port/dbname`

---

## License

MIT

---

## About

Built as a demonstration of discrete-event simulation applied to manufacturing process optimization. The simulation engine uses SimPy to model station cycle times with variability, buffer queues, operator resources, and random machine breakdowns — the same concepts used in industrial tools like Siemens Tecnomatix Plant Simulation.
