"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-05-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Lawn Config
    op.create_table('lawn_config',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False, server_default='My Lawn'),
        sa.Column('address', sa.String(500)),
        sa.Column('latitude', sa.Float()),
        sa.Column('longitude', sa.Float()),
        sa.Column('grass_type', sa.String(50)),
        sa.Column('climate_zone', sa.String(20)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Lawn Zones
    op.create_table('lawn_zone',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('lawn_id', sa.Integer(), sa.ForeignKey('lawn_config.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('color', sa.String(9), server_default='#52B788'),
        sa.Column('polygon_coords', sa.JSON(), nullable=False),
        sa.Column('area_sqft', sa.Float(), server_default='0'),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Activities
    op.create_table('activity',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('zone_id', sa.Integer(), sa.ForeignKey('lawn_zone.id', ondelete='SET NULL')),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('notes', sa.Text()),
        sa.Column('products_used', sa.JSON()),
        sa.Column('health_score', sa.Integer()),
        sa.Column('photo_url', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Maintenance Schedules
    op.create_table('maintenance_schedule',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('frequency_days', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('zone_id', sa.Integer(), sa.ForeignKey('lawn_zone.id', ondelete='SET NULL')),
        sa.Column('last_completed', sa.DateTime(timezone=True)),
        sa.Column('next_due', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Weather Snapshots
    op.create_table('weather_snapshot',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False, unique=True),
        sa.Column('temp_high_f', sa.Float()),
        sa.Column('temp_low_f', sa.Float()),
        sa.Column('soil_temp_0cm_f', sa.Float()),
        sa.Column('soil_temp_6cm_f', sa.Float()),
        sa.Column('precipitation_in', sa.Float()),
        sa.Column('humidity_pct', sa.Float()),
        sa.Column('wind_speed_mph', sa.Float()),
        sa.Column('uv_index', sa.Float()),
        sa.Column('sunshine_hours', sa.Float()),
        sa.Column('weather_code', sa.Integer()),
        sa.Column('raw_json', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Drought Status
    op.create_table('drought_status',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('drought_level', sa.String(10)),
        sa.Column('drought_label', sa.String(50)),
        sa.Column('coverage_pct', sa.Float()),
        sa.Column('source_data', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Watering Recommendations
    op.create_table('watering_recommendation',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False, unique=True),
        sa.Column('recommendation', sa.String(20)),
        sa.Column('frequency', sa.String(50)),
        sa.Column('duration_minutes', sa.Integer()),
        sa.Column('reasoning', sa.Text()),
        sa.Column('rain_past_7d_in', sa.Float()),
        sa.Column('rain_forecast_7d_in', sa.Float()),
        sa.Column('soil_temp_f', sa.Float()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Lawn Diagnosis
    op.create_table('lawn_diagnosis',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('zone_id', sa.Integer(), sa.ForeignKey('lawn_zone.id', ondelete='SET NULL')),
        sa.Column('photo_path', sa.String(500), nullable=False),
        sa.Column('analysis_result', sa.JSON()),
        sa.Column('recommendations', sa.JSON()),
        sa.Column('ai_model_used', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('lawn_diagnosis')
    op.drop_table('watering_recommendation')
    op.drop_table('drought_status')
    op.drop_table('weather_snapshot')
    op.drop_table('maintenance_schedule')
    op.drop_table('activity')
    op.drop_table('lawn_zone')
    op.drop_table('lawn_config')
