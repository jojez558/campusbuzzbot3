"""Initial schema — all CampusBuzz tables

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Let SQLAlchemy create tables via models.py on first run.
    # This migration is a no-op placeholder so Alembic tracks the baseline.
    pass


def downgrade() -> None:
    pass
