"""Phase 6: payments and webhook events tables."""
from alembic import op
from apps.api.app.db.database import Base
from apps.api.app.db import models

revision = "20260828_0002"
down_revision = "20260827_0001"
branch_labels = None
depends_on = None

_TARGET_TABLES = ("payments", "webhook_events")


def upgrade():
    bind = op.get_bind()
    # create_all is idempotent: only tables that do not exist yet are created,
    # so the existing Phase 1-5 schema is left untouched.
    Base.metadata.create_all(bind=bind, tables=[models.Payment.__table__, models.WebhookEvent.__table__])


def downgrade():
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, tables=[models.WebhookEvent.__table__, models.Payment.__table__])