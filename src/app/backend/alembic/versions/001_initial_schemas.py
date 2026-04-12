from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(255), nullable=False, unique=True),
        sa.Column('password', sa.String(255), nullable=False),  # hashed password
        sa.Column('verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('verification_token', sa.String(255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        'user_accounts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_type', sa.String(50), nullable=False, server_default="paper"),  # for now only paper trading, can be live in the future with regulation lol
        sa.Column('balance', sa.Numeric(18, 2), nullable=False, server_default='100000.00'),  # default balance for paper trading
        sa.Column('currency', sa.String(10), nullable=False, server_default="'USD'"),
        sa.Column('status', sa.String(20), nullable=False, server_default="'active'"),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('user_accounts')
    op.drop_table('users')