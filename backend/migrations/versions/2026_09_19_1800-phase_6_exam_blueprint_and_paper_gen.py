"""phase_6_exam_blueprint_and_paper_gen

Revision ID: phase_6_blueprint_and_paper_gen
Revises: phase_5_question_bank_and_runs
Create Date: 2026-09-19 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'phase_6_blueprint_and_paper_gen'
down_revision: Union[str, None] = 'phase_5_question_bank_and_runs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Add distribution_json to blueprint_rules
    with op.batch_alter_table('blueprint_rules') as batch_op:
        batch_op.add_column(sa.Column('distribution_json', sa.JSON(), nullable=True))

    # 2. Add snapshots to question_paper_items
    with op.batch_alter_table('question_paper_items') as batch_op:
        batch_op.add_column(sa.Column('options_snapshot', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('question_type_snapshot', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('difficulty_snapshot', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('bloom_snapshot', sa.String(length=50), nullable=True))

def downgrade() -> None:
    with op.batch_alter_table('question_paper_items') as batch_op:
        batch_op.drop_column('bloom_snapshot')
        batch_op.drop_column('difficulty_snapshot')
        batch_op.drop_column('question_type_snapshot')
        batch_op.drop_column('options_snapshot')

    with op.batch_alter_table('blueprint_rules') as batch_op:
        batch_op.drop_column('distribution_json')
