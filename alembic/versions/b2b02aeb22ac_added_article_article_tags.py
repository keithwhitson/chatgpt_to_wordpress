"""added article article_tags

Revision ID: b2b02aeb22ac
Revises: 777bf04ac3ba
Create Date: 2023-07-24 13:55:34.194092

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2b02aeb22ac'
down_revision = '777bf04ac3ba'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('trends', sa.Column('tags_on_wordpress_checked_and_updated', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('trends', 'tags_on_wordpress_checked_and_updated')
    # ### end Alembic commands ###