"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-10 11:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('user_id', sa.String(36), nullable=False),  # UUID as string for SQLite compatibility
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('role', sa.Enum('resident', 'society_manager', 'operator', 'municipal', 'admin', name='userroleenum'), nullable=False),
        sa.Column('ward_id', sa.String(length=32), nullable=True),
        sa.Column('society_id', sa.String(length=64), nullable=True),
        sa.Column('consent_flags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email')
    )

    # Materials table
    op.create_table(
        'materials',
        sa.Column('material_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('category', sa.Enum('plastic', 'glass', 'metal', 'organic', 'paper', 'e_waste', 'composite', 'hazardous', 'other', name='materialcategoryenum'), nullable=False),
        sa.Column('subcategory', sa.String(length=64), nullable=True),
        sa.Column('disposal_bin', sa.Enum('wet', 'dry', 'hazardous', 'e_waste', 'rejected', name='disposalbinenum'), nullable=False),
        sa.Column('recovery_potential', sa.Enum('high', 'medium', 'low', 'none', name='recoverypotentialenum'), nullable=False),
        sa.Column('next_life', sa.Text(), nullable=True),
        sa.Column('recovery_channel', sa.String(length=64), nullable=True),
        sa.Column('contamination_notes', sa.Text(), nullable=True),
        sa.Column('icon_slug', sa.String(length=64), nullable=True),
        sa.Column('demo_seed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('material_id')
    )

    # User Corrections table
    op.create_table(
        'user_corrections',
        sa.Column('correction_id', sa.String(36), nullable=False),  # UUID as string for SQLite compatibility
        sa.Column('event_id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('corrected_class', sa.String(length=64), nullable=False),
        sa.Column('correction_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reviewed', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('correction_id')
    )
    op.create_index(op.f('ix_user_corrections_event_id'), 'user_corrections', ['event_id'], unique=False)
    op.create_index(op.f('ix_user_corrections_session_id'), 'user_corrections', ['session_id'], unique=False)

    # Classification Events table
    op.create_table(
        'classification_events',
        sa.Column('event_id', sa.String(36), nullable=False),  # UUID as string for SQLite compatibility
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ward_id', sa.String(length=32), nullable=True),
        sa.Column('input_type', sa.Enum('image', 'text', name='inputtypeenum'), nullable=False),
        sa.Column('model_version', sa.String(length=32), nullable=False),
        sa.Column('predicted_class', sa.String(length=64), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('top3_predictions', sa.JSON(), nullable=True),
        sa.Column('material_category', sa.Enum('plastic', 'glass', 'metal', 'organic', 'paper', 'e_waste', 'composite', 'hazardous', 'other', name='materialcategoryenum'), nullable=False),
        sa.Column('disposal_bin', sa.Enum('wet', 'dry', 'hazardous', 'e_waste', 'rejected', name='disposalbinenum'), nullable=False),
        sa.Column('recovery_potential', sa.Enum('high', 'medium', 'low', 'none', name='recoverypotentialenum'), nullable=False),
        sa.Column('recovery_channel', sa.String(length=64), nullable=True),
        sa.Column('is_corrected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('correction_id', sa.String(36), nullable=True),
        sa.Column('image_stored', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('image_key', sa.Text(), nullable=True),
        sa.Column('consent_flags', sa.JSON(), nullable=True),
        sa.Column('demo_mode', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['correction_id'], ['user_corrections.correction_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('event_id')
    )

    op.create_index('idx_events_ward_created', 'classification_events', ['ward_id', 'created_at'])
    op.create_index('idx_events_session_created', 'classification_events', ['session_id', 'created_at'])
    op.create_index('idx_events_class_created', 'classification_events', ['predicted_class', 'created_at'])
    op.create_index('idx_events_corrected_created', 'classification_events', ['is_corrected', 'created_at'])
    op.create_index('idx_events_demo_created', 'classification_events', ['demo_mode', 'created_at'])

    # Add foreign key from user_corrections back to classification_events.
    # Deferred because classification_events is created after user_corrections
    # (circular FK). Explicit batch block: SQLite recreates the table
    # (copy-and-move) for ALTER constraints; on PostgreSQL recreate="auto"
    # renders a plain ALTER with no table copy.
    with op.batch_alter_table("user_corrections", recreate="auto") as batch_op:
        batch_op.create_foreign_key('fk_user_corrections_event_id', 'classification_events', ['event_id'], ['event_id'])

    # Ward Analytics Rollups table
    op.create_table(
        'ward_analytics_rollups',
        sa.Column('rollup_id', sa.String(36), nullable=False),  # UUID as string for SQLite compatibility
        sa.Column('ward_id', sa.String(length=32), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_events', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_sessions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('correction_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('contamination_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('recovery_potential_avg', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('low_confidence_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('material_breakdown', sa.JSON(), nullable=True),
        sa.Column('top_misclassifications', sa.JSON(), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('rollup_id'),
        sa.UniqueConstraint('ward_id', 'date', name='uq_ward_date')
    )
    op.create_index(op.f('ix_ward_analytics_rollups_date'), 'ward_analytics_rollups', ['date'], unique=False)
    op.create_index(op.f('ix_ward_analytics_rollups_ward_id'), 'ward_analytics_rollups', ['ward_id'], unique=False)


def downgrade() -> None:
    op.drop_table('ward_analytics_rollups')
    op.drop_constraint('fk_user_corrections_event_id', 'user_corrections', type_='foreignkey')
    op.drop_table('classification_events')
    op.drop_table('user_corrections')
    op.drop_table('materials')
    op.drop_table('users')
