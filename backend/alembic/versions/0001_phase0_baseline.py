"""Phase 0 empty migration baseline.

Revision ID: 0001_phase0
Revises:
"""

from typing import Sequence, Union

revision: str = "0001_phase0"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Keep Phase 0 free of business tables."""
    pass


def downgrade() -> None:
    pass
