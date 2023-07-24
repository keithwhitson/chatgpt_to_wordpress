"""added article updated

Revision ID: 357f31b330da
Revises: d44e4dab4425
Create Date: 2023-07-24 03:34:00.352025

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '357f31b330da'
down_revision = 'd44e4dab4425'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('trends', sa.Column('article_wordpress_updated', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('trends', 'article_wordpress_updated')
    # ### end Alembic commands ###
