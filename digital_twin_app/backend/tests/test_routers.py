"""Tests for API routers."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthRouter:
    async def test_health_ok(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert data["database"] == "ok"

    async def test_health_returns_active_simulations(self, client: AsyncClient):
        resp = await client.get("/health")
        assert "active_simulations" in resp.json()


@pytest.mark.asyncio
class TestSimulationRouter:
    async def test_run_simulation_returns_job_id(self, client: AsyncClient, base_config):
        resp = await client.post("/api/simulations/run", json=base_config)
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    async def test_run_simulation_invalid_config(self, client: AsyncClient):
        resp = await client.post("/api/simulations/run", json={"name": "bad"})
        assert resp.status_code == 422

    async def test_run_simulation_duplicate_station_names(self, client: AsyncClient, base_config):
        config = dict(base_config)
        config["stations"] = [config["stations"][0], config["stations"][0]]
        resp = await client.post("/api/simulations/run", json=config)
        assert resp.status_code == 422

    async def test_get_status_not_found(self, client: AsyncClient):
        resp = await client.get("/api/simulations/nonexistent-id/status")
        assert resp.status_code == 404

    async def test_get_status_after_queue(self, client: AsyncClient, base_config):
        run_resp = await client.post("/api/simulations/run", json=base_config)
        job_id = run_resp.json()["job_id"]

        status_resp = await client.get(f"/api/simulations/{job_id}/status")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["job_id"] == job_id
        assert data["status"] in ("queued", "running", "complete")

    async def test_get_results_not_found(self, client: AsyncClient):
        resp = await client.get("/api/simulations/nonexistent-id/results")
        assert resp.status_code == 404

    async def test_get_history_empty(self, client: AsyncClient):
        resp = await client.get("/api/simulations/history")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_get_history_after_run(self, client: AsyncClient, base_config):
        await client.post("/api/simulations/run", json=base_config)
        resp = await client.get("/api/simulations/history")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_rate_limit_enforced(self, client: AsyncClient, base_config, monkeypatch):
        """Rate limit should reject when max concurrent simulations reached."""
        # Patch the function in the routers.simulation module namespace
        import routers.simulation as sim_router
        monkeypatch.setattr(sim_router, "get_active_count", lambda: 999)

        resp = await client.post("/api/simulations/run", json=base_config)
        assert resp.status_code == 429


@pytest.mark.asyncio
class TestScenariosRouter:
    async def test_list_scenarios_empty(self, client: AsyncClient):
        resp = await client.get("/api/scenarios")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_save_scenario(self, client: AsyncClient, base_config):
        payload = {
            "name": "My Scenario",
            "description": "Test scenario",
            "config": base_config,
        }
        resp = await client.post("/api/scenarios", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Scenario"
        assert "id" in data

    async def test_list_scenarios_after_save(self, client: AsyncClient, base_config):
        payload = {"name": "S1", "description": "", "config": base_config}
        await client.post("/api/scenarios", json=payload)
        resp = await client.get("/api/scenarios")
        assert len(resp.json()) == 1

    async def test_delete_scenario(self, client: AsyncClient, base_config):
        payload = {"name": "ToDelete", "description": "", "config": base_config}
        create_resp = await client.post("/api/scenarios", json=payload)
        scenario_id = create_resp.json()["id"]

        del_resp = await client.delete(f"/api/scenarios/{scenario_id}")
        assert del_resp.status_code == 204

        list_resp = await client.get("/api/scenarios")
        assert list_resp.json() == []

    async def test_delete_nonexistent_scenario(self, client: AsyncClient):
        resp = await client.delete("/api/scenarios/nonexistent")
        assert resp.status_code == 404

    async def test_get_scenario_by_id(self, client: AsyncClient, base_config):
        payload = {"name": "GetMe", "description": "desc", "config": base_config}
        create_resp = await client.post("/api/scenarios", json=payload)
        scenario_id = create_resp.json()["id"]

        get_resp = await client.get(f"/api/scenarios/{scenario_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "GetMe"


@pytest.mark.asyncio
class TestReportsRouter:
    async def test_csv_not_found(self, client: AsyncClient):
        resp = await client.get("/api/reports/nonexistent/csv")
        assert resp.status_code == 404

    async def test_pdf_not_found(self, client: AsyncClient):
        resp = await client.get("/api/reports/nonexistent/pdf")
        assert resp.status_code == 404
