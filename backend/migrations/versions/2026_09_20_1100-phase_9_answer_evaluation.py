"""phase_9_answer_evaluation

Revision ID: phase_9_answer_evaluation
Revises: phase_8_answer_paper_ingestion
Create Date: 2026-09-20 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'phase_9_answer_evaluation'
down_revision: Union[str, None] = 'phase_8_answer_paper_ingestion'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Add columns to evaluations
    with op.batch_alter_table('evaluations') as batch_op:
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('requires_review', sa.Boolean(), nullable=False, server_default='0'))

    # 2. Add columns to evaluation_items
    with op.batch_alter_table('evaluation_items') as batch_op:
        batch_op.add_column(sa.Column('strengths', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('missing_points', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('criterion_scores', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('requires_faculty_review', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('review_reason', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('prompt_version', sa.String(length=50), nullable=True, server_default='v1'))

def downgrade() -> None:
    with op.batch_alter_table('evaluation_items') as batch_op:
        batch_op.drop_column('prompt_version')
        batch_op.drop_column('review_reason')
        batch_op.drop_column('requires_faculty_review')
        batch_op.drop_column('criterion_scores')
        batch_op.drop_column('missing_points')
        batch_op.drop_column('strengths')

    with op.batch_alter_table('evaluations') as batch_op:
        batch_op.drop_column('requires_review')
        batch_op.drop_column('version')
