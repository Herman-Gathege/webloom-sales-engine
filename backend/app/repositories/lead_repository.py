"""Data access for leads. The only place that writes queries for them."""

import uuid
from collections.abc import Iterable

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session, aliased, selectinload

from app.models import (
    Activity,
    ImportBatch,
    Lead,
    LeadChannelEligibility,
    LeadComplianceEvaluation,
    LeadProvenance,
    Suppression,
)


class LeadRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_leads(
        self,
        *,
        limit: int,
        offset: int,
        q: str | None = None,
        sector: str | None = None,
        area: str | None = None,
        source: str | None = None,
        website: str | None = None,
        lead_status: str | None = None,
        compliance_status: str | None = None,
        data_quality_status: str | None = None,
        provenance: str | None = None,
        outreach_ready: bool | None = None,
        has_suppression: bool | None = None,
        batch_id: uuid.UUID | None = None,
        sort: str = "newest",
    ) -> tuple[list[Lead], int]:
        """One filtered page of leads and the count after filters, before paging."""
        provenance_join = aliased(LeadProvenance)
        base = (
            select(Lead)
            .outerjoin(LeadComplianceEvaluation, LeadComplianceEvaluation.lead_id == Lead.id)
            .outerjoin(provenance_join, provenance_join.lead_id == Lead.id)
        )
        conditions = []

        if q:
            escaped = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            if escaped:
                pattern = f"%{escaped}%"
                conditions.append(
                    or_(
                        Lead.business_name.ilike(pattern, escape="\\"),
                        Lead.phone.ilike(pattern, escape="\\"),
                        Lead.email.ilike(pattern, escape="\\"),
                        Lead.area.ilike(pattern, escape="\\"),
                        Lead.sector.ilike(pattern, escape="\\"),
                        Lead.source.ilike(pattern, escape="\\"),
                    )
                )
        if sector:
            conditions.append(Lead.sector == sector)
        if area:
            conditions.append(Lead.area == area)
        if source:
            conditions.append(Lead.source == source)
        if website == "yes":
            conditions.append(Lead.has_website.is_(True))
        elif website == "no":
            conditions.append(Lead.has_website.is_(False))
        if lead_status:
            conditions.append(Lead.status == lead_status)
        if compliance_status:
            conditions.append(LeadComplianceEvaluation.status == compliance_status)
        if data_quality_status:
            conditions.append(
                LeadComplianceEvaluation.data_quality_status == data_quality_status
            )
        if provenance == "missing":
            conditions.append(provenance_join.id.is_(None))
        elif provenance == "available":
            conditions.append(provenance_join.id.is_not(None))
            conditions.append(
                or_(
                    func.coalesce(provenance_join.source_name, "") != "",
                    func.coalesce(provenance_join.source_url, "") != "",
                    func.coalesce(provenance_join.collection_method, "") != "",
                )
            )
        elif provenance == "incomplete":
            conditions.append(provenance_join.id.is_not(None))
            conditions.append(
                func.coalesce(provenance_join.source_name, "") == ""
            )
            conditions.append(
                func.coalesce(provenance_join.source_url, "") == ""
            )
            conditions.append(
                func.coalesce(provenance_join.collection_method, "") == ""
            )
        if outreach_ready is not None:
            conditions.append(LeadComplianceEvaluation.outreach_ready.is_(outreach_ready))
        if has_suppression is not None:
            has_rows = (
                func.coalesce(
                    func.jsonb_array_length(
                        LeadComplianceEvaluation.suppressed_channels
                    ),
                    0,
                )
                > 0
            )
            conditions.append(has_rows if has_suppression else ~has_rows)
        if batch_id is not None:
            conditions.append(provenance_join.import_batch_id == batch_id)

        if conditions:
            base = base.where(*conditions)

        total = (
            self.session.scalar(select(func.count()).select_from(base.subquery())) or 0
        )

        if sort == "oldest":
            ordering = (Lead.created_at.asc(), Lead.id.asc())
        elif sort == "business_name":
            ordering = (func.lower(Lead.business_name).asc(), Lead.id.asc())
        elif sort == "compliance_status":
            status_order = case(
                (LeadComplianceEvaluation.status == "eligible", 0),
                (LeadComplianceEvaluation.status == "needs_review", 1),
                (LeadComplianceEvaluation.status == "blocked", 2),
                (LeadComplianceEvaluation.status == "invalid", 3),
                else_=4,
            )
            ordering = (status_order, Lead.created_at.desc(), Lead.id.desc())
        else:
            ordering = (Lead.created_at.desc(), Lead.id.desc())

        statement = (
            base.options(
                selectinload(Lead.compliance),
                selectinload(Lead.provenance),
                selectinload(Lead.eligibility),
            )
            .order_by(*ordering)
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(statement).all()), total

    def get(self, lead_id: uuid.UUID) -> Lead | None:
        return self.session.get(Lead, lead_id)

    def get_with_activity(self, lead_id: uuid.UUID) -> Lead | None:
        """The lead and its history in two queries rather than one per row."""
        statement = (
            select(Lead)
            .where(Lead.id == lead_id)
            .options(
                selectinload(Lead.activity),
                selectinload(Lead.provenance),
                selectinload(Lead.eligibility),
                selectinload(Lead.compliance),
            )
        )
        lead = self.session.scalar(statement)
        if lead is None:
            return None
        fingerprints = self._lead_fingerprints(lead)
        lead._matching_suppressions = self.suppressions_for_fingerprints(
            fingerprints, lead_id=lead.id
        )
        return lead

    def filter_options(self) -> dict[str, object]:
        """Distinct values available to the Lead Desk filters."""

        def distinct(column, *, non_blank: bool = True):
            condition = column.is_not(None)
            if non_blank:
                condition = condition & (column != "")
            rows = self.session.scalars(
                select(column)
                .where(condition)
                .distinct()
                .order_by(column)
            )
            return list(rows)

        batches = self.session.scalars(
            select(ImportBatch).order_by(ImportBatch.imported_at.desc(), ImportBatch.id.desc())
        ).all()
        return {
            "sectors": distinct(Lead.sector),
            "areas": distinct(Lead.area),
            "sources": distinct(Lead.source),
            "statuses": distinct(Lead.status, non_blank=False),
            "compliance_statuses": ["eligible", "needs_review", "blocked", "invalid"],
            "data_quality_statuses": ["complete", "incomplete", "invalid"],
            "import_batches": [
                {
                    "id": batch.id,
                    "filename": batch.filename,
                    "imported_at": batch.imported_at,
                }
                for batch in batches
            ],
        }

    def find_by_phone(self, phone: str) -> Lead | None:
        return self.session.scalar(select(Lead).where(Lead.phone == phone))

    def existing_phones(self, phones: Iterable[str]) -> set[str]:
        """Which of these numbers we already hold, in one query.

        The importer asks once for a whole file rather than once per row: 52
        row-by-row lookups would be 52 round trips for an answer one query gives.
        """
        wanted = list(phones)
        if not wanted:
            return set()
        rows = self.session.scalars(select(Lead.phone).where(Lead.phone.in_(wanted)))
        return {phone for phone in rows if phone is not None}

    def add(self, lead: Lead) -> Lead:
        self.session.add(lead)
        return lead

    def add_activity(self, activity: Activity) -> Activity:
        self.session.add(activity)
        return activity

    def add_import_batch(self, batch: ImportBatch) -> ImportBatch:
        self.session.add(batch)
        return batch

    def add_provenance(self, provenance: LeadProvenance) -> LeadProvenance:
        self.session.add(provenance)
        return provenance

    def add_eligibility(self, eligibility: LeadChannelEligibility) -> LeadChannelEligibility:
        self.session.add(eligibility)
        return eligibility

    def add_suppression(self, suppression: Suppression) -> Suppression:
        self.session.add(suppression)
        return suppression

    def get_eligibility(
        self, lead_id: uuid.UUID, channel: str
    ) -> LeadChannelEligibility | None:
        return self.session.scalar(
            select(LeadChannelEligibility).where(
                LeadChannelEligibility.lead_id == lead_id,
                LeadChannelEligibility.channel == channel,
            )
        )

    def suppressions_for_fingerprints(
        self,
        fingerprints: Iterable[str],
        *,
        lead_id: uuid.UUID | None = None,
    ) -> list[Suppression]:
        wanted = set(fingerprints)
        if not wanted and lead_id is None:
            return []
        conditions = []
        if wanted:
            conditions.append(Suppression.contact_fingerprint.in_(wanted))
        if lead_id is not None:
            conditions.append(Suppression.lead_id == lead_id)
        statement = (
            select(Suppression)
            .where(or_(*conditions))
            .order_by(Suppression.created_at, Suppression.id)
        )
        return list(self.session.scalars(statement).all())

    def flush(self) -> None:
        self.session.flush()

    def count_activity(self) -> int:
        return self.session.scalar(select(func.count()).select_from(Activity)) or 0

    def commit(self) -> None:
        """Save the unit of work — the importer writes all its accepted rows at once."""
        self.session.commit()

    @staticmethod
    def _lead_fingerprints(lead: Lead) -> set[str]:
        # Imported lazily to keep the repository free of service-level rules.
        from app.services.contact_identity import contact_fingerprint

        fingerprints: set[str] = set()
        if lead.phone:
            fingerprints.add(contact_fingerprint("phone", lead.phone))
        if lead.email:
            fingerprints.add(contact_fingerprint("email", lead.email))
        return fingerprints
