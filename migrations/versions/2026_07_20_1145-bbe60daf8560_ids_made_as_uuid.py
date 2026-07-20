"""ids made as uuid

Revision ID: bbe60daf8560
Revises: 470ed32a752e
Create Date: 2026-07-20 11:45:47.138110

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bbe60daf8560"
down_revision: str | Sequence[str] | None = "470ed32a752e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("refresh_token_user_id_fkey", "refresh_token", type_="foreignkey")
    op.drop_constraint("user_social_account_user_id_fkey", "user_social_account", type_="foreignkey")

    op.execute('ALTER TABLE "user" ALTER COLUMN id DROP DEFAULT')
    op.execute("ALTER TABLE user_social_account ALTER COLUMN id DROP DEFAULT")

    op.execute('ALTER TABLE "user" ALTER COLUMN id TYPE uuid USING id::text::uuid')
    op.execute("ALTER TABLE refresh_token ALTER COLUMN user_id TYPE uuid USING user_id::text::uuid")
    op.execute("ALTER TABLE user_social_account ALTER COLUMN id TYPE uuid USING id::text::uuid")
    op.execute("ALTER TABLE user_social_account ALTER COLUMN user_id TYPE uuid USING user_id::text::uuid")

    op.alter_column("user", "id", server_default=sa.text("gen_random_uuid()"))
    op.alter_column("user_social_account", "id", server_default=sa.text("gen_random_uuid()"))

    op.create_foreign_key("refresh_token_user_id_fkey", "refresh_token", "user", ["user_id"], ["id"])
    op.create_foreign_key("user_social_account_user_id_fkey", "user_social_account", "user", ["user_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("refresh_token_user_id_fkey", "refresh_token", type_="foreignkey")
    op.drop_constraint("user_social_account_user_id_fkey", "user_social_account", type_="foreignkey")

    op.execute('ALTER TABLE "user" ALTER COLUMN id DROP DEFAULT')
    op.execute("ALTER TABLE user_social_account ALTER COLUMN id DROP DEFAULT")

    op.execute("ALTER TABLE user_social_account ALTER COLUMN user_id TYPE integer USING NULL")
    op.execute("ALTER TABLE user_social_account ALTER COLUMN id TYPE integer USING NULL")
    op.execute("ALTER TABLE refresh_token ALTER COLUMN user_id TYPE integer USING NULL")
    op.execute('ALTER TABLE "user" ALTER COLUMN id TYPE integer USING NULL')

    op.create_foreign_key("refresh_token_user_id_fkey", "refresh_token", "user", ["user_id"], ["id"])
    op.create_foreign_key("user_social_account_user_id_fkey", "user_social_account", "user", ["user_id"], ["id"])
