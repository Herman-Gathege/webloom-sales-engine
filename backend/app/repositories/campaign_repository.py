"""Data access for Sprint 5 campaigns and draft records."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Campaign,
    CampaignEvent,
    CampaignLead,
    Lead,
    MessageTemplate,
    Offer,
    Outreach,
)


class CampaignRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_campaign(self, campaign: Campaign) -> Campaign:
        self.session.add(campaign)
        return campaign

    def add_campaign_lead(self, campaign_lead: CampaignLead) -> CampaignLead:
        self.session.add(campaign_lead)
        return campaign_lead

    def add_outreach(self, outreach: Outreach) -> Outreach:
        self.session.add(outreach)
        return outreach

    def add_event(self, event: CampaignEvent) -> CampaignEvent:
        self.session.add(event)
        return event

    def get_offer(self, offer_id: uuid.UUID) -> Offer | None:
        return self.session.get(Offer, offer_id)

    def get_template(self, template_id: uuid.UUID) -> MessageTemplate | None:
        return self.session.get(MessageTemplate, template_id)

    def get_campaign(
        self,
        campaign_id: uuid.UUID,
        *,
        include_history: bool = False,
        for_update: bool = False,
    ) -> Campaign | None:
        statement = select(Campaign).where(Campaign.id == campaign_id)
        if for_update:
            statement = statement.with_for_update()
        options = [
            selectinload(Campaign.offer),
            selectinload(Campaign.template),
            selectinload(Campaign.owner),
            selectinload(Campaign.archived_by),
            selectinload(Campaign.selected_leads).selectinload(CampaignLead.lead),
        ]
        if include_history:
            options.extend(
                [
                    selectinload(Campaign.outreaches).selectinload(Outreach.lead),
                    selectinload(Campaign.events).selectinload(CampaignEvent.actor),
                ]
            )
        return self.session.scalar(statement.options(*options))

    def list_campaigns(self, *, include_archived: bool) -> list[Campaign]:
        statement = (
            select(Campaign)
            .options(
                selectinload(Campaign.offer),
                selectinload(Campaign.template),
                selectinload(Campaign.owner),
                selectinload(Campaign.archived_by),
                selectinload(Campaign.selected_leads),
                selectinload(Campaign.outreaches),
            )
            .order_by(Campaign.created_at.desc(), Campaign.id.desc())
        )
        if not include_archived:
            statement = statement.where(Campaign.archived_at.is_(None))
        return list(self.session.scalars(statement).all())

    def get_leads(self, lead_ids: list[uuid.UUID]) -> list[Lead]:
        if not lead_ids:
            return []
        statement = (
            select(Lead)
            .where(Lead.id.in_(lead_ids))
            .options(
                selectinload(Lead.provenance),
                selectinload(Lead.eligibility),
                selectinload(Lead.compliance),
            )
            .order_by(Lead.created_at.desc(), Lead.id.desc())
        )
        return list(self.session.scalars(statement).all())

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
