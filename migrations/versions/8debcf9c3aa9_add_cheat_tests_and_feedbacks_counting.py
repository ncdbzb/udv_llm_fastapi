"""add cheat_tests and feedbacks counting

Revision ID: 8debcf9c3aa9
Revises: 452969261a3e
Create Date: 2024-07-17 22:26:31.593692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8debcf9c3aa9'
down_revision: Union[str, None] = '452969261a3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('contest', sa.Column('cheat_tests', sa.Integer(), nullable=True))
    op.add_column('contest', sa.Column('answer_question_feedbacks', sa.Integer(), nullable=True))
    op.add_column('contest', sa.Column('test_feedbacks', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('contest', 'test_feedbacks')
    op.drop_column('contest', 'answer_question_feedbacks')
    op.drop_column('contest', 'cheat_tests')
    # ### end Alembic commands ###
