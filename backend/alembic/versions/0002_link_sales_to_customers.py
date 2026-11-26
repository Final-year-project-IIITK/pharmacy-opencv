"""Link sales invoices to CRM customers."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0002_link_sales_to_customers"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    columns = {column["name"] for column in inspect(connection).get_columns("sale_invoices")}
    if "customer_id" not in columns:
        op.add_column("sale_invoices", sa.Column("customer_id", sa.Integer(), nullable=True))
    indexes = {index["name"] for index in inspect(connection).get_indexes("sale_invoices")}
    if "ix_sale_invoices_customer_id" not in indexes:
        op.create_index("ix_sale_invoices_customer_id", "sale_invoices", ["customer_id"])


def downgrade() -> None:
    connection = op.get_bind()
    indexes = {index["name"] for index in inspect(connection).get_indexes("sale_invoices")}
    if "ix_sale_invoices_customer_id" in indexes:
        op.drop_index("ix_sale_invoices_customer_id", table_name="sale_invoices")
    columns = {column["name"] for column in inspect(connection).get_columns("sale_invoices")}
    if "customer_id" in columns:
        op.drop_column("sale_invoices", "customer_id")
