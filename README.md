# Digital Twin — Assembly Line Simulation

Full-stack web application for discrete-event simulation of an assembly line with real-time visualization.

## Architecture

- **Backend**: FastAPI (Python 3.11) with SQLAlchemy, SimPy simulation engine
- **Frontend**: React 18 + Vite, Tailwind CSS, Recharts, Zustand, React Query
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Deployment**: Docker + Docker Compose, Nginx reverse proxy

## Features

- ✅ Configure 5-station assembly line with custom parameters
- ✅ Run simulations with multiple replications for statistical reliability
- ✅ Real-time WebSocket streaming of simulation events
- ✅ Live animated SVG assembly line visualizer
- ✅ Comprehensive metrics: throughput, lead time, utilization, bottlenecks
- ✅ Scenario comparison with improvement calculations
- ✅ Export to CSV and PDF reports
- ✅ Save and load scenario configurations
- ✅ Full test coverage (backend pytest, frontend vitest)

## Quick Start — Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)

### Option 1: Docker Compose (Recommended)

```bash
# Clone and navigate
cd digital_twin_app

# Start all services
docker-compose up --build

# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### Option 2: Manual Setup

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173

## Running Tests

**Backend:**

```bash
cd backend
pytest tests/ -v --cov=. --cov-report=html
```

**Frontend:**

```bash
cd frontend
npm run test
npm run test:coverage
```

## Production Deployment

### 1. Prepare Environment

```bash
# Copy and edit production env file
cp backend/.env.example backend/.env

# Set production values:
# - APP_ENV=production
# - APP_SECRET_KEY=<strong-random-key>
# - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/digital_twin
# - CORS_ORIGINS=https://yourdomain.com
```

### 2. Deploy with Docker Compose

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

This starts:
- FastAPI backend with Gunicorn + Uvicorn workers
- React frontend built and served by Nginx
- PostgreSQL database
- Nginx reverse proxy (port 80)

### 3. Database Migrations (if using Alembic)

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 4. Access

- Frontend: http://your-server-ip
- API: http://your-server-ip/api
- API Docs: http://your-server-ip/api/docs

## Project Structure

```
digital_twin_app/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings from environment
│   ├── routers/                # API endpoints
│   │   ├── simulation.py       # Run, status, results, WebSocket
│   │   ├── scenarios.py        # Save/load scenarios
│   │   ├── reports.py          # CSV/PDF export
│   │   └── health.py           # Health check
│   ├── simulation/             # SimPy simulation engine
│   │   ├── engine.py
│   │   ├── station.py
│   │   ├── part.py
│   │   └── metrics.py
│   ├── services/               # Business logic
│   │   ├── simulation_service.py
│   │   ├── report_service.py
│   │   └── export_service.py
│   ├── models/                 # Pydantic request/response models
│   ├── db/                     # SQLAlchemy ORM, CRUD
│   ├── tests/                  # Pytest tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── pages/              # Dashboard, Configure, RunSimulation, Reports
│   │   ├── components/         # Reusable UI components
│   │   ├── hooks/              # useSimulation, useWebSocket, useExport
│   │   ├── api/                # Axios client
│   │   └── store/              # Zustand state management
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml          # Development
├── docker-compose.prod.yml     # Production
└── README.md
```

## API Endpoints

### Simulations

- `POST /api/simulations/run` — Start a simulation (returns job_id)
- `GET /api/simulations/{job_id}/status` — Get status and progress
- `GET /api/simulations/{job_id}/results` — Get full results
- `GET /api/simulations/history` — List all past runs
- `WS /api/simulations/ws/{job_id}` — Real-time event stream

### Scenarios

- `POST /api/scenarios` — Save a scenario configuration
- `GET /api/scenarios` — List all saved scenarios
- `GET /api/scenarios/{id}` — Get a scenario by ID
- `DELETE /api/scenarios/{id}` — Delete a scenario

### Reports

- `GET /api/reports/{job_id}/csv` — Download metrics CSV
- `GET /api/reports/{job_id}/csv/lead_times` — Download lead times CSV
- `GET /api/reports/{job_id}/pdf` — Download PDF report

### Health

- `GET /health` — Health check

## Configuration

All configuration is via environment variables (see `.env.example`):

- `APP_ENV` — development | production
- `APP_SECRET_KEY` — Secret key for sessions
- `DATABASE_URL` — Database connection string
- `CORS_ORIGINS` — Comma-separated allowed origins
- `MAX_CONCURRENT_SIMULATIONS` — Rate limit (default: 5)

Frontend environment variables (`.env` in frontend/):

- `VITE_API_URL` — Backend API base URL (default: http://localhost:8000)
- `VITE_WS_URL` — WebSocket base URL (default: ws://localhost:8000)

## Development

### Code Quality

**Backend:**

```bash
black backend/
isort backend/
```

**Frontend:**

```bash
npm run lint
npm run format
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Troubleshooting

**CORS errors:**
- Check `CORS_ORIGINS` in backend `.env`
- Ensure frontend is accessing the correct API URL

**WebSocket connection fails:**
- Verify `VITE_WS_URL` in frontend
- Check firewall rules for WebSocket traffic

**Simulation hangs:**
- Check backend logs: `docker-compose logs backend`
- Verify `MAX_CONCURRENT_SIMULATIONS` limit not reached

**Database connection errors:**
- Ensure PostgreSQL is running (production)
- Check `DATABASE_URL` format

## License

MIT

## Support

For issues, please open a GitHub issue with:
- Environment (dev/prod, OS, Docker version)
- Steps to reproduce
- Relevant logs
