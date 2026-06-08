"""add fertilizer programs

Revision ID: 002
Revises: 001
Create Date: 2026-05-13
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fertilizer Program
    op.create_table('fertilizer_program',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('brand', sa.String(100)),
        sa.Column('description', sa.Text()),
        sa.Column('grass_season', sa.String(20)),
        sa.Column('soil_type', sa.String(20)),
        sa.Column('is_builtin', sa.Boolean(), server_default='false'),
        sa.Column('is_custom', sa.Boolean(), server_default='false'),
        sa.Column('source_url', sa.String(500)),
        sa.Column('year', sa.Integer()),
        sa.Column('step_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Fertilizer Step
    op.create_table('fertilizer_step',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('program_id', sa.Integer(), sa.ForeignKey('fertilizer_program.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('product_name', sa.String(300), nullable=False),
        sa.Column('product_description', sa.Text()),
        sa.Column('season', sa.String(30)),
        sa.Column('month_start', sa.Integer()),
        sa.Column('month_end', sa.Integer()),
        sa.Column('application_rate_per_1k', sa.String(100)),
        sa.Column('coverage_sqft_per_bag', sa.Integer()),
        sa.Column('bag_weight', sa.String(50)),
        sa.Column('purpose', sa.Text()),
        sa.Column('tips', sa.Text()),
        sa.Column('icon_emoji', sa.String(10), server_default='🧪'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Fertilizer Application (adherence tracking)
    op.create_table('fertilizer_application',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('step_id', sa.Integer(), sa.ForeignKey('fertilizer_step.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lawn_id', sa.Integer(), sa.ForeignKey('lawn_config.id', ondelete='CASCADE'), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('scheduled_date', sa.DateTime(timezone=True)),
        sa.Column('applied_date', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('notes', sa.Text()),
        sa.Column('product_used', sa.String(300)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Add active_program_id to lawn_config
    op.add_column('lawn_config', sa.Column('active_program_id', sa.Integer(),
        sa.ForeignKey('fertilizer_program.id', ondelete='SET NULL')))


def downgrade() -> None:
    op.drop_column('lawn_config', 'active_program_id')
    op.drop_table('fertilizer_application')
    op.drop_table('fertilizer_step')
    op.drop_table('fertilizer_program')
