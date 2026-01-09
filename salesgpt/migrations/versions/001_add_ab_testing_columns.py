"""add_ab_testing_columns

Revision ID: 001_add_ab_testing
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001_add_ab_testing'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add A/B testing columns to leads table
    op.add_column('leads', sa.Column('variant_code', sa.String(255), nullable=True))
    op.add_column('leads', sa.Column('apollo_config_code', sa.String(255), nullable=True))
    op.add_column('leads', sa.Column('persuasion_route', sa.String(50), nullable=True))
    op.add_column('leads', sa.Column('elaboration_score', sa.Float(), nullable=True))
    op.add_column('leads', sa.Column('email_subject', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('email_body', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('email_generated_at', sa.DateTime(), nullable=True))
    op.add_column('leads', sa.Column('email_sent_at', sa.DateTime(), nullable=True))
    op.add_column('leads', sa.Column('reply_received_at', sa.DateTime(), nullable=True))
    op.add_column('leads', sa.Column('reply_intent', sa.String(50), nullable=True))
    op.add_column('leads', sa.Column('booked_at', sa.DateTime(), nullable=True))
    op.add_column('leads', sa.Column('closed_at', sa.DateTime(), nullable=True))
    op.add_column('leads', sa.Column('deal_value', sa.Float(), nullable=True))
    
    # Create indexes
    op.create_index('idx_lead_variant_code', 'leads', ['variant_code'])
    op.create_index('idx_lead_apollo_config_code', 'leads', ['apollo_config_code'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_lead_apollo_config_code', table_name='leads')
    op.drop_index('idx_lead_variant_code', table_name='leads')
    
    # Drop columns
    op.drop_column('leads', 'deal_value')
    op.drop_column('leads', 'closed_at')
    op.drop_column('leads', 'booked_at')
    op.drop_column('leads', 'reply_intent')
    op.drop_column('leads', 'reply_received_at')
    op.drop_column('leads', 'email_sent_at')
    op.drop_column('leads', 'email_generated_at')
    op.drop_column('leads', 'email_body')
    op.drop_column('leads', 'email_subject')
    op.drop_column('leads', 'elaboration_score')
    op.drop_column('leads', 'persuasion_route')
    op.drop_column('leads', 'apollo_config_code')
    op.drop_column('leads', 'variant_code')

