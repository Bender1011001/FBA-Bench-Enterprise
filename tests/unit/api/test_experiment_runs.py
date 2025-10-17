"""Unit tests for experiment runs API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from fba_bench_api.models.experiments import (
    ExperimentParticipant,
    ExperimentRun,
    ExperimentRunCreate,
    RunProgress,
    RunStatus,
)
from fba_bench_api.models.scenarios import Scenario
from fba_bench_api.server.app_factory import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_persistence_manager():
    """Mock async persistence manager."""
    pm = Mock()
    pm.experiments = Mock(return_value=Mock())
    pm.agents = Mock(return_value=Mock())
    return pm


@pytest.fixture
def sample_experiment():
    """Sample experiment data."""
    return {
        "id": "exp-123",
        "name": "Test Experiment",
        "description": "Test description",
        "agent_id": "agent-456",
        "scenario_id": "tier_0_baseline",
        "status": "draft",
        "params": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_agent():
    """Sample agent data."""
    return {
        "id": "agent-456",
        "name": "Test Agent",
        "framework": "baseline",
        "config": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_scenario():
    """Sample scenario for testing."""
    return Scenario(
        id="tier_0_baseline",
        name="Tier 0 Baseline",
        description="Basic scenario",
        difficulty_tier=0,
        expected_duration=30,
        tags=["tier_0"],
        default_params={},
        success_criteria={},
        market_conditions={},
        external_events=[],
        agent_constraints={},
    )


@pytest.fixture
def sample_participant():
    """Sample experiment participant."""
    return ExperimentParticipant(
        agent_id="agent-456", role="primary", config_override={}
    )


@pytest.fixture
def sample_run_create(sample_participant):
    """Sample experiment run create request."""
    return ExperimentRunCreate(
        scenario_id="tier_0_baseline",
        participants=[sample_participant],
        params={"test_param": "value"},
    )


class TestExperimentRunModels:
    """Test experiment run model validation."""

    def test_experiment_participant_validation(self):
        """Test experiment participant model validation."""
        participant = ExperimentParticipant(
            agent_id="agent-123", role="primary", config_override={"setting": "value"}
        )

        assert participant.agent_id == "agent-123"
        assert participant.role == "primary"
        assert participant.config_override == {"setting": "value"}

    def test_experiment_participant_empty_fields(self):
        """Test experiment participant with empty required fields."""
        with pytest.raises(ValueError, match="Field must be non-empty"):
            ExperimentParticipant(agent_id="", role="primary", config_override={})

        with pytest.raises(ValueError, match="Field must be non-empty"):
            ExperimentParticipant(agent_id="agent-123", role="", config_override={})

    def test_experiment_run_create_validation(self, sample_participant):
        """Test experiment run create model validation."""
        run_create = ExperimentRunCreate(
            scenario_id="test_scenario",
            participants=[sample_participant],
            params={"key": "value"},
        )

        assert run_create.scenario_id == "test_scenario"
        assert len(run_create.participants) == 1
        assert run_create.params == {"key": "value"}

    def test_experiment_run_create_empty_scenario(self, sample_participant):
        """Test experiment run create with empty scenario ID."""
        with pytest.raises(ValueError, match="scenario_id must be non-empty"):
            ExperimentRunCreate(
                scenario_id="", participants=[sample_participant], params={}
            )

    def test_experiment_run_create_no_participants(self):
        """Test experiment run create with no participants."""
        with pytest.raises(ValueError, match="At least one participant is required"):
            ExperimentRunCreate(scenario_id="test_scenario", participants=[], params={})

    def test_experiment_run_create_duplicate_agents(self):
        """Test experiment run create with duplicate agent IDs."""
        participants = [
            ExperimentParticipant(
                agent_id="agent-123", role="primary", config_override={}
            ),
            ExperimentParticipant(
                agent_id="agent-123", role="secondary", config_override={}
            ),
        ]

        with pytest.raises(
            ValueError, match="Agent IDs must be unique among participants"
        ):
            ExperimentRunCreate(
                scenario_id="test_scenario", participants=participants, params={}
            )

    def test_experiment_run_model(self, sample_participant):
        """Test experiment run model."""
        run = ExperimentRun(
            id="run-123",
            experiment_id="exp-456",
            scenario_id="scenario-789",
            participants=[sample_participant],
            params={"test": "value"},
            status="running",
            current_tick=50,
            total_ticks=100,
            progress_percent=50.0,
        )

        assert run.id == "run-123"
        assert run.experiment_id == "exp-456"
        assert run.scenario_id == "scenario-789"
        assert run.status == "running"
        assert run.current_tick == 50
        assert run.total_ticks == 100
        assert run.progress_percent == 50.0

    def test_run_status_model(self):
        """Test run status model."""
        status = RunStatus(
            experiment_id="exp-123",
            run_id="run-456",
            status="running",
            progress_percent=75.0,
            current_tick=75,
            total_ticks=100,
            started_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        assert status.experiment_id == "exp-123"
        assert status.run_id == "run-456"
        assert status.status == "running"
        assert status.progress_percent == 75.0

    def test_run_progress_model(self):
        """Test run progress model."""
        progress = RunProgress(
            experiment_id="exp-123",
            run_id="run-456",
            current_tick=25,
            total_ticks=100,
            progress_percent=25.0,
            elapsed_time_seconds=120.5,
            estimated_remaining_seconds=362.5,
            ticks_per_second=0.21,
            memory_usage_mb=128.5,
        )

        assert progress.experiment_id == "exp-123"
        assert progress.run_id == "run-456"
        assert progress.current_tick == 25
        assert progress.total_ticks == 100
        assert progress.progress_percent == 25.0
        assert progress.elapsed_time_seconds == 120.5


class TestExperimentRunsAPI:
    """Test experiment runs API endpoints."""

    @patch("fba_bench_api.api.routes.experiments.get_scenario_service")
    @patch("fba_bench_api.api.routes.experiments._start_experiment_run")
    def test_start_experiment_success(
        self,
        mock_start_run,
        mock_get_scenario_service,
        client,
        mock_persistence_manager,
        sample_experiment,
        sample_agent,
        sample_scenario,
        sample_run_create,
    ):
        """Test successful experiment start."""
        # Setup mocks
        mock_scenario_service = Mock()
        mock_scenario_service.get_scenario.return_value = sample_scenario
        mock_get_scenario_service.return_value = mock_scenario_service

        mock_exp_repo = Mock()
        mock_exp_repo.get = AsyncMock(return_value=sample_experiment)
        mock_exp_repo.update = AsyncMock(return_value=sample_experiment)
        mock_persistence_manager.experiments.return_value = mock_exp_repo

        mock_agent_repo = Mock()
        mock_agent_repo.get = AsyncMock(return_value=sample_agent)
        mock_persistence_manager.agents.return_value = mock_agent_repo

        with patch(
            "fba_bench_api.api.routes.experiments.get_pm",
            return_value=mock_persistence_manager,
        ):
            response = client.post(
                "/api/v1/experiments/exp-123/start", json=sample_run_create.model_dump()
            )

        assert response.status_code == 202
        data = response.json()
        assert data["experiment_id"] == "exp-123"
        assert data["status"] == "pending"
        assert data["participants_count"] == 1
        assert "run_id" in data
        assert "message" in data

    @patch("fba_bench_api.api.routes.experiments.get_scenario_service")
    def test_start_experiment_not_found(
        self,
        mock_get_scenario_service,
        client,
        mock_persistence_manager,
        sample_run_create,
    ):
        """Test starting experiment when experiment not found."""
        mock_exp_repo = Mock()
        mock_exp_repo.get = AsyncMock(return_value=None)
        mock_persistence_manager.experiments.return_value = mock_exp_repo

        with patch(
            "fba_bench_api.api.routes.experiments.get_pm",
            return_value=mock_persistence_manager,
        ):
            response = client.post(
                "/api/v1/experiments/nonexistent/start",
                json=sample_run_create.model_dump(),
            )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("fba_bench_api.api.routes.experiments.get_scenario_service")
    def test_start_experiment_wrong_status(
        self,
        mock_get_scenario_service,
        client,
        mock_persistence_manager,
        sample_experiment,
        sample_run_create,
    ):
        """Test starting experiment with wrong status."""
        sample_experiment["status"] = "running"  # Not draft

        mock_exp_repo = Mock()
        mock_exp_repo.get = AsyncMock(return_value=sample_experiment)
        mock_persistence_manager.experiments.return_value = mock_exp_repo

        with patch(
            "fba_bench_api.api.routes.experiments.get_pm",
            return_value=mock_persistence_manager,
        ):
            response = client.post(
                "/api/v1/experiments/exp-123/start", json=sample_run_create.model_dump()
            )

        assert response.status_code == 400
        assert "draft" in response.json()["detail"]

    @patch("fba_bench_api.api.routes.experiments.get_scenario_service")
    def test_start_experiment_scenario_not_found(
        self,
        mock_get_scenario_service,
        client,
        mock_persistence_manager,
        sample_experiment,
        sample_run_create,
    ):
        """Test starting experiment with nonexistent scenario."""
        mock_scenario_service = Mock()
        mock_scenario_service.get_scenario.return_value = None
        mock_get_scenario_service.return_value = mock_scenario_service

        mock_exp_repo = Mock()
        mock_exp_repo.get = AsyncMock(return_value=sample_experiment)
        mock_persistence_manager.experiments.return_value = mock_exp_repo

        with patch(
            "fba_bench_api.api.routes.experiments.get_pm",
            return_value=mock_persistence_manager,
        ):
            response = client.post(
                "/api/v1/experiments/exp-123/start", json=sample_run_create.model_dump()
            )

        assert response.status_code == 404
        assert "Scenario" in response.json()["detail"]

    @patch("fba_bench_api.api.routes.experiments.get_scenario_service")
    def test_start_experiment_agent_not_found(
        self,
        mock_get_scenario_service,
        client,
        mock_persistence_manager,
        sample_experiment,
        sample_scenario,
        sample_run_create,
    ):
        """Test starting experiment with nonexistent agent."""
        mock_scenario_service = Mock()
        mock_scenario_service.get_scenario.return_value = sample_scenario
        mock_get_scenario_service.return_value = mock_scenario_service

        mock_exp_repo = Mock()
        mock_exp_repo.get = AsyncMock(return_value=sample_experiment)
        mock_persistence_manager.experiments.return_value = mock_exp_repo

        mock_agent_repo = Mock()
        mock_agent_repo.get = AsyncMock(return_value=None)  # Agent not found
        mock_persistence_manager.agents.return_value = mock_agent_repo

        with patch(
            "fba_bench_api.api.routes.experiments.get_pm",
            return_value=mock_persistence_manager,
        ):
            response = client.post(
                "/api/v1/experiments/exp-123/start", json=sample_run_create.model_dump()
            )

        assert response.status_code == 404
        assert "Agent" in response.json()["detail"]

    def test_get_experiment_status_success(
        self, client, mock_persistence_manager, sample_experiment
    ):
        """Test successful experiment status retrieval."""
        # Create a mock active run
        active_run = ExperimentRun(
            id="run-123",
            experiment_id="exp-123",
            scenario_id="tier_0_baseline",
            participants=[],
            status="running",
            current_tick=25,
            total_ticks=100,
            progress_percent=25.0,
            started_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        mock_exp_repo = Mock()
        mock_exp_repo.get = AsyncMock(return_value=sample_experiment)
        mock_persistence_manager.experiments.return_value = mock_exp_repo

        with patch(
            "fba_bench_api.api.routes.experiments.get_pm",
            return_value=mock_persistence_manager,
        ):
            with patch(
                "fba_bench_api.api.routes.experiments._experiment_runs",
                {"run-123": active_run},
            ):
                response = client.get("/api/v1/experiments/exp-123/status")

        assert response.status_code == 200
        data = response.json()
        assert data["experiment_id"] == "exp-123"
        assert data["run_id"] == "run-123"
        assert data["status"] == "running"
        assert data["progress_percent"] == 25.0
        assert data["current_tick"] == 25
        assert data["total_ticks"] == 100

    def test_get_experiment_status_experiment_not_found(
        self, client, mock_persistence_manager
    ):
        """Test experiment status when experiment not found."""
        mock_exp_repo = Mock()
        mock_exp_repo.get = AsyncMock(return_value=None)
        mock_persistence_manager.experiments.return_value = mock_exp_repo

        with patch(
            "fba_bench_api.api.routes.experiments.get_pm",
            return_value=mock_persistence_manager,
        ):
            response = client.get("/api/v1/experiments/nonexistent/status")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_experiment_status_no_runs(
        self, client, mock_persistence_manager, sample_experiment
    ):
        """Test experiment status when no runs exist."""
        mock_exp_repo = Mock()
        mock_exp_repo.get = AsyncMock(return_value=sample_experiment)
        mock_persistence_manager.experiments.return_value = mock_exp_repo

        with patch(
            "fba_bench_api.api.routes.experiments.get_pm",
            return_value=mock_persistence_manager,
        ):
            with patch("fba_bench_api.api.routes.experiments._experiment_runs", {}):
                response = client.get("/api/v1/experiments/exp-123/status")

        assert response.status_code == 404
        assert "No runs found" in response.json()["detail"]

    def test_get_experiment_progress_success(
        self, client, mock_persistence_manager, sample_experiment
    ):
        """Test successful experiment progress retrieval."""
        active_run = ExperimentRun(
            id="run-123",
            experiment_id="exp-123",
            scenario_id="tier_0_baseline",
            participants=[
                ExperimentParticipant(
                    agent_id="agent-456", role="primary", config_override={}
                )
            ],
            status="running",
            current_tick=30,
            total_ticks=100,
            progress_percent=30.0,
            started_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            metrics={"revenue": 1500.0},
        )

        mock_exp_repo = Mock()
        mock_exp_repo.get = AsyncMock(return_value=sample_experiment)
        mock_persistence_manager.experiments.return_value = mock_exp_repo

        with patch(
            "fba_bench_api.api.routes.experiments.get_pm",
            return_value=mock_persistence_manager,
        ):
            with patch(
                "fba_bench_api.api.routes.experiments._experiment_runs",
                {"run-123": active_run},
            ):
                response = client.get("/api/v1/experiments/exp-123/progress")

        assert response.status_code == 200
        data = response.json()
        assert data["experiment_id"] == "exp-123"
        assert data["run_id"] == "run-123"
        assert data["current_tick"] == 30
        assert data["total_ticks"] == 100
        assert data["progress_percent"] == 30.0
        assert data["elapsed_time_seconds"] >= 0
        assert len(data["participant_status"]) == 1
        assert data["participant_status"][0]["agent_id"] == "agent-456"

    def test_get_experiment_progress_no_active_run(
        self, client, mock_persistence_manager, sample_experiment
    ):
        """Test experiment progress when no active run exists."""
        mock_exp_repo = Mock()
        mock_exp_repo.get = AsyncMock(return_value=sample_experiment)
        mock_persistence_manager.experiments.return_value = mock_exp_repo

        with patch(
            "fba_bench_api.api.routes.experiments.get_pm",
            return_value=mock_persistence_manager,
        ):
            with patch("fba_bench_api.api.routes.experiments._experiment_runs", {}):
                response = client.get("/api/v1/experiments/exp-123/progress")

        assert response.status_code == 404
        assert "No active run found" in response.json()["detail"]

    @patch("fba_bench_api.api.routes.experiments._stop_experiment_run")
    def test_stop_experiment_run_success(
        self, mock_stop_run, client, mock_persistence_manager, sample_experiment
    ):
        """Test successful experiment run stop."""
        active_run = ExperimentRun(
            id="run-123",
            experiment_id="exp-123",
            scenario_id="tier_0_baseline",
            participants=[],
            status="running",
            current_tick=50,
            total_ticks=100,
            progress_percent=50.0,
            started_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Mock the stop function to update the run status
        def stop_side_effect(run):
            run.status = "stopped"
            run.completed_at = datetime.now(timezone.utc)
            run.updated_at = datetime.now(timezone.utc)

        mock_stop_run.side_effect = stop_side_effect

        mock_exp_repo = Mock()
        mock_exp_repo.get = AsyncMock(return_value=sample_experiment)
        mock_exp_repo.update = AsyncMock(return_value=sample_experiment)
        mock_persistence_manager.experiments.return_value = mock_exp_repo

        with patch(
            "fba_bench_api.api.routes.experiments.get_pm",
            return_value=mock_persistence_manager,
        ):
            with patch(
                "fba_bench_api.api.routes.experiments._experiment_runs",
                {"run-123": active_run},
            ):
                response = client.post("/api/v1/experiments/exp-123/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["experiment_id"] == "exp-123"
        assert data["run_id"] == "run-123"
        assert data["status"] == "stopped"
        mock_stop_run.assert_called_once_with(active_run)

    def test_stop_experiment_run_no_running_experiment(
        self, client, mock_persistence_manager, sample_experiment
    ):
        """Test stopping experiment when no running experiment exists."""
        mock_exp_repo = Mock()
        mock_exp_repo.get = AsyncMock(return_value=sample_experiment)
        mock_persistence_manager.experiments.return_value = mock_exp_repo

        with patch(
            "fba_bench_api.api.routes.experiments.get_pm",
            return_value=mock_persistence_manager,
        ):
            with patch("fba_bench_api.api.routes.experiments._experiment_runs", {}):
                response = client.post("/api/v1/experiments/exp-123/stop")

        assert response.status_code == 400
        assert "No running experiment found" in response.json()["detail"]


class TestExperimentRunHelpers:
    """Test experiment run helper functions."""

    @patch("fba_bench_api.api.routes.experiments.get_redis")
    @pytest.mark.asyncio
    async def test_publish_experiment_event_success(self, mock_get_redis):
        """Test successful event publishing."""
        from fba_bench_api.api.routes.experiments import _publish_experiment_event

        mock_redis = Mock()
        mock_redis.publish = AsyncMock()
        mock_get_redis.return_value = mock_redis

        await _publish_experiment_event("exp-123", "status", {"status": "running"})

        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == "experiments:exp-123:status"

        import json

        event_data = json.loads(call_args[0][1])
        assert event_data["experiment_id"] == "exp-123"
        assert event_data["event_type"] == "status"
        assert event_data["data"]["status"] == "running"

    @patch("fba_bench_api.api.routes.experiments.get_redis")
    @pytest.mark.asyncio
    async def test_publish_experiment_event_redis_error(self, mock_get_redis):
        """Test event publishing with Redis error."""
        from fba_bench_api.api.routes.experiments import _publish_experiment_event

        mock_get_redis.side_effect = Exception("Redis connection failed")

        # Should not raise exception, just log warning
        await _publish_experiment_event("exp-123", "status", {"status": "running"})

    def test_validate_run_transition_valid(self):
        """Test valid run status transitions."""
        from fba_bench_api.api.routes.experiments import _validate_run_transition

        # Valid transitions should not raise
        _validate_run_transition("pending", "starting")
        _validate_run_transition("starting", "running")
        _validate_run_transition("running", "completed")
        _validate_run_transition("running", "failed")
        _validate_run_transition("running", "stopped")

    def test_validate_run_transition_invalid(self):
        """Test invalid run status transitions."""
        from fba_bench_api.api.routes.experiments import _validate_run_transition

        with pytest.raises(Exception):  # HTTPException
            _validate_run_transition("completed", "running")

        with pytest.raises(Exception):  # HTTPException
            _validate_run_transition("failed", "running")

        with pytest.raises(Exception):  # HTTPException
            _validate_run_transition("stopped", "running")

    @patch("fba_bench_api.api.routes.experiments._publish_experiment_event")
    @pytest.mark.asyncio
    async def test_start_experiment_run_success(self, mock_publish):
        """Test successful experiment run start."""
        from fba_bench_api.api.routes.experiments import _start_experiment_run

        run = ExperimentRun(
            id="run-123",
            experiment_id="exp-456",
            scenario_id="tier_0_baseline",
            participants=[],
            status="pending",
        )

        await _start_experiment_run(run)

        assert run.status == "running"
        assert run.started_at is not None
        assert run.current_tick == 0
        assert run.total_ticks == 100
        assert run.progress_percent == 0.0

        # Should have published two events: starting and running
        assert mock_publish.call_count == 2

    @patch("fba_bench_api.api.routes.experiments._publish_experiment_event")
    @pytest.mark.asyncio
    async def test_start_experiment_run_failure(self, mock_publish):
        """Test experiment run start with failure."""
        from fba_bench_api.api.routes.experiments import _start_experiment_run

        run = ExperimentRun(
            id="run-123",
            experiment_id="exp-456",
            scenario_id="tier_0_baseline",
            participants=[],
            status="pending",
        )

        # Mock publish to raise exception during starting phase
        mock_publish.side_effect = [None, Exception("Orchestrator failed")]

        with pytest.raises(Exception):
            await _start_experiment_run(run)

        assert run.status == "failed"
        assert run.error_message is not None

    @patch("fba_bench_api.api.routes.experiments._publish_experiment_event")
    @pytest.mark.asyncio
    async def test_stop_experiment_run_success(self, mock_publish):
        """Test successful experiment run stop."""
        from fba_bench_api.api.routes.experiments import _stop_experiment_run

        run = ExperimentRun(
            id="run-123",
            experiment_id="exp-456",
            scenario_id="tier_0_baseline",
            participants=[],
            status="running",
            started_at=datetime.now(timezone.utc),
        )

        await _stop_experiment_run(run)

        assert run.status == "stopped"
        assert run.completed_at is not None
        mock_publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_experiment_run_wrong_status(self):
        """Test stopping experiment run with wrong status."""
        from fba_bench_api.api.routes.experiments import _stop_experiment_run

        run = ExperimentRun(
            id="run-123",
            experiment_id="exp-456",
            scenario_id="tier_0_baseline",
            participants=[],
            status="completed",  # Cannot stop completed run
        )

        with pytest.raises(Exception):  # HTTPException
            await _stop_experiment_run(run)


class TestExperimentRunIntegration:
    """Integration tests for experiment runs."""

    @patch("fba_bench_api.api.routes.experiments.get_scenario_service")
    @patch("fba_bench_api.api.routes.experiments._start_experiment_run")
    @patch("fba_bench_api.api.routes.experiments.get_redis")
    def test_full_experiment_run_lifecycle(
        self,
        mock_get_redis,
        mock_start_run,
        mock_get_scenario_service,
        client,
        mock_persistence_manager,
        sample_experiment,
        sample_agent,
        sample_scenario,
        sample_run_create,
    ):
        """Test complete experiment run lifecycle: start -> status -> progress -> stop."""
        # Setup mocks
        mock_scenario_service = Mock()
        mock_scenario_service.get_scenario.return_value = sample_scenario
        mock_get_scenario_service.return_value = mock_scenario_service

        mock_exp_repo = Mock()
        mock_exp_repo.get = AsyncMock(return_value=sample_experiment)
        mock_exp_repo.update = AsyncMock(return_value=sample_experiment)
        mock_persistence_manager.experiments.return_value = mock_exp_repo

        mock_agent_repo = Mock()
        mock_agent_repo.get = AsyncMock(return_value=sample_agent)
        mock_persistence_manager.agents.return_value = mock_agent_repo

        mock_redis = Mock()
        mock_redis.publish = AsyncMock()
        mock_get_redis.return_value = mock_redis

        with patch(
            "fba_bench_api.api.routes.experiments.get_pm",
            return_value=mock_persistence_manager,
        ):
            # 1. Start experiment
            response = client.post(
                "/api/v1/experiments/exp-123/start", json=sample_run_create.model_dump()
            )
            assert response.status_code == 202
            run_id = response.json()["run_id"]

            # Simulate the run being started
            active_run = ExperimentRun(
                id=run_id,
                experiment_id="exp-123",
                scenario_id="tier_0_baseline",
                participants=sample_run_create.participants,
                status="running",
                current_tick=15,
                total_ticks=30,
                progress_percent=50.0,
                started_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                metrics={"revenue": 750.0},
            )

            with patch(
                "fba_bench_api.api.routes.experiments._experiment_runs",
                {run_id: active_run},
            ):
                # 2. Check status
                response = client.get("/api/v1/experiments/exp-123/status")
                assert response.status_code == 200
                assert response.json()["status"] == "running"
                assert response.json()["progress_percent"] == 50.0

                # 3. Check progress
                response = client.get("/api/v1/experiments/exp-123/progress")
                assert response.status_code == 200
                progress_data = response.json()
                assert progress_data["current_tick"] == 15
                assert progress_data["total_ticks"] == 30
                assert len(progress_data["participant_status"]) == 1

                # 4. Stop experiment
                with patch(
                    "fba_bench_api.api.routes.experiments._stop_experiment_run"
                ) as mock_stop:

                    def stop_side_effect(run):
                        run.status = "stopped"
                        run.completed_at = datetime.now(timezone.utc)

                    mock_stop.side_effect = stop_side_effect

                    response = client.post("/api/v1/experiments/exp-123/stop")
                    assert response.status_code == 200
                    assert response.json()["status"] == "stopped"
