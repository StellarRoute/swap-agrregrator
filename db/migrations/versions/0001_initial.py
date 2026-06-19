# Initial schema: pool/signal snapshot history tables and the agent run audit log.
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pool_snapshots",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("pool_id", sa.String, nullable=False),
        sa.Column("reserve_a", sa.Float, nullable=False),
        sa.Column("reserve_b", sa.Float, nullable=False),
        sa.Column("volume_24h", sa.Float, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_pool_snapshots_pool_id", "pool_snapshots", ["pool_id"])
    op.create_index("ix_pool_snapshots_created_at", "pool_snapshots", ["created_at"])

    op.create_table(
        "signal_snapshots",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("asset", sa.String, nullable=False),
        sa.Column("velocity_score", sa.Float, nullable=False),
        sa.Column("sentiment_score", sa.Float, nullable=False),
        sa.Column("stale", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_signal_snapshots_asset", "signal_snapshots", ["asset"])
    op.create_index("ix_signal_snapshots_created_at", "signal_snapshots", ["created_at"])

    op.create_table(
        "agent_run_log",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("run_id", sa.String, nullable=False),
        sa.Column("path_id", sa.String, nullable=False),
        sa.Column("risk_score", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("risk_inputs", sa.JSON, nullable=False),
        sa.Column("decision_action", sa.String, nullable=False),
        sa.Column("decision_reason", sa.String, nullable=False),
        sa.Column("proposed_delta", sa.Float, nullable=False),
        sa.Column("target_pool_id", sa.String, nullable=True),
        sa.Column("execution_success", sa.Boolean, nullable=False),
        sa.Column("execution_detail", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agent_run_log_run_id", "agent_run_log", ["run_id"])
    op.create_index("ix_agent_run_log_path_id", "agent_run_log", ["path_id"])
    op.create_index("ix_agent_run_log_created_at", "agent_run_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("agent_run_log")
    op.drop_table("signal_snapshots")
    op.drop_table("pool_snapshots")
