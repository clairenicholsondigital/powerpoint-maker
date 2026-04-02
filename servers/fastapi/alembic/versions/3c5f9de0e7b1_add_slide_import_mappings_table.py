"""add slide import mappings table

Revision ID: 3c5f9de0e7b1
Revises: 82abdbc476a7
Create Date: 2026-04-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3c5f9de0e7b1"
down_revision: Union[str, None] = "82abdbc476a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "slide_import_mappings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slide_id", sa.Uuid(), nullable=False),
        sa.Column("presentation_id", sa.Uuid(), nullable=False),
        sa.Column("slide_index", sa.Integer(), nullable=False),
        sa.Column("shape_key", sa.String(), nullable=False),
        sa.Column("source_part", sa.String(), nullable=False),
        sa.Column("source_shape_id", sa.String(), nullable=True),
        sa.Column("rel_id", sa.String(), nullable=True),
        sa.Column("media_target", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["slide_id"], ["slides.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "slide_id", "shape_key", name="uq_slide_import_mapping_slide_shape"
        ),
    )
    op.create_index(
        op.f("ix_slide_import_mappings_slide_id"),
        "slide_import_mappings",
        ["slide_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_slide_import_mappings_presentation_id"),
        "slide_import_mappings",
        ["presentation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_slide_import_mappings_slide_index"),
        "slide_import_mappings",
        ["slide_index"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_slide_import_mappings_slide_index"), table_name="slide_import_mappings")
    op.drop_index(op.f("ix_slide_import_mappings_presentation_id"), table_name="slide_import_mappings")
    op.drop_index(op.f("ix_slide_import_mappings_slide_id"), table_name="slide_import_mappings")
    op.drop_table("slide_import_mappings")
