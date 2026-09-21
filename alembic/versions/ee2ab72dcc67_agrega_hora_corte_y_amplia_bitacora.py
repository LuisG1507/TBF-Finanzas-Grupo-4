"""agrega hora_corte y amplia bitacora

Revision ID: ee2ab72dcc67
Revises: 3ca4ff45b789
Create Date: 2026-09-20 12:25:55.414480

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ee2ab72dcc67'
down_revision: Union[str, None] = '3ca4ff45b789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('condicion_credito', sa.Column('hora_corte', sa.Time(), server_default=sa.text("'00:00:00'"), nullable=False))
    op.execute("ALTER TYPE accionbitacora ADD VALUE IF NOT EXISTS 'ANULACION'")
    op.execute("ALTER TYPE entidadbitacora ADD VALUE IF NOT EXISTS 'COMPRA'")
    op.execute("ALTER TYPE entidadbitacora ADD VALUE IF NOT EXISTS 'PAGO'")
    op.execute("ALTER TYPE entidadbitacora ADD VALUE IF NOT EXISTS 'ESTADO_CUENTA'")


def downgrade() -> None:
    # Postgres no permite quitar valores de un ENUM; solo se revierte la columna.
    op.drop_column('condicion_credito', 'hora_corte')
