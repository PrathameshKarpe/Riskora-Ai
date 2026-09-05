"""Initial Riskora schema."""
from alembic import op
from apps.api.app.db.database import Base
from apps.api.app.db import models

revision = "20260827_0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

def downgrade():
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
