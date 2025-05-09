"""empty message

Revision ID: e83fd142ba83
Revises: dc2af5838860
Create Date: 2025-03-27 04:07:58.909414

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e83fd142ba83"
down_revision: Union[str, None] = "dc2af5838860"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "collections",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("highlighted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "collection_games",
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["collections.id"],
        ),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
        ),
        sa.PrimaryKeyConstraint("game_id", "collection_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("collection_games")
    op.drop_table("collections")
    # ### end Alembic commands ###
