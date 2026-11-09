"""Business rules for offers and reusable message templates."""

import re
import uuid
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.models import MessageTemplate, Offer, TemplateChannel
from app.repositories.catalog_repository import CatalogRepository

VARIABLE_TOKEN = re.compile(r"\{\{\s*([a-z][a-z0-9_]*)\s*\}\}")
RAW_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
RAW_PHONE = re.compile(
    r"(?<!\d)(?:\+?254|0)(?:[\s().-]*\d){9,12}(?!\d)"
)
ALLOWED_VARIABLES = {
    "business_name",
    "sector",
    "area",
    "website_status",
    "has_website",
    "offer_name",
    "price_range",
    "pitch_angle",
    "opt_out",
}


class CatalogNotFoundError(Exception):
    pass


class CatalogConflictError(Exception):
    pass


class CatalogValidationError(Exception):
    pass


def variables_in_body(body: str) -> list[str]:
    variables = VARIABLE_TOKEN.findall(body)
    remainder = VARIABLE_TOKEN.sub("", body)
    if "{{" in remainder or "}}" in remainder:
        raise CatalogValidationError("Template contains a malformed variable placeholder.")
    return sorted(set(variables))


class CatalogService:
    def __init__(self, repository: CatalogRepository) -> None:
        self.repository = repository

    def list_offers(self, *, include_inactive: bool) -> list[Offer]:
        return self.repository.list_offers(include_inactive=include_inactive)

    def create_offer(self, values: dict[str, Any]) -> Offer:
        if self.repository.get_offer_by_slug(values["slug"]) is not None:
            raise CatalogConflictError("An offer with this slug already exists.")
        offer = Offer(**values)
        self.repository.add(offer)
        self._commit("An offer with this slug already exists.")
        self.repository.session.refresh(offer)
        return offer

    def update_offer(self, offer_id: uuid.UUID, changes: dict[str, Any]) -> Offer:
        offer = self.repository.get_offer(offer_id)
        if offer is None:
            raise CatalogNotFoundError("Offer not found.")
        slug = changes.get("slug")
        if slug and slug != offer.slug and self.repository.get_offer_by_slug(slug):
            raise CatalogConflictError("An offer with this slug already exists.")

        price_min = changes.get("price_min", offer.price_min)
        price_max = changes.get("price_max", offer.price_max)
        if price_min is not None and price_max is not None and price_min > price_max:
            raise CatalogValidationError("Minimum price cannot be greater than maximum price.")
        for key, value in changes.items():
            setattr(offer, key, value)
        self._commit("An offer with this slug already exists.")
        self.repository.session.refresh(offer)
        return offer

    def list_templates(
        self,
        *,
        include_inactive: bool,
        offer_id: uuid.UUID | None = None,
        channel: TemplateChannel | None = None,
    ) -> list[MessageTemplate]:
        if offer_id is not None and self.repository.get_offer(offer_id) is None:
            raise CatalogNotFoundError("Offer not found.")
        return self.repository.list_templates(
            include_inactive=include_inactive,
            offer_id=offer_id,
            channel=channel.value if channel else None,
        )

    def create_template(self, values: dict[str, Any]) -> MessageTemplate:
        offer_id = values["offer_id"]
        if self.repository.get_offer(offer_id) is None:
            raise CatalogNotFoundError("Offer not found.")
        self._validate_template(values)
        self._ensure_no_template_conflict(values)
        template = MessageTemplate(**values)
        self.repository.add(template)
        self._commit("A template with this offer, channel and variant already exists.")
        self.repository.session.refresh(template)
        return template

    def update_template(
        self, template_id: uuid.UUID, changes: dict[str, Any]
    ) -> MessageTemplate:
        template = self.repository.get_template(template_id)
        if template is None:
            raise CatalogNotFoundError("Template not found.")
        merged = {
            "offer_id": changes.get("offer_id", template.offer_id),
            "channel": changes.get("channel", template.channel),
            "variant": changes.get("variant", template.variant),
            "body": changes.get("body", template.body),
            "variables": changes.get("variables", template.variables),
            "is_active": changes.get("is_active", template.is_active),
        }
        if (
            merged["offer_id"] != template.offer_id
            and self.repository.get_offer(merged["offer_id"]) is None
        ):
            raise CatalogNotFoundError("Offer not found.")
        self._validate_template(merged)
        self._ensure_no_template_conflict(merged, exclude_id=template.id)
        for key, value in changes.items():
            setattr(template, key, value)
        self._commit("A template with this offer, channel and variant already exists.")
        self.repository.session.refresh(template)
        return template

    @staticmethod
    def _validate_template(values: dict[str, Any]) -> None:
        body = values["body"].strip()
        if RAW_EMAIL.search(body) or RAW_PHONE.search(body):
            raise CatalogValidationError(
                "Templates cannot contain raw contact details; use lead variables instead."
            )
        detected = variables_in_body(body)
        declared = sorted(set(values.get("variables") or []))
        if detected != declared:
            raise CatalogValidationError(
                "Declared variables must exactly match the placeholders in the body."
            )
        unknown = [value for value in declared if value not in ALLOWED_VARIABLES]
        if unknown:
            raise CatalogValidationError(
                "Unknown template variables: " + ", ".join(unknown) + "."
            )
        if values.get("is_active", True) and "opt_out" not in declared:
            raise CatalogValidationError(
                "Active templates must include the {{opt_out}} variable."
            )

    def _ensure_no_template_conflict(
        self, values: dict[str, Any], *, exclude_id: uuid.UUID | None = None
    ) -> None:
        channel = values["channel"]
        channel_value = channel.value if isinstance(channel, TemplateChannel) else channel
        if (
            self.repository.template_conflict(
                offer_id=values["offer_id"],
                channel=channel_value,
                variant=values["variant"],
                exclude_id=exclude_id,
            )
            is not None
        ):
            raise CatalogConflictError(
                "A template with this offer, channel and variant already exists."
            )

    def _commit(self, conflict_message: str) -> None:
        try:
            self.repository.commit()
        except IntegrityError as exc:
            self.repository.session.rollback()
            raise CatalogConflictError(conflict_message) from exc
