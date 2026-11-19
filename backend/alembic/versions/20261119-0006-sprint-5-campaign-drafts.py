"""add normalized website state and Sprint 5 campaign/draft records

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column(
            "website_presence",
            sa.String(length=16),
            server_default="unknown",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        op.f("ck_leads_website_presence_valid"),
        "leads",
        "website_presence IN ('has_website', 'no_website', 'unknown')",
    )
    op.execute(
        """
        UPDATE leads
        SET website_presence = CASE
            WHEN has_website THEN 'has_website'
            WHEN lower(coalesce(website_status, '')) LIKE '%no website%'
              OR lower(coalesce(website_status, '')) LIKE '%new listing%'
              OR lower(coalesce(website_status, '')) LIKE '%facebook page only%'
              OR lower(coalesce(website_status, '')) LIKE '%instagram only%'
            THEN 'no_website'
            ELSE 'unknown'
        END
        """
    )

    op.create_table(
        "campaigns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("offer_id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("archived_by_id", sa.Uuid(), nullable=True),
        sa.Column("selected_count", sa.Integer(), nullable=False),
        sa.Column("offer_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "template_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "selection_context",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint("name <> ''", name=op.f("ck_campaigns_campaign_name_not_blank")),
        sa.CheckConstraint("goal <> ''", name=op.f("ck_campaigns_campaign_goal_not_blank")),
        sa.CheckConstraint(
            "channel IN ('email', 'sms')", name=op.f("ck_campaigns_campaign_channel_valid")
        ),
        sa.CheckConstraint(
            "selected_count >= 1 AND selected_count <= 200",
            name=op.f("ck_campaigns_campaign_selected_count_valid"),
        ),
        sa.CheckConstraint(
            "length(input_fingerprint) = 64",
            name=op.f("ck_campaigns_campaign_input_fingerprint_length"),
        ),
        sa.ForeignKeyConstraint(
            ["offer_id"],
            ["offers.id"],
            name=op.f("fk_campaigns_offer_id_offers"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["message_templates.id"],
            name=op.f("fk_campaigns_template_id_message_templates"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_campaigns_owner_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["archived_by_id"],
            ["users.id"],
            name=op.f("fk_campaigns_archived_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaigns")),
    )
    op.create_index(op.f("ix_campaigns_offer_id"), "campaigns", ["offer_id"])
    op.create_index(op.f("ix_campaigns_template_id"), "campaigns", ["template_id"])
    op.create_index(op.f("ix_campaigns_owner_id"), "campaigns", ["owner_id"])
    op.create_index(
        "ix_campaigns_archive_generated", "campaigns", ["archived_at", "generated_at"]
    )

    op.create_table(
        "campaign_leads",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("outcome", sa.String(length=16), server_default="pending", nullable=False),
        sa.Column("skip_code", sa.String(length=64), nullable=True),
        sa.Column("skip_label", sa.String(length=120), nullable=True),
        sa.Column("skip_explanation", sa.Text(), nullable=True),
        sa.Column(
            "eligibility_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "outcome IN ('pending', 'drafted', 'skipped')",
            name=op.f("ck_campaign_leads_campaign_lead_outcome_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
            name=op.f("fk_campaign_leads_campaign_id_campaigns"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["leads.id"],
            name=op.f("fk_campaign_leads_lead_id_leads"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_leads")),
        sa.UniqueConstraint("campaign_id", "lead_id", name="uq_campaign_lead"),
    )
    op.create_index(op.f("ix_campaign_leads_campaign_id"), "campaign_leads", ["campaign_id"])
    op.create_index(op.f("ix_campaign_leads_lead_id"), "campaign_leads", ["lead_id"])

    op.create_table(
        "outreaches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_lead_id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("offer_id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("state", sa.String(length=16), server_default="draft", nullable=False),
        sa.Column("rendered_body", sa.Text(), nullable=False),
        sa.Column("offer_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "template_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "eligibility_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("sms_encoding", sa.String(length=16), nullable=True),
        sa.Column("sms_characters", sa.Integer(), nullable=True),
        sa.Column("sms_units", sa.Integer(), nullable=True),
        sa.Column("sms_segments", sa.Integer(), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "channel IN ('email', 'sms')", name=op.f("ck_outreaches_outreach_channel_valid")
        ),
        sa.CheckConstraint("state = 'draft'", name=op.f("ck_outreaches_outreach_sprint5_state")),
        sa.CheckConstraint(
            "rendered_body <> ''", name=op.f("ck_outreaches_outreach_body_not_blank")
        ),
        sa.CheckConstraint(
            "sms_segments IS NULL OR sms_segments >= 1",
            name=op.f("ck_outreaches_outreach_sms_segments_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
            name=op.f("fk_outreaches_campaign_id_campaigns"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["campaign_lead_id"],
            ["campaign_leads.id"],
            name=op.f("fk_outreaches_campaign_lead_id_campaign_leads"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"], ["leads.id"], name=op.f("fk_outreaches_lead_id_leads"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["offer_id"],
            ["offers.id"],
            name=op.f("fk_outreaches_offer_id_offers"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["message_templates.id"],
            name=op.f("fk_outreaches_template_id_message_templates"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outreaches")),
        sa.UniqueConstraint(
            "campaign_id",
            "lead_id",
            "channel",
            name="uq_outreach_campaign_lead_channel",
        ),
        sa.UniqueConstraint("campaign_lead_id"),
    )
    op.create_index(op.f("ix_outreaches_campaign_id"), "outreaches", ["campaign_id"])
    op.create_index(op.f("ix_outreaches_lead_id"), "outreaches", ["lead_id"])

    op.create_table(
        "campaign_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "event_type <> ''", name=op.f("ck_campaign_events_campaign_event_type_not_blank")
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
            name=op.f("fk_campaign_events_campaign_id_campaigns"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name=op.f("fk_campaign_events_actor_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_events")),
    )
    op.create_index(
        op.f("ix_campaign_events_campaign_id"), "campaign_events", ["campaign_id"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_campaign_events_campaign_id"), table_name="campaign_events")
    op.drop_table("campaign_events")
    op.drop_index(op.f("ix_outreaches_lead_id"), table_name="outreaches")
    op.drop_index(op.f("ix_outreaches_campaign_id"), table_name="outreaches")
    op.drop_table("outreaches")
    op.drop_index(op.f("ix_campaign_leads_lead_id"), table_name="campaign_leads")
    op.drop_index(op.f("ix_campaign_leads_campaign_id"), table_name="campaign_leads")
    op.drop_table("campaign_leads")
    op.drop_index("ix_campaigns_archive_generated", table_name="campaigns")
    op.drop_index(op.f("ix_campaigns_owner_id"), table_name="campaigns")
    op.drop_index(op.f("ix_campaigns_template_id"), table_name="campaigns")
    op.drop_index(op.f("ix_campaigns_offer_id"), table_name="campaigns")
    op.drop_table("campaigns")
    op.drop_constraint(
        op.f("ck_leads_website_presence_valid"), "leads", type_="check"
    )
    op.drop_column("leads", "website_presence")
