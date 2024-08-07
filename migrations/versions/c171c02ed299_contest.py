"""contest

Revision ID: c171c02ed299
Revises: 82b44b92271e
Create Date: 2024-07-03 20:53:21.181208

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c171c02ed299'
down_revision: Union[str, None] = '82b44b92271e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('contest',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('total_tests', sa.Integer(), nullable=False),
    sa.Column('points', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contest_id'), 'contest', ['id'], unique=False)
    op.create_table('answer_question_system',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('request_id', sa.Integer(), nullable=True),
    sa.Column('rigth_answer', sa.String(), nullable=False),
    sa.Column('is_answered', sa.Boolean(), nullable=False),
    sa.Column('metrics', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['request_id'], ['request_statistic.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_answer_question_system_id'), 'answer_question_system', ['id'], unique=False)
    op.create_table('test_system',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('request_id', sa.Integer(), nullable=True),
    sa.Column('question', sa.String(), nullable=False),
    sa.Column('option_1', sa.String(), nullable=False),
    sa.Column('option_2', sa.String(), nullable=False),
    sa.Column('option_3', sa.String(), nullable=False),
    sa.Column('option_4', sa.String(), nullable=False),
    sa.Column('rigth_answer', sa.String(), nullable=False),
    sa.Column('is_answered', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['request_id'], ['request_statistic.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_test_system_id'), 'test_system', ['id'], unique=False)
    op.add_column('doc', sa.Column('type', sa.String(), nullable=True))
    op.drop_column('feedback', 'llm_response')
    op.drop_column('feedback', 'viewed')
    op.drop_column('request_statistic', 'metrics')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('request_statistic', sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('feedback', sa.Column('viewed', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('feedback', sa.Column('llm_response', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_column('doc', 'type')
    op.drop_index(op.f('ix_test_system_id'), table_name='test_system')
    op.drop_table('test_system')
    op.drop_index(op.f('ix_answer_question_system_id'), table_name='answer_question_system')
    op.drop_table('answer_question_system')
    op.drop_index(op.f('ix_contest_id'), table_name='contest')
    op.drop_table('contest')
    # ### end Alembic commands ###
