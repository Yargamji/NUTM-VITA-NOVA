"""create lab request sequences table

Revision ID: e5fb9f5625a6
Revises: 57abcb73d51f
Create Date: 2026-09-27 11:05:56.693641

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e5fb9f5625a6"
down_revision = "57abcb73d51f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lab_request_sequences",
        sa.Column(
            "year",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "last_sequence",
            sa.Integer(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("year"),
    )


def downgrade():
    op.drop_table("lab_request_sequences")