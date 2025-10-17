from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConfigTemplateSave(BaseModel):
    config_id: str
    template_name: str
    description: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ConfigTemplateResponse(BaseModel):
    template_name: str
    description: Optional[str]
    config_data: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(extra="forbid")


class BenchmarkConfigRequest(BaseModel):
    simulationSettings: Dict[str, Any]
    agentConfigs: List[Dict[str, Any]]
    llmSettings: Dict[str, Any]
    constraints: Dict[str, Any]
    experimentSettings: Dict[str, Any]

    model_config = ConfigDict(extra="forbid")


class BenchmarkConfigResponse(BaseModel):
    success: bool
    message: str
    config_id: str
    created_at: datetime

    model_config = ConfigDict(extra="forbid")


class ExperimentCreateRequest(BaseModel):
    experiment_name: str
    description: Optional[str] = None
    base_parameters: Dict[str, Any]
    parameter_sweep: Dict[str, List[Any]]
    output_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    parallel_workers: int = Field(1, ge=1)
    max_runs: Optional[int] = Field(None, ge=1)

    model_config = ConfigDict(extra="forbid")


class ExperimentStatusResponse(BaseModel):
    experiment_id: str
    status: str
    total_runs: int
    completed_runs: int
    successful_runs: int
    failed_runs: int
    progress_percentage: float
    start_time: datetime
    end_time: Optional[datetime] = None
    current_run_details: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ExperimentResultsResponse(BaseModel):
    experiment_id: str
    status: str
    results_summary: Dict[str, Any]
    individual_run_results: List[Dict[str, Any]]
    results_uri: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


# New models for experiment runs


class ExperimentParticipant(BaseModel):
    """Model representing an agent participant in an experiment run."""

    # Remove min_length to allow our custom validators to raise ValueError (as tests expect)
    agent_id: str = Field(..., description="Agent identifier")
    role: str = Field(..., description="Agent role in the experiment")
    config_override: Dict[str, Any] = Field(
        default_factory=dict, description="Configuration overrides for this participant"
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("agent_id", "role")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must be non-empty")
        return v.strip()


class ExperimentRunCreate(BaseModel):
    """Request model for creating and starting an experiment run."""

    # Remove min_length so our validators raise the expected ValueError messages
    scenario_id: str = Field(..., description="Scenario to execute")
    participants: List[ExperimentParticipant] = Field(
        ..., description="Agent participants in the experiment"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Override parameters for the scenario"
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("scenario_id")
    @classmethod
    def validate_scenario_id(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("scenario_id must be non-empty")
        return v.strip()

    @field_validator("participants")
    @classmethod
    def validate_participants(
        cls, v: List[ExperimentParticipant]
    ) -> List[ExperimentParticipant]:
        if not v:
            raise ValueError("At least one participant is required")

        # Validate unique agent IDs
        agent_ids = [p.agent_id for p in v]
        if len(agent_ids) != len(set(agent_ids)):
            raise ValueError("Agent IDs must be unique among participants")

        return v


RunStatusType = Literal[
    "pending", "starting", "running", "completed", "failed", "stopped"
]


class ExperimentRun(BaseModel):
    """Model representing a complete experiment run."""

    id: str = Field(..., description="Unique run identifier")
    experiment_id: str = Field(..., description="Parent experiment identifier")
    scenario_id: str = Field(..., description="Scenario being executed")
    participants: List[ExperimentParticipant] = Field(
        ..., description="Agent participants"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Scenario parameters"
    )
    status: RunStatusType = Field(default="pending", description="Current run status")

    # Progress tracking
    current_tick: Optional[int] = Field(
        None, ge=0, description="Current simulation tick"
    )
    total_ticks: Optional[int] = Field(None, ge=1, description="Total expected ticks")
    progress_percent: Optional[float] = Field(
        None, ge=0, le=100, description="Progress percentage"
    )

    # Timing
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = Field(None, description="When the run started")
    completed_at: Optional[datetime] = Field(None, description="When the run completed")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Results and metrics
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Runtime metrics")
    results: Optional[Dict[str, Any]] = Field(None, description="Final results")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    model_config = ConfigDict(extra="forbid")


class RunStatus(BaseModel):
    """Response model for experiment run status."""

    experiment_id: str
    run_id: str
    status: RunStatusType
    progress_percent: Optional[float] = Field(None, ge=0, le=100)
    current_tick: Optional[int] = Field(None, ge=0)
    total_ticks: Optional[int] = Field(None, ge=1)
    started_at: Optional[datetime]
    updated_at: datetime
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class RunProgress(BaseModel):
    """Response model for experiment run progress metrics."""

    experiment_id: str
    run_id: str
    current_tick: int = Field(ge=0)
    total_ticks: int = Field(ge=1)
    progress_percent: float = Field(ge=0, le=100)
    elapsed_time_seconds: float = Field(ge=0)
    estimated_remaining_seconds: Optional[float] = Field(None, ge=0)

    # Performance metrics
    ticks_per_second: Optional[float] = Field(None, ge=0)
    memory_usage_mb: Optional[float] = Field(None, ge=0)

    # Business metrics snapshot
    current_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Current business metrics snapshot"
    )

    # Participant status
    participant_status: List[Dict[str, Any]] = Field(
        default_factory=list, description="Status of each participant agent"
    )

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(extra="forbid")


class ExperimentRunResponse(BaseModel):
    """Response model for experiment run operations."""

    run_id: str
    experiment_id: str
    status: RunStatusType
    message: str
    created_at: datetime
    participants_count: int

    model_config = ConfigDict(extra="forbid")
