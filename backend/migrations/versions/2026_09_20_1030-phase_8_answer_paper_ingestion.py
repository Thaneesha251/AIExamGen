"""phase_8_answer_paper_ingestion

Revision ID: phase_8_answer_paper_ingestion
Revises: phase_7_answer_key_and_rubric
Create Date: 2026-09-20 10:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'phase_8_answer_paper_ingestion'
down_revision: Union[str, None] = 'phase_7_answer_key_and_rubric'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Add columns to answer_pages
    with op.batch_alter_table('answer_pages') as batch_op:
        batch_op.add_column(sa.Column('ocr_provider', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('processing_time', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('error_message', sa.Text(), nullable=True))

    # 2. Add columns to extracted_answers
    with op.batch_alter_table('extracted_answers') as batch_op:
        batch_op.add_column(sa.Column('page_start', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('page_end', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('ocr_confidence', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('segmentation_confidence', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'))

def downgrade() -> None:
    with op.batch_alter_table('extracted_answers') as batch_op:
        batch_op.drop_column('status')
        batch_op.drop_column('segmentation_confidence')
        batch_op.drop_column('ocr_confidence')
        batch_op.drop_column('page_end')
        batch_op.drop_column('page_start')

    with op.batch_alter_table('answer_pages') as batch_op:
        batch_op.drop_column('error_message')
        batch_op.drop_column('processing_time')
        batch_op.drop_column('ocr_provider')
