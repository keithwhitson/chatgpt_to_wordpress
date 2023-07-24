"""added article article_excerpt

Revision ID: 1d308b125592
Revises: 9e1662f523f7
Create Date: 2023-07-24 21:08:31.048395

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d308b125592'
down_revision = '9e1662f523f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('trends', sa.Column('article_excerpt', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('trends', 'article_excerpt')
    # ### end Alembic commands ###
