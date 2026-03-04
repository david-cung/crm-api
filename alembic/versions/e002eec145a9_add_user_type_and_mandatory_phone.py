"""add_user_type_and_mandatory_phone

Revision ID: e002eec145a9
Revises: ddf07c225cd2
Create Date: 2026-03-03 22:26:45.256304

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e002eec145a9'
down_revision: Union[str, Sequence[str], None] = 'ddf07c225cd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the enum type manually for PostgreSQL
    usertype_enum = sa.Enum('WEB_ADMIN', 'MOBILE_APP', name='usertype')
    usertype_enum.create(op.get_bind())
    
    # Update existing users to have a placeholder phone number if null
    op.execute("UPDATE \"user\" SET phone_number = '0000000000' WHERE phone_number IS NULL")
    
    op.add_column('user', sa.Column('user_type', sa.Enum('WEB_ADMIN', 'MOBILE_APP', name='usertype'), server_default='MOBILE_APP', nullable=False))
    
    # Set existing users (admin) to WEB_ADMIN
    op.execute("UPDATE \"user\" SET user_type = 'WEB_ADMIN'")
    
    op.alter_column('user', 'phone_number',
               existing_type=sa.VARCHAR(),
               nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('user', 'phone_number',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.drop_column('user', 'user_type')
    
    # Drop the enum type
    sa.Enum(name='usertype').drop(op.get_bind())
