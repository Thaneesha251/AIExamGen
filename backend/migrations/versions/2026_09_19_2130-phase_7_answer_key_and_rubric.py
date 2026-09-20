"""phase_7_answer_key_and_rubric

Revision ID: phase_7_answer_key_and_rubric
Revises: phase_6_blueprint_and_paper_gen
Create Date: 2026-09-19 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'phase_7_answer_key_and_rubric'
down_revision: Union[str, None] = 'phase_6_blueprint_and_paper_gen'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Add rubric_id to answer_key_items
    with op.batch_alter_table('answer_key_items') as batch_op:
        batch_op.add_column(sa.Column('rubric_id', sa.String(36), nullable=True))
        batch_op.create_foreign_key('fk_answer_key_item_rubric', 'rubrics', ['rubric_id'], ['id'], ondelete='SET NULL')

    # 2. Add subject_id, question_type, status, version to rubrics
    with op.batch_alter_table('rubrics') as batch_op:
        batch_op.add_column(sa.Column('subject_id', sa.String(36), nullable=True))
        batch_op.add_column(sa.Column('question_type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'))
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
        batch_op.create_foreign_key('fk_rubric_subject', 'subjects', ['subject_id'], ['id'], ondelete='SET NULL')

    # 3. Add min_marks, weight, partial_credit_rules to rubric_criteria
    with op.batch_alter_table('rubric_criteria') as batch_op:
        batch_op.add_column(sa.Column('min_marks', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'))
        batch_op.add_column(sa.Column('partial_credit_rules', sa.JSON(), nullable=True))

def downgrade() -> None:
    with op.batch_alter_table('rubric_criteria') as batch_op:
        batch_op.drop_column('partial_credit_rules')
        batch_op.drop_column('weight')
        batch_op.drop_column('min_marks')

    with op.batch_alter_table('rubrics') as batch_op:
        batch_op.drop_constraint('fk_rubric_subject', type_='foreignkey')
        batch_op.drop_column('version')
        batch_op.drop_column('status')
        batch_op.drop_column('question_type')
        batch_op.drop_column('subject_id')

    with op.batch_alter_table('answer_key_items') as batch_op:
        batch_op.drop_constraint('fk_answer_key_item_rubric', type_='foreignkey')
        batch_op.drop_column('rubric_id')
