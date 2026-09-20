"""phase_4_syllabus_and_assignments

Revision ID: phase_4_syllabus_and_assignments
Revises: 45d20984c7ea
Create Date: 2026-09-19 11:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'phase_4_syllabus_and_assignments'
down_revision: Union[str, None] = '45d20984c7ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create faculty_subject_assignments table
    op.create_table(
        'faculty_subject_assignments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('faculty_id', sa.String(length=36), nullable=False),
        sa.Column('subject_id', sa.String(length=36), nullable=False),
        sa.Column('academic_year_id', sa.String(length=36), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['faculty_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('faculty_id', 'subject_id', 'academic_year_id', name='uq_faculty_subject_year')
    )
    op.create_index(op.f('ix_faculty_subject_assignments_faculty_id'), 'faculty_subject_assignments', ['faculty_id'], unique=False)
    op.create_index(op.f('ix_faculty_subject_assignments_subject_id'), 'faculty_subject_assignments', ['subject_id'], unique=False)
    op.create_index(op.f('ix_faculty_subject_assignments_academic_year_id'), 'faculty_subject_assignments', ['academic_year_id'], unique=False)

    # 2. Create syllabus_documents table
    op.create_table(
        'syllabus_documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('subject_id', sa.String(length=36), nullable=False),
        sa.Column('uploaded_by', sa.String(length=36), nullable=False),
        sa.Column('file_asset_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('status', sa.Enum('UPLOADED', 'PROCESSING', 'TEXT_EXTRACTED', 'STRUCTURED', 'REVIEW_REQUIRED', 'APPROVED', 'FAILED', name='syllabusprocessingstatusenum'), nullable=False),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('structured_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['file_asset_id'], ['file_assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_syllabus_documents_subject_id'), 'syllabus_documents', ['subject_id'], unique=False)
    op.create_index(op.f('ix_syllabus_documents_is_current'), 'syllabus_documents', ['is_current'], unique=False)
    op.create_index(op.f('ix_syllabus_documents_status'), 'syllabus_documents', ['status'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_syllabus_documents_status'), table_name='syllabus_documents')
    op.drop_index(op.f('ix_syllabus_documents_is_current'), table_name='syllabus_documents')
    op.drop_index(op.f('ix_syllabus_documents_subject_id'), table_name='syllabus_documents')
    op.drop_table('syllabus_documents')

    op.drop_index(op.f('ix_faculty_subject_assignments_academic_year_id'), table_name='faculty_subject_assignments')
    op.drop_index(op.f('ix_faculty_subject_assignments_subject_id'), table_name='faculty_subject_assignments')
    op.drop_index(op.f('ix_faculty_subject_assignments_faculty_id'), table_name='faculty_subject_assignments')
    op.drop_table('faculty_subject_assignments')
