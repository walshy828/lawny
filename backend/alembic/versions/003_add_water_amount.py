"""Add water_amount_inches to activity table.

Revision ID: 003
Revises: 002
Create Date: 2026-05-13
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("activity", sa.Column("water_amount_inches", sa.Float(), nullable=True))


def downgrade():
    op.drop_column("activity", "water_amount_inches")
