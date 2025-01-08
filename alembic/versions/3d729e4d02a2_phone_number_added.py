"""phone number added

Revision ID: 3d729e4d02a2
Revises: 
Create Date: 2025-01-08 19:37:45.378049

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d729e4d02a2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None: #cloumun eklerken
    op.add_column('users', sa.Column('phone_number', sa.String(length=15), nullable=True))


def downgrade() -> None: #silerken
    pass
