"""Add user_session table

[PATCH-A] 單一有效登入：記錄每位使用者當前有效 Session 的 jti。

Revision ID: a1c0ffee5e55
Revises: 42e2978c7933
Create Date: 2026-07-03 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1c0ffee5e55'
down_revision: Union[str, None] = '42e2978c7933'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_tables = set(inspector.get_table_names())

    # ── Create user_session table (idempotent) ────────────────────────
    if 'user_session' not in existing_tables:
        op.create_table(
            'user_session',
            sa.Column(
                'user_id',
                sa.Text(),
                sa.ForeignKey('user.id', ondelete='CASCADE'),
                primary_key=True,
                nullable=False,
            ),
            sa.Column('session_id', sa.Text(), nullable=False),
            sa.Column('updated_at', sa.BigInteger(), nullable=False),
        )


def downgrade() -> None:
    op.drop_table('user_session')
