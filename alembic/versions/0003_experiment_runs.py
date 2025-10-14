"""experiment runs

Revision ID: 0003_experiment_runs
Revises: 0002_models_baseline
Create Date: 2025-09-20 22:17:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_experiment_runs"
down_revision = "0002_models_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # experiment_runs table
    op.create_table(
        "experiment_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "experiment_id",
            sa.String(length=36),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("scenario_id", sa.String(length=255), nullable=False, index=True),
        sa.Column("params", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "starting",
                "running",
                "completed",
                "failed",
                "stopped",
                name="experiment_run_status_enum",
                native_enum=False,
                validate_strings=True,
            ),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        # Progress tracking
        sa.Column("current_tick", sa.Integer(), nullable=True),
        sa.Column("total_ticks", sa.Integer(), nullable=True),
        sa.Column("progress_percent", sa.Float(), nullable=True),
        # Timing
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        # Results and error handling
        sa.Column("metrics", sa.Text(), nullable=True),
        sa.Column("results", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    # experiment_run_participants table - stores agent participants for each run
    op.create_table(
        "experiment_run_participants",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(length=36),
            sa.ForeignKey("experiment_runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "agent_id",
            sa.String(length=36),
            sa.ForeignKey("agents.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("config_override", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        # Unique constraint to prevent duplicate participants in same run
        sa.UniqueConstraint("run_id", "agent_id", name="uq_run_agent"),
    )


def downgrade() -> None:
    # drop experiment_run_participants
    op.drop_table("experiment_run_participants")

    # drop experiment_runs
    op.drop_table("experiment_runs")
    op.execute("DROP TYPE IF EXISTS experiment_run_status_enum")
