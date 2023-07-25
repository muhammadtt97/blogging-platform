"""Add status column to post

Revision ID: 788a36cc3f02
Revises: 6f4fa871d902
Create Date: 2023-07-25 04:16:46.384582

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '788a36cc3f02'
down_revision = '6f4fa871d902'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=10), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###