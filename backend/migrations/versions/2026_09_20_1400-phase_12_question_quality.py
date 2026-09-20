"""Phase 12 Question Quality Reviews

Revision ID: phase_12_question_quality
Revises: phase_11_similarity_analytics
Create Date: 2026-09-20 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'phase_12_question_quality'
down_revision = 'phase_11_similarity_analytics'
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tables = inspector.get_table_names()
    if 'question_quality_reviews' not in tables:
        op.create_table(
            'question_quality_reviews',
            sa.Column('id', sa.CHAR(36), primary_key=True),
            sa.Column('question_id', sa.CHAR(36), sa.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False),
            sa.Column('examination_id', sa.CHAR(36), sa.ForeignKey('examinations.id', ondelete='CASCADE'), nullable=True),
            sa.Column('reviewer_id', sa.CHAR(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='REVIEWED'),
            sa.Column('note', sa.Text(), nullable=True),
            sa.Column('reviewed_at', sa.String(length=30), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True)
        )
        op.create_index('idx_question_quality_reviews_q_exam', 'question_quality_reviews', ['question_id', 'examination_id'])
        op.create_index('ix_question_quality_reviews_question_id', 'question_quality_reviews', ['question_id'])

def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    if 'question_quality_reviews' in tables:
        op.drop_table('question_quality_reviews')
