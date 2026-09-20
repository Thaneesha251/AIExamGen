"""Phase 10 Faculty Review and Finalization

Revision ID: phase_10_faculty_review_finalization
Revises: phase_9_answer_evaluation
Create Date: 2026-09-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'phase_10_faculty_review_finalization'
down_revision = 'phase_9_answer_evaluation'
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    eval_cols = [c['name'] for c in inspector.get_columns('evaluations')]
    item_cols = [c['name'] for c in inspector.get_columns('evaluation_items')]
    review_cols = [c['name'] for c in inspector.get_columns('faculty_reviews')]

    with op.batch_alter_table('evaluations') as batch_op:
        if 'reviewed_by' not in eval_cols:
            batch_op.add_column(sa.Column('reviewed_by', sa.CHAR(36), nullable=True))
        if 'approved_by' not in eval_cols:
            batch_op.add_column(sa.Column('approved_by', sa.CHAR(36), nullable=True))
        if 'approved_at' not in eval_cols:
            batch_op.add_column(sa.Column('approved_at', sa.String(length=30), nullable=True))
        if 'finalized_by' not in eval_cols:
            batch_op.add_column(sa.Column('finalized_by', sa.CHAR(36), nullable=True))
        if 'finalized_at' not in eval_cols:
            batch_op.add_column(sa.Column('finalized_at', sa.String(length=30), nullable=True))
        if 'review_notes' not in eval_cols:
            batch_op.add_column(sa.Column('review_notes', sa.Text(), nullable=True))
        if 'finalization_notes' not in eval_cols:
            batch_op.add_column(sa.Column('finalization_notes', sa.Text(), nullable=True))

    with op.batch_alter_table('evaluation_items') as batch_op:
        if 'review_status' not in item_cols:
            batch_op.add_column(sa.Column('review_status', sa.String(length=50), server_default='PENDING', nullable=True))
        if 'override_reason' not in item_cols:
            batch_op.add_column(sa.Column('override_reason', sa.Text(), nullable=True))
        if 'faculty_comment' not in item_cols:
            batch_op.add_column(sa.Column('faculty_comment', sa.Text(), nullable=True))
        if 'reviewed_by' not in item_cols:
            batch_op.add_column(sa.Column('reviewed_by', sa.CHAR(36), nullable=True))
        if 'reviewed_at' not in item_cols:
            batch_op.add_column(sa.Column('reviewed_at', sa.String(length=30), nullable=True))

    with op.batch_alter_table('faculty_reviews') as batch_op:
        if 'reason' not in review_cols:
            batch_op.add_column(sa.Column('reason', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('faculty_reviews') as batch_op:
        batch_op.drop_column('reason')

    with op.batch_alter_table('evaluation_items') as batch_op:
        batch_op.drop_column('reviewed_at')
        batch_op.drop_column('reviewed_by')
        batch_op.drop_column('faculty_comment')
        batch_op.drop_column('override_reason')
        batch_op.drop_column('review_status')

    with op.batch_alter_table('evaluations') as batch_op:
        batch_op.drop_column('finalization_notes')
        batch_op.drop_column('review_notes')
        batch_op.drop_column('finalized_at')
        batch_op.drop_column('finalized_by')
        batch_op.drop_column('approved_at')
        batch_op.drop_column('approved_by')
        batch_op.drop_column('reviewed_by')
