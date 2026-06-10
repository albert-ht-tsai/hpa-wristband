"""rename batch_date to start_date and add end_date columns

Revision ID: d7f2c841b305
Revises: b3f8a12e9c01
Create Date: 2026-06-10

"""
from typing import Sequence, Union
from alembic import op

revision: str = "d7f2c841b305"
down_revision: Union[str, None] = "b3f8a12e9c01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE user_device_locations RENAME COLUMN batch_date TO start_date"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_user_device_locations_batch_date "
        "RENAME TO ix_user_device_locations_start_date"
    )
    op.execute(
        "ALTER TABLE user_device_locations ADD COLUMN IF NOT EXISTS end_date DATE"
    )

    op.execute(
        "ALTER TABLE user_device_health_records RENAME COLUMN batch_date TO start_date"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_user_device_health_records_batch_date "
        "RENAME TO ix_user_device_health_records_start_date"
    )
    op.execute(
        "ALTER TABLE user_device_health_records ADD COLUMN IF NOT EXISTS end_date DATE"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE user_device_health_records DROP COLUMN IF EXISTS end_date"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_user_device_health_records_start_date "
        "RENAME TO ix_user_device_health_records_batch_date"
    )
    op.execute(
        "ALTER TABLE user_device_health_records RENAME COLUMN start_date TO batch_date"
    )

    op.execute(
        "ALTER TABLE user_device_locations DROP COLUMN IF EXISTS end_date"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_user_device_locations_start_date "
        "RENAME TO ix_user_device_locations_batch_date"
    )
    op.execute(
        "ALTER TABLE user_device_locations RENAME COLUMN start_date TO batch_date"
    )
