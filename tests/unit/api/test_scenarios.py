"""Unit tests for scenarios API endpoints."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from fba_bench_api.models.scenarios import Scenario, ScenarioList, ScenarioService
from fba_bench_api.server.app_factory import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_scenario_service():
    """Mock scenario service."""
    return Mock(spec=ScenarioService)


@pytest.fixture
def sample_scenario():
    """Sample scenario for testing."""
    return Scenario(
        id="tier_0_baseline",
        name="Tier 0 Baseline",
        description="Basic scenario for beginners",
        difficulty_tier=0,
        expected_duration=30,
        tags=["tier_0", "baseline"],
        default_params={"initial_capital": 20000},
        success_criteria={"profit_target": 1000.0},
        market_conditions={"economic_cycles": "stable"},
        external_events=[],
        agent_constraints={"initial_capital": 20000.0},
    )


@pytest.fixture
def sample_scenario_list(sample_scenario):
    """Sample scenario list for testing."""
    return ScenarioList(
        scenarios=[sample_scenario], total=1, page=1, page_size=20, total_pages=1
    )


class TestScenariosAPI:
    """Test scenarios API endpoints."""

    @patch("fba_bench_api.api.routes.scenarios.get_scenario_service")
    def test_list_scenarios_success(
        self, mock_get_service, client, mock_scenario_service, sample_scenario_list
    ):
        """Test successful scenario listing."""
        mock_get_service.return_value = mock_scenario_service
        mock_scenario_service.list_scenarios.return_value = sample_scenario_list

        response = client.get("/api/v1/scenarios")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["scenarios"]) == 1
        assert data["scenarios"][0]["id"] == "tier_0_baseline"
        mock_scenario_service.list_scenarios.assert_called_once_with(
            page=1, page_size=20, tags=None, difficulty_tier=None
        )

    @patch("fba_bench_api.api.routes.scenarios.get_scenario_service")
    def test_list_scenarios_with_filters(
        self, mock_get_service, client, mock_scenario_service, sample_scenario_list
    ):
        """Test scenario listing with filters."""
        mock_get_service.return_value = mock_scenario_service
        mock_scenario_service.list_scenarios.return_value = sample_scenario_list

        response = client.get(
            "/api/v1/scenarios?difficulty_tier=0&tags=baseline&page=2&page_size=10"
        )

        assert response.status_code == 200
        mock_scenario_service.list_scenarios.assert_called_once_with(
            page=2, page_size=10, tags=["baseline"], difficulty_tier=0
        )

    @patch("fba_bench_api.api.routes.scenarios.get_scenario_service")
    def test_list_scenarios_service_error(
        self, mock_get_service, client, mock_scenario_service
    ):
        """Test scenario listing with service error."""
        mock_get_service.return_value = mock_scenario_service
        mock_scenario_service.list_scenarios.side_effect = Exception("Service error")

        response = client.get("/api/v1/scenarios")

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to retrieve scenarios"

    @patch("fba_bench_api.api.routes.scenarios.get_scenario_service")
    def test_get_scenario_success(
        self, mock_get_service, client, mock_scenario_service, sample_scenario
    ):
        """Test successful scenario retrieval."""
        mock_get_service.return_value = mock_scenario_service
        mock_scenario_service.get_scenario.return_value = sample_scenario

        response = client.get("/api/v1/scenarios/tier_0_baseline")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "tier_0_baseline"
        assert data["name"] == "Tier 0 Baseline"
        assert data["difficulty_tier"] == 0
        assert data["expected_duration"] == 30
        mock_scenario_service.get_scenario.assert_called_once_with("tier_0_baseline")

    @patch("fba_bench_api.api.routes.scenarios.get_scenario_service")
    def test_get_scenario_not_found(
        self, mock_get_service, client, mock_scenario_service
    ):
        """Test scenario retrieval when scenario not found."""
        mock_get_service.return_value = mock_scenario_service
        mock_scenario_service.get_scenario.return_value = None

        response = client.get("/api/v1/scenarios/nonexistent")

        assert response.status_code == 404
        assert response.json()["detail"] == "Scenario 'nonexistent' not found"

    @patch("fba_bench_api.api.routes.scenarios.get_scenario_service")
    def test_get_scenario_service_error(
        self, mock_get_service, client, mock_scenario_service
    ):
        """Test scenario retrieval with service error."""
        mock_get_service.return_value = mock_scenario_service
        mock_scenario_service.get_scenario.side_effect = Exception("Service error")

        response = client.get("/api/v1/scenarios/tier_0_baseline")

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to retrieve scenario"

    @patch("fba_bench_api.api.routes.scenarios.get_scenario_service")
    def test_validate_scenario_success(
        self, mock_get_service, client, mock_scenario_service, sample_scenario
    ):
        """Test successful scenario validation."""
        mock_get_service.return_value = mock_scenario_service
        mock_scenario_service.get_scenario.return_value = sample_scenario
        mock_scenario_service.validate_scenario.return_value = True

        response = client.get("/api/v1/scenarios/tier_0_baseline/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["scenario_id"] == "tier_0_baseline"
        assert data["valid"] is True
        assert data["message"] == "Scenario validation passed"
        mock_scenario_service.validate_scenario.assert_called_once_with(
            "tier_0_baseline"
        )

    @patch("fba_bench_api.api.routes.scenarios.get_scenario_service")
    def test_validate_scenario_failed(
        self, mock_get_service, client, mock_scenario_service, sample_scenario
    ):
        """Test scenario validation failure."""
        mock_get_service.return_value = mock_scenario_service
        mock_scenario_service.get_scenario.return_value = sample_scenario
        mock_scenario_service.validate_scenario.return_value = False

        response = client.get("/api/v1/scenarios/tier_0_baseline/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["scenario_id"] == "tier_0_baseline"
        assert data["valid"] is False
        assert data["message"] == "Scenario validation failed"

    @patch("fba_bench_api.api.routes.scenarios.get_scenario_service")
    def test_validate_scenario_not_found(
        self, mock_get_service, client, mock_scenario_service
    ):
        """Test scenario validation when scenario not found."""
        mock_get_service.return_value = mock_scenario_service
        mock_scenario_service.get_scenario.return_value = None

        response = client.get("/api/v1/scenarios/nonexistent/validate")

        assert response.status_code == 404
        assert response.json()["detail"] == "Scenario 'nonexistent' not found"


class TestScenarioService:
    """Test ScenarioService functionality."""

    def test_scenario_service_initialization(self):
        """Test scenario service initialization."""
        service = ScenarioService()
        assert service.scenarios_dir == "src/scenarios"
        assert service._scenario_cache is None
        assert service._cache_timestamp is None

    def test_scenario_service_custom_dir(self):
        """Test scenario service with custom directory."""
        service = ScenarioService("/custom/path")
        assert service.scenarios_dir == "/custom/path"

    @patch("fba_bench_api.models.scenarios.glob.glob")
    def test_get_scenario_files(self, mock_glob):
        """Test getting scenario files."""
        mock_glob.return_value = [
            "src/scenarios/tier_0_baseline.yaml",
            "src/scenarios/business_types/boom_and_bust_cycle.yaml",
        ]

        service = ScenarioService()
        files = service._get_scenario_files()

        assert len(files) == 2
        assert "src/scenarios/tier_0_baseline.yaml" in files
        assert "src/scenarios/business_types/boom_and_bust_cycle.yaml" in files

    @patch("builtins.open")
    @patch("fba_bench_api.models.scenarios.yaml.safe_load")
    def test_load_scenario_from_file(self, mock_yaml_load, mock_open):
        """Test loading scenario from YAML file."""
        mock_yaml_data = {
            "scenario_name": "Test Scenario",
            "difficulty_tier": 1,
            "expected_duration": 50,
            "success_criteria": {"profit_target": 2000},
            "market_conditions": {"economic_cycles": "stable"},
            "external_events": [],
            "agent_constraints": {"initial_capital": 15000},
        }
        mock_yaml_load.return_value = mock_yaml_data

        service = ScenarioService()
        scenario = service._load_scenario_from_file("test_scenario.yaml")

        assert scenario is not None
        assert scenario.id == "test_scenario"
        assert scenario.name == "Test Scenario"
        assert scenario.difficulty_tier == 1
        assert scenario.expected_duration == 50

    @patch("builtins.open")
    @patch("fba_bench_api.models.scenarios.yaml.safe_load")
    def test_load_scenario_string_difficulty_tier(self, mock_yaml_load, mock_open):
        """Test loading scenario with string difficulty tier."""
        mock_yaml_data = {
            "scenario_name": "Test Scenario",
            "difficulty_tier": "moderate",  # String instead of int
            "expected_duration": 50,
            "success_criteria": {"profit_target": 2000},
            "market_conditions": {"economic_cycles": "stable"},
            "external_events": [],
            "agent_constraints": {"initial_capital": 15000},
        }
        mock_yaml_load.return_value = mock_yaml_data

        service = ScenarioService()
        scenario = service._load_scenario_from_file("test_scenario.yaml")

        assert scenario is not None
        assert scenario.difficulty_tier == 1  # "moderate" -> 1

    @patch("builtins.open")
    def test_load_scenario_file_error(self, mock_open):
        """Test handling of file loading errors."""
        mock_open.side_effect = FileNotFoundError("File not found")

        service = ScenarioService()
        scenario = service._load_scenario_from_file("nonexistent.yaml")

        assert scenario is None

    def test_should_refresh_cache(self):
        """Test cache refresh logic."""
        service = ScenarioService()

        # Should refresh when cache is None
        assert service._should_refresh_cache() is True

        # Mock cache timestamp
        from datetime import datetime, timezone

        service._scenario_cache = {}
        service._cache_timestamp = datetime.now(timezone.utc)

        # Should not refresh immediately
        assert service._should_refresh_cache() is False

    @patch.object(ScenarioService, "_get_scenario_files")
    @patch.object(ScenarioService, "_load_scenario_from_file")
    def test_refresh_scenarios(self, mock_load_file, mock_get_files, sample_scenario):
        """Test refreshing scenarios cache."""
        mock_get_files.return_value = ["tier_0_baseline.yaml"]
        mock_load_file.return_value = sample_scenario

        service = ScenarioService()
        service._refresh_scenarios()

        assert service._scenario_cache is not None
        assert "tier_0_baseline" in service._scenario_cache
        assert service._cache_timestamp is not None

    @patch.object(ScenarioService, "_should_refresh_cache")
    @patch.object(ScenarioService, "_refresh_scenarios")
    def test_list_scenarios_with_cache_refresh(
        self, mock_refresh, mock_should_refresh, sample_scenario
    ):
        """Test listing scenarios with cache refresh."""
        mock_should_refresh.return_value = True

        service = ScenarioService()
        service._scenario_cache = {"tier_0_baseline": sample_scenario}

        result = service.list_scenarios()

        mock_refresh.assert_called_once()
        assert len(result.scenarios) == 1

    def test_list_scenarios_filtering(self, sample_scenario):
        """Test scenario filtering functionality."""
        # Create scenarios with different properties
        scenario2 = Scenario(
            id="tier_1_moderate",
            name="Tier 1 Moderate",
            description="Moderate difficulty",
            difficulty_tier=1,
            expected_duration=60,
            tags=["tier_1", "moderate"],
            default_params={},
            success_criteria={},
            market_conditions={},
            external_events=[],
            agent_constraints={},
        )

        service = ScenarioService()
        service._scenario_cache = {
            "tier_0_baseline": sample_scenario,
            "tier_1_moderate": scenario2,
        }
        service._cache_timestamp = sample_scenario.created_at

        # Test filtering by difficulty tier
        result = service.list_scenarios(difficulty_tier=0)
        assert len(result.scenarios) == 1
        assert result.scenarios[0].id == "tier_0_baseline"

        # Test filtering by tags
        result = service.list_scenarios(tags=["moderate"])
        assert len(result.scenarios) == 1
        assert result.scenarios[0].id == "tier_1_moderate"

    def test_list_scenarios_pagination(self, sample_scenario):
        """Test scenario pagination."""
        # Create multiple scenarios
        scenarios = {}
        for i in range(25):
            scenario = Scenario(
                id=f"scenario_{i}",
                name=f"Scenario {i}",
                description=f"Test scenario {i}",
                difficulty_tier=i % 4,
                expected_duration=30,
                tags=[f"tier_{i % 4}"],
                default_params={},
                success_criteria={},
                market_conditions={},
                external_events=[],
                agent_constraints={},
            )
            scenarios[f"scenario_{i}"] = scenario

        service = ScenarioService()
        service._scenario_cache = scenarios
        service._cache_timestamp = sample_scenario.created_at

        # Test first page
        result = service.list_scenarios(page=1, page_size=10)
        assert len(result.scenarios) == 10
        assert result.total == 25
        assert result.page == 1
        assert result.total_pages == 3

        # Test last page
        result = service.list_scenarios(page=3, page_size=10)
        assert len(result.scenarios) == 5
        assert result.page == 3

    @patch.object(ScenarioService, "_should_refresh_cache")
    def test_get_scenario(self, mock_should_refresh, sample_scenario):
        """Test getting specific scenario."""
        mock_should_refresh.return_value = False

        service = ScenarioService()
        service._scenario_cache = {"tier_0_baseline": sample_scenario}

        result = service.get_scenario("tier_0_baseline")
        assert result == sample_scenario

        result = service.get_scenario("nonexistent")
        assert result is None

    @patch("scenarios.scenario_framework.ScenarioFramework")
    def test_validate_scenario(self, mock_framework_class, sample_scenario):
        """Test scenario validation."""
        mock_framework = Mock()
        mock_framework.validate_scenario_consistency.return_value = True
        mock_framework_class.return_value = mock_framework

        service = ScenarioService()
        service._scenario_cache = {"tier_0_baseline": sample_scenario}
        service._cache_timestamp = sample_scenario.created_at

        result = service.validate_scenario("tier_0_baseline")
        assert result is True

        mock_framework_class.assert_called_once()
        mock_framework.validate_scenario_consistency.assert_called_once()

    @patch("scenarios.scenario_framework.ScenarioFramework")
    def test_validate_scenario_not_found(self, mock_framework_class):
        """Test scenario validation when scenario not found."""
        service = ScenarioService()
        service._scenario_cache = {}
        service._cache_timestamp = (
            sample_scenario.created_at if "sample_scenario" in locals() else None
        )

        result = service.validate_scenario("nonexistent")
        assert result is False

        mock_framework_class.assert_not_called()

    @patch("scenarios.scenario_framework.ScenarioFramework")
    def test_validate_scenario_validation_error(
        self, mock_framework_class, sample_scenario
    ):
        """Test scenario validation with framework error."""
        mock_framework_class.side_effect = Exception("Validation error")

        service = ScenarioService()
        service._scenario_cache = {"tier_0_baseline": sample_scenario}
        service._cache_timestamp = sample_scenario.created_at

        result = service.validate_scenario("tier_0_baseline")
        assert result is False


class TestScenarioModel:
    """Test Scenario model validation."""

    def test_scenario_model_validation(self):
        """Test scenario model field validation."""
        scenario = Scenario(
            id="test",
            name="Test Scenario",
            difficulty_tier=2,
            expected_duration=100,
            success_criteria={"profit": 5000},
        )

        assert scenario.id == "test"
        assert scenario.name == "Test Scenario"
        assert scenario.difficulty_tier == 2
        assert scenario.expected_duration == 100
        assert scenario.tags == []
        assert scenario.default_params == {}

    def test_scenario_model_invalid_difficulty_tier(self):
        """Test scenario model with invalid difficulty tier."""
        with pytest.raises(ValueError):
            Scenario(
                id="test",
                name="Test Scenario",
                difficulty_tier=5,  # Invalid: must be 0-3
                expected_duration=100,
            )

    def test_scenario_model_invalid_duration(self):
        """Test scenario model with invalid duration."""
        with pytest.raises(ValueError):
            Scenario(
                id="test",
                name="Test Scenario",
                difficulty_tier=1,
                expected_duration=0,  # Invalid: must be > 0
            )

    def test_scenario_model_empty_name(self):
        """Test scenario model with empty name."""
        with pytest.raises(ValueError):
            Scenario(
                id="test",
                name="",  # Invalid: must be non-empty
                difficulty_tier=1,
                expected_duration=100,
            )


class TestScenarioListModel:
    """Test ScenarioList model validation."""

    def test_scenario_list_model(self, sample_scenario):
        """Test scenario list model."""
        scenario_list = ScenarioList(
            scenarios=[sample_scenario], total=1, page=1, page_size=20, total_pages=1
        )

        assert len(scenario_list.scenarios) == 1
        assert scenario_list.total == 1
        assert scenario_list.page == 1
        assert scenario_list.page_size == 20
        assert scenario_list.total_pages == 1

    def test_scenario_list_invalid_page(self):
        """Test scenario list with invalid page number."""
        with pytest.raises(ValueError):
            ScenarioList(
                scenarios=[],
                total=0,
                page=0,  # Invalid: must be >= 1
                page_size=20,
                total_pages=1,
            )

    def test_scenario_list_invalid_page_size(self):
        """Test scenario list with invalid page size."""
        with pytest.raises(ValueError):
            ScenarioList(
                scenarios=[],
                total=0,
                page=1,
                page_size=101,  # Invalid: must be <= 100
                total_pages=1,
            )
