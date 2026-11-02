"""add durable lead compliance evaluation and stale-input fingerprints

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("lead_provenance", sa.Column("source_name", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE lead_provenance
        SET source_name = leads.source
        FROM leads
        WHERE lead_provenance.lead_id = leads.id
          AND lead_provenance.source_name IS NULL
        """
    )
    op.add_column(
        "lead_channel_eligibility",
        sa.Column("reviewed_input_fingerprint", sa.String(length=64), nullable=True),
    )

    for column_name in (
        "matched",
        "eligible",
        "needs_review",
        "blocked",
        "invalid",
        "provenance_incomplete",
    ):
        op.add_column(
            "import_batches",
            sa.Column(column_name, sa.Integer(), server_default="0", nullable=False),
        )
        op.create_check_constraint(
            op.f(f"ck_import_batches_{column_name}_non_negative"),
            "import_batches",
            f"{column_name} >= 0",
        )

    op.create_table(
        "lead_compliance_evaluation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("data_quality_status", sa.String(length=16), nullable=False),
        sa.Column(
            "reason_codes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column(
            "eligible_channels",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "suppressed_channels",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "channel_results",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "outreach_ready",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("rule_version", sa.String(length=32), nullable=False),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "status IN ('eligible', 'needs_review', 'blocked', 'invalid')",
            name=op.f("ck_lead_compliance_evaluation_compliance_status_valid"),
        ),
        sa.CheckConstraint(
            "data_quality_status IN ('complete', 'incomplete', 'invalid')",
            name=op.f("ck_lead_compliance_evaluation_data_quality_status_valid"),
        ),
        sa.CheckConstraint(
            "outreach_ready = (status = 'eligible')",
            name=op.f(
                "ck_lead_compliance_evaluation_outreach_ready_matches_eligible"
            ),
        ),
        sa.CheckConstraint(
            "explanation <> ''",
            name=op.f("ck_lead_compliance_evaluation_explanation_not_blank"),
        ),
        sa.CheckConstraint(
            "rule_version <> ''",
            name=op.f("ck_lead_compliance_evaluation_rule_version_not_blank"),
        ),
        sa.CheckConstraint(
            "length(input_fingerprint) = 64",
            name=op.f("ck_lead_compliance_evaluation_input_fingerprint_length"),
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["leads.id"],
            name=op.f(
                "fk_lead_compliance_evaluation_lead_id_leads"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lead_compliance_evaluation")),
        sa.UniqueConstraint(
            "lead_id",
            name=op.f("uq_lead_compliance_evaluation_lead_id"),
        ),
    )

    # Existing approvals remain visible but deliberately have no reviewed-input
    # fingerprint; the evaluator will require a fresh review before relying on
    # one. This safe backfill never invents provenance or consent.
    op.execute(
        """
        INSERT INTO lead_compliance_evaluation (
            id,
            lead_id,
            status,
            data_quality_status,
            reason_codes,
            explanation,
            eligible_channels,
            suppressed_channels,
            channel_results,
            outreach_ready,
            evaluated_at,
            rule_version,
            input_fingerprint
        )
        SELECT
            gen_random_uuid(),
            leads.id,
            'needs_review',
            CASE
                WHEN leads.phone IS NULL AND leads.email IS NULL THEN 'invalid'
                WHEN NOT EXISTS (
                    SELECT 1
                    FROM lead_provenance
                    WHERE lead_provenance.lead_id = leads.id
                      AND (
                          coalesce(lead_provenance.source_name, '') <> ''
                          OR coalesce(lead_provenance.source_url, '') <> ''
                          OR coalesce(lead_provenance.collection_method, '') <> ''
                      )
                ) THEN 'incomplete'
                ELSE 'complete'
            END,
            CASE
                WHEN leads.phone IS NULL AND leads.email IS NULL
                    THEN '["evaluation_backfill", "no_valid_contact"]'::jsonb
                WHEN NOT EXISTS (
                    SELECT 1
                    FROM lead_provenance
                    WHERE lead_provenance.lead_id = leads.id
                      AND (
                          coalesce(lead_provenance.source_name, '') <> ''
                          OR coalesce(lead_provenance.source_url, '') <> ''
                          OR coalesce(lead_provenance.collection_method, '') <> ''
                      )
                ) THEN '["evaluation_backfill", "missing_provenance"]'::jsonb
                ELSE '["evaluation_backfill"]'::jsonb
            END,
            'Compliance must be evaluated after the durable-evaluation migration.',
            '[]'::jsonb,
            '[]'::jsonb,
            '[]'::jsonb,
            false,
            now(),
            'migration-0004',
            md5(leads.id::text) || md5('lead:' || leads.id::text)
        FROM leads
        """
    )


def downgrade() -> None:
    op.drop_table("lead_compliance_evaluation")

    for column_name in (
        "provenance_incomplete",
        "invalid",
        "blocked",
        "needs_review",
        "eligible",
        "matched",
    ):
        op.drop_constraint(
            op.f(f"ck_import_batches_{column_name}_non_negative"),
            "import_batches",
            type_="check",
        )
        op.drop_column("import_batches", column_name)

    op.drop_column("lead_channel_eligibility", "reviewed_input_fingerprint")
    op.drop_column("lead_provenance", "source_name")
