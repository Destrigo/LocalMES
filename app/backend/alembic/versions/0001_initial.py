"""Initial schema placeholder — LocalMES uses create_all on startup for fresh installs.
Generate real revisions with: alembic revision --autogenerate -m \"message\"
"""

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fresh installs rely on SQLAlchemy create_all in init_db().
    pass


def downgrade() -> None:
    pass
