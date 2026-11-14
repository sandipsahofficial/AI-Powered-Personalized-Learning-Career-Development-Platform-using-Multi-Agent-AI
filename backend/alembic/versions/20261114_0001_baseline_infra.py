"""Baseline infrastructure and pgvector extension initialization

Revision ID: 0001_baseline_infra
Revises: 
Create Date: 2026-11-14 10:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_baseline_infra'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Activate essential extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector";')

    # Baseline system verification table
    op.create_table(
        'system_health_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('component_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('system_health_checks')
