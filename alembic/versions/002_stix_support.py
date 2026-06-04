"""stix support

Revision ID: 002_stix_support
Revises: 001_initial
Create Date: 2026-06-04 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = '002_stix_support'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('stix_objects',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('pattern', sa.Text(), nullable=True),
        sa.Column('pattern_type', sa.String(length=50), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('object_data', JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_stix_obj_created', 'stix_objects', ['created'], unique=False)
    op.create_index('idx_stix_obj_type', 'stix_objects', ['type'], unique=False)

    op.create_table('stix_relationships',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('relationship_type', sa.String(length=100), nullable=False),
        sa.Column('source_ref', sa.String(length=255), nullable=False),
        sa.Column('target_ref', sa.String(length=255), nullable=False),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('object_data', JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['source_ref'], ['stix_objects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_ref'], ['stix_objects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_ref', 'target_ref', 'relationship_type', name='uq_stix_rel')
    )

def downgrade() -> None:
    op.drop_table('stix_relationships')
    op.drop_index('idx_stix_obj_type', table_name='stix_objects')
    op.drop_index('idx_stix_obj_created', table_name='stix_objects')
    op.drop_table('stix_objects')
