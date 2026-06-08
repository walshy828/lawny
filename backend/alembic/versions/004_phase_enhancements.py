"""Phase enhancements: soil tests, observations, product catalog, AI consultations.

Revision ID: 004
Revises: 003
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    # ── lawn_config additions ────────────────────────────────
    op.add_column("lawn_config", sa.Column("ai_provider", sa.String(20), nullable=True, server_default="openai"))
    op.add_column("lawn_config", sa.Column("usda_zone", sa.String(20), nullable=True))

    # ── soil_test ────────────────────────────────────────────
    op.create_table(
        "soil_test",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=True),
        sa.Column("test_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lab_name", sa.String(200), nullable=True),
        sa.Column("ph", sa.Float(), nullable=True),
        sa.Column("buffer_ph", sa.Float(), nullable=True),
        sa.Column("nitrogen_ppm", sa.Float(), nullable=True),
        sa.Column("phosphorus_ppm", sa.Float(), nullable=True),
        sa.Column("potassium_ppm", sa.Float(), nullable=True),
        sa.Column("calcium_ppm", sa.Float(), nullable=True),
        sa.Column("magnesium_ppm", sa.Float(), nullable=True),
        sa.Column("sulfur_ppm", sa.Float(), nullable=True),
        sa.Column("organic_matter_pct", sa.Float(), nullable=True),
        sa.Column("cec", sa.Float(), nullable=True),
        sa.Column("lime_recommendation_lbs_per_1k", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["zone_id"], ["lawn_zone.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── observation ──────────────────────────────────────────
    op.create_table(
        "observation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("now()")),
        sa.Column("observation_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("coverage_pct", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=True, server_default="active"),
        sa.Column("resolved_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["zone_id"], ["lawn_zone.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── product_catalog ──────────────────────────────────────
    op.create_table(
        "product_catalog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("npk_ratio", sa.String(20), nullable=True),
        sa.Column("active_ingredient", sa.String(300), nullable=True),
        sa.Column("application_rate_per_1k", sa.String(100), nullable=True),
        sa.Column("coverage_sqft_per_bag", sa.Integer(), nullable=True),
        sa.Column("bag_size", sa.String(50), nullable=True),
        sa.Column("safe_grass_types", sa.JSON(), nullable=True),
        sa.Column("application_timing", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_builtin", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("is_custom", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── ai_consultation ──────────────────────────────────────
    op.create_table(
        "ai_consultation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("context_snapshot", sa.JSON(), nullable=True),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("structured_response", sa.JSON(), nullable=True),
        sa.Column("ai_provider", sa.String(20), nullable=True),
        sa.Column("ai_model", sa.String(50), nullable=True),
        sa.Column("observation_ids", sa.JSON(), nullable=True),
        sa.Column("zone_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["zone_id"], ["lawn_zone.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("ai_consultation")
    op.drop_table("product_catalog")
    op.drop_table("observation")
    op.drop_table("soil_test")
    op.drop_column("lawn_config", "usda_zone")
    op.drop_column("lawn_config", "ai_provider")
