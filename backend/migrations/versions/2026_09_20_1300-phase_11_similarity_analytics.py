"""Phase 11 Answer Similarity and Analytics

Revision ID: phase_11_similarity_analytics
Revises: phase_10_faculty_review_finalization
Create Date: 2026-09-20 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'phase_11_similarity_analytics'
down_revision = 'phase_10_faculty_review_finalization'
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    plag_cols = [c['name'] for c in inspector.get_columns('plagiarism_results')]
    sim_cols = [c['name'] for c in inspector.get_columns('answer_similarities')]

    with op.batch_alter_table('plagiarism_results') as batch_op:
        if 'lexical_score' not in plag_cols:
            batch_op.add_column(sa.Column('lexical_score', sa.Float(), nullable=True))
        if 'semantic_score' not in plag_cols:
            batch_op.add_column(sa.Column('semantic_score', sa.Float(), nullable=True))
        if 'combined_score' not in plag_cols:
            batch_op.add_column(sa.Column('combined_score', sa.Float(), nullable=True))
        if 'threshold_used' not in plag_cols:
            batch_op.add_column(sa.Column('threshold_used', sa.Float(), nullable=True))
        if 'analysis_version' not in plag_cols:
            batch_op.add_column(sa.Column('analysis_version', sa.String(length=50), server_default='v1.0', nullable=True))
        if 'reviewed_by' not in plag_cols:
            batch_op.add_column(sa.Column('reviewed_by', sa.CHAR(36), nullable=True))
        if 'reviewed_at' not in plag_cols:
            batch_op.add_column(sa.Column('reviewed_at', sa.String(length=30), nullable=True))
        if 'review_notes' not in plag_cols:
            batch_op.add_column(sa.Column('review_notes', sa.Text(), nullable=True))

    with op.batch_alter_table('answer_similarities') as batch_op:
        if 'examination_id' not in sim_cols:
            batch_op.add_column(sa.Column('examination_id', sa.CHAR(36), nullable=True))
        if 'question_id' not in sim_cols:
            batch_op.add_column(sa.Column('question_id', sa.CHAR(36), nullable=True))
        if 'lexical_score' not in sim_cols:
            batch_op.add_column(sa.Column('lexical_score', sa.Float(), nullable=True))
        if 'semantic_score' not in sim_cols:
            batch_op.add_column(sa.Column('semantic_score', sa.Float(), nullable=True))
        if 'combined_score' not in sim_cols:
            batch_op.add_column(sa.Column('combined_score', sa.Float(), nullable=True))
        if 'flagged_for_review' not in sim_cols:
            batch_op.add_column(sa.Column('flagged_for_review', sa.Boolean(), server_default='0', nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('answer_similarities') as batch_op:
        batch_op.drop_column('flagged_for_review')
        batch_op.drop_column('combined_score')
        batch_op.drop_column('semantic_score')
        batch_op.drop_column('lexical_score')
        batch_op.drop_column('question_id')
        batch_op.drop_column('examination_id')

    with op.batch_alter_table('plagiarism_results') as batch_op:
        batch_op.drop_column('review_notes')
        batch_op.drop_column('reviewed_at')
        batch_op.drop_column('reviewed_by')
        batch_op.drop_column('analysis_version')
        batch_op.drop_column('threshold_used')
        batch_op.drop_column('combined_score')
        batch_op.drop_column('semantic_score')
        batch_op.drop_column('lexical_score')
