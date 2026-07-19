"""create tool calls

Revision ID: 0003_create_tool_calls
Revises: 0002_create_workflow_runs
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_create_tool_calls"
down_revision = "0002_create_workflow_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tool_calls",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("workflow_run_id", sa.Uuid(), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tool_calls_task_id", "tool_calls", ["task_id"], unique=False)
    op.create_index(
        "ix_tool_calls_workflow_run_id", "tool_calls", ["workflow_run_id"], unique=False
    )
