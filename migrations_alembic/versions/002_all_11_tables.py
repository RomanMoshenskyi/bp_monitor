"""All 11 ORM tables from diploma

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Create all additional tables (8 more) ###
    
    # Enum types
    activitytype = postgresql.ENUM('walking', 'running', 'cycling', 'swimming', 'gym', 'yoga', 'sport', 'other', name='activitytype')
    activitytype.create(op.get_bind())
    
    severitylevel = postgresql.ENUM('low', 'medium', 'high', 'critical', name='severitylevel')
    severitylevel.create(op.get_bind())
    
    reportformat = postgresql.ENUM('pdf', 'csv', 'json', name='reportformat')
    reportformat.create(op.get_bind())
    
    reportstatus = postgresql.ENUM('pending', 'generating', 'completed', 'failed', name='reportstatus')
    reportstatus.create(op.get_bind())
    
    # 1. medications table
    op.create_table(
        'medications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('dosage', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('frequency', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_medications_id', 'medications', ['id'])
    op.create_index('ix_medications_patient_id', 'medications', ['patient_id'])
    
    # 2. medication_intakes table
    op.create_table(
        'medication_intakes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('medication_id', sa.Integer(), sa.ForeignKey('medications.id'), nullable=False),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('measurement_id', sa.Integer(), sa.ForeignKey('measurements.id'), nullable=True),
        sa.Column('taken_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('dosage_taken', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_medication_intakes_id', 'medication_intakes', ['id'])
    op.create_index('ix_medication_intakes_medication_id', 'medication_intakes', ['medication_id'])
    op.create_index('ix_medication_intakes_patient_id', 'medication_intakes', ['patient_id'])
    op.create_index('ix_medication_intakes_measurement_id', 'medication_intakes', ['measurement_id'])
    op.create_index('ix_medication_intakes_taken_at', 'medication_intakes', ['taken_at'])
    
    # 3. activity_events table
    op.create_table(
        'activity_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('measurement_id', sa.Integer(), sa.ForeignKey('measurements.id'), nullable=True),
        sa.Column('activity_type', sa.Enum('walking', 'running', 'cycling', 'swimming', 'gym', 'yoga', 'sport', 'other', name='activitytype'), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('intensity', sa.String(length=20), nullable=True),
        sa.Column('calories_burned', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_activity_events_id', 'activity_events', ['id'])
    op.create_index('ix_activity_events_patient_id', 'activity_events', ['patient_id'])
    op.create_index('ix_activity_events_measurement_id', 'activity_events', ['measurement_id'])
    op.create_index('ix_activity_events_started_at', 'activity_events', ['started_at'])
    
    # 4. threshold_profiles table
    op.create_table(
        'threshold_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True, unique=True),
        sa.Column('sys_min', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('sys_max', sa.Integer(), nullable=False, server_default='140'),
        sa.Column('dia_min', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('dia_max', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('pulse_min', sa.Integer(), nullable=True),
        sa.Column('pulse_max', sa.Integer(), nullable=True),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_threshold_profiles_id', 'threshold_profiles', ['id'])
    op.create_index('ix_threshold_profiles_patient_id', 'threshold_profiles', ['patient_id'])
    
    # 5. daily_summaries table
    op.create_table(
        'daily_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('summary_date', sa.Date(), nullable=False),
        sa.Column('avg_systolic', sa.Float(), nullable=True),
        sa.Column('min_systolic', sa.Integer(), nullable=True),
        sa.Column('max_systolic', sa.Integer(), nullable=True),
        sa.Column('avg_diastolic', sa.Float(), nullable=True),
        sa.Column('min_diastolic', sa.Integer(), nullable=True),
        sa.Column('max_diastolic', sa.Integer(), nullable=True),
        sa.Column('avg_pulse', sa.Float(), nullable=True),
        sa.Column('min_pulse', sa.Integer(), nullable=True),
        sa.Column('max_pulse', sa.Integer(), nullable=True),
        sa.Column('measurements_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('patient_id', 'summary_date', name='uq_daily_summary_patient_date')
    )
    op.create_index('ix_daily_summaries_id', 'daily_summaries', ['id'])
    op.create_index('ix_daily_summaries_patient_id', 'daily_summaries', ['patient_id'])
    op.create_index('ix_daily_summaries_summary_date', 'daily_summaries', ['summary_date'])
    op.create_index('ix_daily_summary_patient_date', 'daily_summaries', ['patient_id', 'summary_date'])
    
    # 6. recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('measurement_id', sa.Integer(), sa.ForeignKey('measurements.id'), nullable=True),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='severitylevel'), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.String(length=1), server_default='N'),
        sa.Column('is_acknowledged', sa.String(length=1), server_default='N'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_recommendations_id', 'recommendations', ['id'])
    op.create_index('ix_recommendations_patient_id', 'recommendations', ['patient_id'])
    op.create_index('ix_recommendations_measurement_id', 'recommendations', ['measurement_id'])
    
    # 7. audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('ix_audit_user_timestamp', 'audit_logs', ['user_id', 'timestamp'])
    op.create_index('ix_audit_action_timestamp', 'audit_logs', ['action', 'timestamp'])
    
    # 8. reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_format', sa.Enum('pdf', 'csv', 'json', name='reportformat'), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'generating', 'completed', 'failed', name='reportstatus'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('generated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reports_id', 'reports', ['id'])
    op.create_index('ix_reports_patient_id', 'reports', ['patient_id'])
    op.create_index('ix_reports_generated_by', 'reports', ['generated_by'])
    
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### Drop tables in reverse order ###
    op.drop_index('ix_reports_generated_by', table_name='reports')
    op.drop_index('ix_reports_patient_id', table_name='reports')
    op.drop_index('ix_reports_id', table_name='reports')
    op.drop_table('reports')
    
    op.drop_index('ix_audit_action_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_user_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_user_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_id', table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index('ix_recommendations_measurement_id', table_name='recommendations')
    op.drop_index('ix_recommendations_patient_id', table_name='recommendations')
    op.drop_index('ix_recommendations_id', table_name='recommendations')
    op.drop_table('recommendations')
    
    op.drop_index('ix_daily_summary_patient_date', table_name='daily_summaries')
    op.drop_index('ix_daily_summaries_summary_date', table_name='daily_summaries')
    op.drop_index('ix_daily_summaries_patient_id', table_name='daily_summaries')
    op.drop_index('ix_daily_summaries_id', table_name='daily_summaries')
    op.drop_table('daily_summaries')
    
    op.drop_index('ix_threshold_profiles_patient_id', table_name='threshold_profiles')
    op.drop_index('ix_threshold_profiles_id', table_name='threshold_profiles')
    op.drop_table('threshold_profiles')
    
    op.drop_index('ix_activity_events_started_at', table_name='activity_events')
    op.drop_index('ix_activity_events_measurement_id', table_name='activity_events')
    op.drop_index('ix_activity_events_patient_id', table_name='activity_events')
    op.drop_index('ix_activity_events_id', table_name='activity_events')
    op.drop_table('activity_events')
    
    op.drop_index('ix_medication_intakes_taken_at', table_name='medication_intakes')
    op.drop_index('ix_medication_intakes_measurement_id', table_name='medication_intakes')
    op.drop_index('ix_medication_intakes_patient_id', table_name='medication_intakes')
    op.drop_index('ix_medication_intakes_medication_id', table_name='medication_intakes')
    op.drop_index('ix_medication_intakes_id', table_name='medication_intakes')
    op.drop_table('medication_intakes')
    
    op.drop_index('ix_medications_patient_id', table_name='medications')
    op.drop_index('ix_medications_id', table_name='medications')
    op.drop_table('medications')
    
    # Drop enum types
    reportstatus = postgresql.ENUM(name='reportstatus')
    reportstatus.drop(op.get_bind())
    reportformat = postgresql.ENUM(name='reportformat')
    reportformat.drop(op.get_bind())
    severitylevel = postgresql.ENUM(name='severitylevel')
    severitylevel.drop(op.get_bind())
    activitytype = postgresql.ENUM(name='activitytype')
    activitytype.drop(op.get_bind())
    # ### end Alembic commands ###
