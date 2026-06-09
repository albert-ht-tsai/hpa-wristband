"""add batch_date columns to location and health record tables

Revision ID: b3f8a12e9c01
Revises: caa6dc298f36
Create Date: 2026-06-09

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3f8a12e9c01"
down_revision: Union[str, None] = "caa6dc298f36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE user_device_locations ADD COLUMN IF NOT EXISTS batch_date DATE"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_device_locations_batch_date "
        "ON user_device_locations (batch_date)"
    )
    op.execute(
        "ALTER TABLE user_device_health_records ADD COLUMN IF NOT EXISTS batch_date DATE"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_device_health_records_batch_date "
        "ON user_device_health_records (batch_date)"
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS ix_user_device_health_records_batch_date"
    )
    op.execute(
        "ALTER TABLE user_device_health_records DROP COLUMN IF EXISTS batch_date"
    )
    op.execute(
        "DROP INDEX IF EXISTS ix_user_device_locations_batch_date"
    )
    op.execute(
        "ALTER TABLE user_device_locations DROP COLUMN IF EXISTS batch_date"
    )
