"""Store per-provider AI keys and model preferences in lawn_config.

Revision ID: 006
Revises: 005
Create Date: 2025-06-05
"""

from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("lawn_config", sa.Column("openai_api_key", sa.String(300)))
    op.add_column("lawn_config", sa.Column("openai_model", sa.String(100), server_default="gpt-4o"))
    op.add_column("lawn_config", sa.Column("anthropic_api_key", sa.String(300)))
    op.add_column("lawn_config", sa.Column("anthropic_model", sa.String(100), server_default="claude-sonnet-4-6"))
    op.add_column("lawn_config", sa.Column("gemini_api_key", sa.String(300)))
    op.add_column("lawn_config", sa.Column("gemini_model", sa.String(100), server_default="gemini-2.0-flash"))


def downgrade():
    for col in ["openai_api_key", "openai_model", "anthropic_api_key", "anthropic_model", "gemini_api_key", "gemini_model"]:
        op.drop_column("lawn_config", col)
