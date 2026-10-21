"""add lead provenance, channel review, and terminal suppression

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("email", sa.String(length=255), nullable=True))
    op.create_index("ix_leads_email", "leads", ["email"], unique=False)
    op.add_column(
        "activities",
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "import_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column(
            "imported_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("row_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("accepted", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rejected", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duplicates", sa.Integer(), server_default="0", nullable=False),
        sa.Column("review_required", sa.Integer(), server_default="0", nullable=False),
        sa.Column("imported_by", sa.String(length=64), server_default="system", nullable=False),
        sa.CheckConstraint("filename <> ''", name=op.f("ck_import_batches_filename_not_blank")),
        sa.CheckConstraint(
            "row_count >= 0", name=op.f("ck_import_batches_row_count_non_negative")
        ),
        sa.CheckConstraint("accepted >= 0", name=op.f("ck_import_batches_accepted_non_negative")),
        sa.CheckConstraint("rejected >= 0", name=op.f("ck_import_batches_rejected_non_negative")),
        sa.CheckConstraint(
            "duplicates >= 0", name=op.f("ck_import_batches_duplicates_non_negative")
        ),
        sa.CheckConstraint(
            "review_required >= 0",
            name=op.f("ck_import_batches_review_required_non_negative"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_import_batches")),
    )

    op.create_table(
        "lead_provenance",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("import_batch_id", sa.Uuid(), nullable=True),
        sa.Column("row_number", sa.Integer(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("collection_date", sa.Date(), nullable=True),
        sa.Column("collection_method", sa.String(length=255), nullable=True),
        sa.Column("intended_purpose", sa.Text(), nullable=True),
        sa.Column("contact_type", sa.String(length=32), server_default="unknown", nullable=False),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.CheckConstraint(
            "contact_type IN ('unknown', 'generic_business', 'named_individual')",
            name=op.f("ck_lead_provenance_contact_type_valid"),
        ),
        sa.CheckConstraint(
            "row_number IS NULL OR row_number >= 2",
            name=op.f("ck_lead_provenance_row_number_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["import_batch_id"],
            ["import_batches.id"],
            name=op.f("fk_lead_provenance_import_batch_id_import_batches"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["leads.id"],
            name=op.f("fk_lead_provenance_lead_id_leads"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lead_provenance")),
        sa.UniqueConstraint("lead_id", name=op.f("uq_lead_provenance_lead_id")),
    )

    op.create_table(
        "lead_channel_eligibility",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column(
            "state", sa.String(length=16), server_default="needs_review", nullable=False
        ),
        sa.Column("lawful_basis", sa.String(length=32), nullable=True),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("evidence_source", sa.Text(), nullable=True),
        sa.Column("intended_purpose", sa.Text(), nullable=True),
        sa.Column("contact_context", sa.Text(), nullable=True),
        sa.Column("reviewer", sa.String(length=64), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "channel IN ('email', 'sms', 'whatsapp')",
            name=op.f("ck_lead_channel_eligibility_channel_valid"),
        ),
        sa.CheckConstraint(
            "state IN ('needs_review', 'eligible')",
            name=op.f("ck_lead_channel_eligibility_eligibility_state_valid"),
        ),
        sa.CheckConstraint(
            "lawful_basis IS NULL OR lawful_basis IN "
            "('consent', 'contract', 'legal_obligation', 'vital_interests', "
            "'public_task', 'legitimate_interests', 'other')",
            name=op.f("ck_lead_channel_eligibility_lawful_basis_valid"),
        ),
        sa.CheckConstraint(
            "state <> 'eligible' OR ("
            "lawful_basis IS NOT NULL AND evidence_summary IS NOT NULL AND "
            "evidence_source IS NOT NULL AND intended_purpose IS NOT NULL AND "
            "contact_context IS NOT NULL AND reviewer IS NOT NULL AND "
            "reviewed_at IS NOT NULL AND rationale IS NOT NULL)",
            name=op.f("ck_lead_channel_eligibility_eligible_review_complete"),
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["leads.id"],
            name=op.f("fk_lead_channel_eligibility_lead_id_leads"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lead_channel_eligibility")),
        sa.UniqueConstraint(
            "lead_id",
            "channel",
            name="uq_lead_channel_eligibility_lead_channel",
        ),
    )

    op.create_table(
        "suppressions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("contact_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("contact_kind", sa.String(length=16), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("recorded_by", sa.String(length=64), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "contact_kind IN ('phone', 'email')",
            name=op.f("ck_suppressions_contact_kind_valid"),
        ),
        sa.CheckConstraint(
            "scope IN ('all_marketing', 'email', 'sms', 'whatsapp')",
            name=op.f("ck_suppressions_scope_valid"),
        ),
        sa.CheckConstraint(
            "reason IN ('opt_out', 'objection', 'manual_restriction')",
            name=op.f("ck_suppressions_reason_valid"),
        ),
        sa.CheckConstraint("source <> ''", name=op.f("ck_suppressions_source_not_blank")),
        sa.CheckConstraint(
            "recorded_by <> ''", name=op.f("ck_suppressions_recorded_by_not_blank")
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["leads.id"],
            name=op.f("fk_suppressions_lead_id_leads"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_suppressions")),
        sa.UniqueConstraint(
            "contact_fingerprint",
            "scope",
            name="uq_suppression_contact_scope",
        ),
    )
    op.create_index(
        "ix_suppressions_contact_fingerprint",
        "suppressions",
        ["contact_fingerprint"],
        unique=False,
    )

    # Existing leads were never reviewed. Every channel starts pending and
    # suppression remains a separate, terminal layer.
    op.execute(
        """
        INSERT INTO lead_channel_eligibility (id, lead_id, channel, state)
        SELECT gen_random_uuid(), leads.id, channel, 'needs_review'
        FROM leads
        CROSS JOIN (VALUES ('email'), ('sms'), ('whatsapp')) AS channels(channel)
        """
    )


def downgrade() -> None:
    op.drop_index("ix_suppressions_contact_fingerprint", table_name="suppressions")
    op.drop_table("suppressions")
    op.drop_table("lead_channel_eligibility")
    op.drop_table("lead_provenance")
    op.drop_table("import_batches")
    op.drop_column("activities", "details")
    op.drop_index("ix_leads_email", table_name="leads")
    op.drop_column("leads", "email")
