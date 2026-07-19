"""create workflow checkpoints

Revision ID: 0004_create_workflow_checkpoints
Revises: 0003_create_tool_calls
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_create_workflow_checkpoints"
down_revision = "0003_create_tool_calls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_checkpoints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_run_id", sa.Uuid(), nullable=False),
        sa.Column("current_node", sa.String(length=64), nullable=False),
        sa.Column("state_snapshot", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workflow_checkpoints_task_id", "workflow_checkpoints", ["task_id"])
    op.create_index(
        "ix_workflow_checkpoints_workflow_run_id", "workflow_checkpoints", ["workflow_run_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_workflow_checkpoints_workflow_run_id", table_name="workflow_checkpoints")
