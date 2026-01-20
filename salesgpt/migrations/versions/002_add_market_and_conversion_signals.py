"""add_market_and_conversion_signals

Revision ID: 002_add_market_and_conversion_signals
Revises: 001_add_ab_testing
Create Date: 2026-01-20 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002_add_market_and_conversion_signals"
down_revision = "001_add_ab_testing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Segmentation labels
    op.add_column("leads", sa.Column("market", sa.String(50), nullable=True))
    op.add_column("leads", sa.Column("persona", sa.String(100), nullable=True))

    # Conversion signals
    op.add_column("leads", sa.Column("free_signup_at", sa.DateTime(), nullable=True))
    op.add_column("leads", sa.Column("paid_pro_at", sa.DateTime(), nullable=True))
    op.add_column("leads", sa.Column("paid_pro_price_id", sa.String(255), nullable=True))
    op.add_column("leads", sa.Column("paid_pro_invoice_id", sa.String(255), nullable=True))
    op.add_column("leads", sa.Column("paid_pro_amount", sa.Float(), nullable=True))

    # Indexes for analytics
    op.create_index("idx_lead_market", "leads", ["market"])
    op.create_index("idx_lead_persona", "leads", ["persona"])
    op.create_index("idx_lead_free_signup_at", "leads", ["free_signup_at"])
    op.create_index("idx_lead_paid_pro_at", "leads", ["paid_pro_at"])
    op.create_index("idx_lead_paid_pro_price_id", "leads", ["paid_pro_price_id"])


def downgrade() -> None:
    op.drop_index("idx_lead_paid_pro_price_id", table_name="leads")
    op.drop_index("idx_lead_paid_pro_at", table_name="leads")
    op.drop_index("idx_lead_free_signup_at", table_name="leads")
    op.drop_index("idx_lead_persona", table_name="leads")
    op.drop_index("idx_lead_market", table_name="leads")

    op.drop_column("leads", "paid_pro_amount")
    op.drop_column("leads", "paid_pro_invoice_id")
    op.drop_column("leads", "paid_pro_price_id")
    op.drop_column("leads", "paid_pro_at")
    op.drop_column("leads", "free_signup_at")
    op.drop_column("leads", "persona")
    op.drop_column("leads", "market")


