"""create commercial offers and reusable message templates

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "offers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_min", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("price_max", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "currency",
            sa.String(length=3),
            server_default="KES",
            nullable=False,
        ),
        sa.Column("pitch_angle", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("name <> ''", name=op.f("ck_offers_name_not_blank")),
        sa.CheckConstraint("slug <> ''", name=op.f("ck_offers_slug_not_blank")),
        sa.CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name=op.f("ck_offers_currency_three_uppercase"),
        ),
        sa.CheckConstraint(
            "price_min IS NULL OR price_min >= 0",
            name=op.f("ck_offers_price_min_non_negative"),
        ),
        sa.CheckConstraint(
            "price_max IS NULL OR price_max >= 0",
            name=op.f("ck_offers_price_max_non_negative"),
        ),
        sa.CheckConstraint(
            "price_min IS NULL OR price_max IS NULL OR price_min <= price_max",
            name=op.f("ck_offers_price_range_valid"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_offers")),
    )
    op.create_index(op.f("ix_offers_slug"), "offers", ["slug"], unique=True)

    op.create_table(
        "message_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("offer_id", sa.Uuid(), nullable=False),
        sa.Column(
            "channel",
            sa.Enum(
                "email",
                "sms",
                name="template_channel",
                native_enum=False,
                create_constraint=True,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("variant", sa.String(length=16), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "variables",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "name <> ''", name=op.f("ck_message_templates_name_not_blank")
        ),
        sa.CheckConstraint(
            "variant <> ''", name=op.f("ck_message_templates_variant_not_blank")
        ),
        sa.CheckConstraint(
            "body <> ''", name=op.f("ck_message_templates_body_not_blank")
        ),
        sa.CheckConstraint(
            "jsonb_typeof(variables) = 'array'",
            name=op.f("ck_message_templates_variables_array"),
        ),
        sa.ForeignKeyConstraint(
            ["offer_id"],
            ["offers.id"],
            name=op.f("fk_message_templates_offer_id_offers"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_message_templates")),
        sa.UniqueConstraint(
            "offer_id",
            "channel",
            "variant",
            name=op.f("uq_message_templates_offer_channel_variant"),
        ),
    )
    op.create_index(
        op.f("ix_message_templates_offer_id"), "message_templates", ["offer_id"]
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_message_templates_offer_id"), table_name="message_templates"
    )
    op.drop_table("message_templates")
    op.drop_index(op.f("ix_offers_slug"), table_name="offers")
    op.drop_table("offers")
