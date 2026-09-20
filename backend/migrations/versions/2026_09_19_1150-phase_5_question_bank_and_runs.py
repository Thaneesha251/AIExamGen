"""phase_5_question_bank_and_runs

Revision ID: phase_5_question_bank_and_runs
Revises: phase_4_syllabus_and_assignments
Create Date: 2026-09-19 11:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'phase_5_question_bank_and_runs'
down_revision: Union[str, None] = 'phase_4_syllabus_and_assignments'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create question_generation_runs table
    op.create_table(
        'question_generation_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('subject_id', sa.String(length=36), nullable=False),
        sa.Column('unit_id', sa.String(length=36), nullable=True),
        sa.Column('topic_id', sa.String(length=36), nullable=True),
        sa.Column('learning_outcome_id', sa.String(length=36), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='mock'),
        sa.Column('model', sa.String(length=100), nullable=False, server_default='mock-model'),
        sa.Column('prompt_version', sa.String(length=50), nullable=False, server_default='v1'),
        sa.Column('configuration_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='COMPLETED'),
        sa.Column('requested_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('generated_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accepted_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rejected_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['learning_outcome_id'], ['learning_outcomes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_generation_runs_subject_id'), 'question_generation_runs', ['subject_id'], unique=False)
    op.create_index(op.f('ix_question_generation_runs_status'), 'question_generation_runs', ['status'], unique=False)

    # 2. Add columns to questions table
    with op.batch_alter_table('questions') as batch_op:
        batch_op.add_column(sa.Column('generation_run_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('options', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('validation_data', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
        batch_op.create_foreign_key('fk_questions_generation_run', 'question_generation_runs', ['generation_run_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index(batch_op.f('ix_questions_generation_run_id'), ['generation_run_id'], unique=False)

    # 3. Add options column to question_versions table
    with op.batch_alter_table('question_versions') as batch_op:
        batch_op.add_column(sa.Column('options', sa.JSON(), nullable=True))

def downgrade() -> None:
    with op.batch_alter_table('question_versions') as batch_op:
        batch_op.drop_column('options')

    with op.batch_alter_table('questions') as batch_op:
        batch_op.drop_index(batch_op.f('ix_questions_generation_run_id'))
        batch_op.drop_constraint('fk_questions_generation_run', type_='foreignkey')
        batch_op.drop_column('version')
        batch_op.drop_column('validation_data')
        batch_op.drop_column('options')
        batch_op.drop_column('generation_run_id')

    op.drop_index(op.f('ix_question_generation_runs_status'), table_name='question_generation_runs')
    op.drop_index(op.f('ix_question_generation_runs_subject_id'), table_name='question_generation_runs')
    op.drop_table('question_generation_runs')
