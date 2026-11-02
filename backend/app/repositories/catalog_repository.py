"""Data access for offers and Sales Engine templates."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MessageTemplate, Offer


class CatalogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_offers(self, *, include_inactive: bool) -> list[Offer]:
        statement = select(Offer).order_by(Offer.name, Offer.id)
        if not include_inactive:
            statement = statement.where(Offer.is_active.is_(True))
        return list(self.session.scalars(statement).all())

    def get_offer(self, offer_id: uuid.UUID) -> Offer | None:
        return self.session.get(Offer, offer_id)

    def get_offer_by_slug(self, slug: str) -> Offer | None:
        return self.session.scalar(select(Offer).where(Offer.slug == slug))

    def list_templates(
        self,
        *,
        include_inactive: bool,
        offer_id: uuid.UUID | None = None,
        channel: str | None = None,
    ) -> list[MessageTemplate]:
        statement = select(MessageTemplate).order_by(
            MessageTemplate.name, MessageTemplate.variant, MessageTemplate.id
        )
        if not include_inactive:
            statement = statement.where(MessageTemplate.is_active.is_(True))
        if offer_id is not None:
            statement = statement.where(MessageTemplate.offer_id == offer_id)
        if channel is not None:
            statement = statement.where(MessageTemplate.channel == channel)
        return list(self.session.scalars(statement).all())

    def get_template(self, template_id: uuid.UUID) -> MessageTemplate | None:
        return self.session.get(MessageTemplate, template_id)

    def template_conflict(
        self,
        *,
        offer_id: uuid.UUID,
        channel: str,
        variant: str,
        exclude_id: uuid.UUID | None = None,
    ) -> MessageTemplate | None:
        statement = select(MessageTemplate).where(
            MessageTemplate.offer_id == offer_id,
            MessageTemplate.channel == channel,
            MessageTemplate.variant == variant,
        )
        if exclude_id is not None:
            statement = statement.where(MessageTemplate.id != exclude_id)
        return self.session.scalar(statement)

    def add(self, row: Offer | MessageTemplate):
        self.session.add(row)
        return row

    def commit(self) -> None:
        self.session.commit()
