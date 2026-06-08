"""Add lawn assessments and unified lawn program tables.

Revision ID: 005
Revises: 004
Create Date: 2025-06-05
"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lawn_assessment",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("zone_id", sa.Integer, sa.ForeignKey("lawn_zone.id", ondelete="SET NULL"), nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("overall_condition", sa.String(20)),
        sa.Column("grass_coverage_pct", sa.Integer),
        sa.Column("notes", sa.Text),
        sa.Column("ai_analyzed", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "assessment_finding",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("assessment_id", sa.Integer, sa.ForeignKey("lawn_assessment.id", ondelete="CASCADE"), nullable=False),
        sa.Column("finding_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20)),
        sa.Column("coverage_pct", sa.Integer),
        sa.Column("location_notes", sa.String(300)),
        sa.Column("photo_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_assessment_finding_assessment_id", "assessment_finding", ["assessment_id"])

    op.create_table(
        "remediation_plan",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("assessment_id", sa.Integer, sa.ForeignKey("lawn_assessment.id", ondelete="CASCADE"), nullable=False),
        sa.Column("findings_summary", sa.Text),
        sa.Column("action_steps", sa.JSON),
        sa.Column("key_warnings", sa.JSON),
        sa.Column("expected_outcomes", sa.JSON),
        sa.Column("seasonal_context", sa.Text),
        sa.Column("ai_provider", sa.String(20)),
        sa.Column("ai_model", sa.String(100)),
        sa.Column("raw_response", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_remediation_plan_assessment_id", "remediation_plan", ["assessment_id"])

    op.create_table(
        "lawn_program",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("season_year", sa.Integer),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "lawn_program_step",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("program_id", sa.Integer, sa.ForeignKey("lawn_program.id", ondelete="CASCADE"), nullable=False),
        sa.Column("month", sa.Integer),
        sa.Column("week_of_month", sa.Integer),
        sa.Column("activity_type", sa.String(50)),
        sa.Column("product_name", sa.String(300)),
        sa.Column("application_rate", sa.String(200)),
        sa.Column("notes", sa.Text),
        sa.Column("priority", sa.String(20), server_default="medium"),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("source", sa.String(20)),
        sa.Column("source_ref_id", sa.Integer),
        sa.Column("conflicts_with", sa.JSON),
        sa.Column("order_index", sa.Integer, server_default="0"),
        sa.Column("completed_date", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_lawn_program_step_program_id", "lawn_program_step", ["program_id"])


def downgrade():
    op.drop_table("lawn_program_step")
    op.drop_table("lawn_program")
    op.drop_table("remediation_plan")
    op.drop_table("assessment_finding")
    op.drop_table("lawn_assessment")
