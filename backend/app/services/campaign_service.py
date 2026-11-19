"""Campaign preparation, eligibility preview and immutable draft generation."""

import hashlib
import json
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.models import (
    Campaign,
    CampaignEvent,
    CampaignLead,
    CampaignLeadOutcome,
    Lead,
    MessageTemplate,
    Offer,
    Outreach,
    OutreachState,
    TemplateChannel,
    User,
    UserRole,
)
from app.repositories import CampaignRepository, LeadRepository
from app.schemas.campaign import (
    CampaignDetailRead,
    CampaignDraftRead,
    CampaignEventRead,
    CampaignInput,
    CampaignListRead,
    CampaignPreviewLeadRead,
    CampaignPreviewRead,
    CampaignSkipRead,
    CampaignSummaryRead,
    CampaignUpdate,
)
from app.services.draft_renderer import RenderFailure, render_draft, sms_metrics
from app.services.outreach_gate import OutreachGateResult, OutreachGateService


class CampaignNotFoundError(Exception):
    pass


class CampaignValidationError(Exception):
    pass


class CampaignConflictError(Exception):
    pass


class CampaignPermissionError(Exception):
    pass


class CampaignService:
    def __init__(
        self,
        campaigns: CampaignRepository,
        leads: LeadRepository,
    ) -> None:
        self.campaigns = campaigns
        self.leads = leads
        self.gate = OutreachGateService(leads)

    def list_campaigns(self, *, include_archived: bool) -> CampaignListRead:
        rows = self.campaigns.list_campaigns(include_archived=include_archived)
        return CampaignListRead(
            items=[self._summary(campaign) for campaign in rows]
        )

    def get_campaign(self, campaign_id: uuid.UUID) -> CampaignDetailRead:
        campaign = self.campaigns.get_campaign(campaign_id, include_history=True)
        if campaign is None:
            raise CampaignNotFoundError("Campaign not found.")
        return self._detail(campaign)

    def preview(self, values: CampaignInput, *, actor: User) -> CampaignPreviewRead:
        offer, template = self._validate_inputs(
            values.offer_id,
            values.template_id,
            values.channel,
        )
        leads = self._validate_leads(values.lead_ids)
        results = {
            result.lead_id: result
            for result in self.gate.check_many(
                values.lead_ids,
                values.channel.value,
                actor=actor.email,
            )
        }
        eligible: list[CampaignPreviewLeadRead] = []
        skipped: list[CampaignSkipRead] = []
        reason_counts: dict[str, int] = {}

        for lead in leads:
            result = results[lead.id]
            if result.allowed:
                rendered, failure = render_draft(template, lead, offer)
                if failure is not None:
                    skip = self._render_skip(lead, failure)
                else:
                    eligible.append(
                        CampaignPreviewLeadRead(
                            lead_id=lead.id,
                            business_name=lead.business_name,
                            sector=lead.sector,
                            area=lead.area,
                            source=lead.source,
                            website_presence=lead.website_presence,
                            decision_type=result.decision_type,
                            explanation=result.explanation,
                            policy_id=result.policy_id,
                            policy_version=result.policy_version,
                            technical_available=result.technical_available,
                            **self._research_metadata(lead),
                        )
                    )
                    continue
            else:
                skip = self._eligibility_skip(lead, result)
            skipped.append(skip)
            reason_counts[skip.label] = reason_counts.get(skip.label, 0) + 1

        return CampaignPreviewRead(
            eligible_count=len(eligible),
            skipped_count=len(skipped),
            eligible=eligible,
            skipped=skipped,
            reason_counts=reason_counts,
        )

    def create(self, values: CampaignInput, *, actor: User) -> CampaignDetailRead:
        offer, template = self._validate_inputs(
            values.offer_id,
            values.template_id,
            values.channel,
        )
        leads = self._validate_leads(values.lead_ids)
        offer_snapshot, template_snapshot = self._snapshots(offer, template)
        campaign = Campaign(
            name=values.name,
            goal=values.goal,
            offer_id=offer.id,
            template_id=template.id,
            channel=values.channel.value,
            owner_id=actor.id,
            selected_count=len(leads),
            offer_snapshot=offer_snapshot,
            template_snapshot=template_snapshot,
            selection_context=values.selection_context.model_dump(
                mode="json", exclude_none=True
            ),
            input_fingerprint=self._fingerprint(offer_snapshot, template_snapshot),
        )
        campaign.selected_leads = [
            CampaignLead(lead_id=lead.id, outcome=CampaignLeadOutcome.PENDING.value)
            for lead in leads
        ]
        campaign.events.append(
            CampaignEvent(
                actor_id=actor.id,
                event_type="campaign.created",
                details={"selected_count": len(leads), "channel": values.channel.value},
                created_at=datetime.now(UTC),
            )
        )
        self.campaigns.add_campaign(campaign)
        self.campaigns.commit()
        return self.get_campaign(campaign.id)

    def update(
        self,
        campaign_id: uuid.UUID,
        values: CampaignUpdate,
        *,
        actor: User,
    ) -> CampaignDetailRead:
        campaign = self._get_mutable_campaign(campaign_id, actor=actor)
        offer, template = self._validate_inputs(
            values.offer_id,
            values.template_id,
            values.channel,
        )
        leads = self._validate_leads(values.lead_ids)
        offer_snapshot, template_snapshot = self._snapshots(offer, template)

        campaign.name = values.name
        campaign.goal = values.goal
        campaign.offer_id = offer.id
        campaign.template_id = template.id
        campaign.channel = values.channel.value
        campaign.selected_count = len(leads)
        campaign.offer_snapshot = offer_snapshot
        campaign.template_snapshot = template_snapshot
        campaign.selection_context = values.selection_context.model_dump(
            mode="json", exclude_none=True
        )
        campaign.input_fingerprint = self._fingerprint(
            offer_snapshot, template_snapshot
        )
        desired_ids = {lead.id for lead in leads}
        retained = {row.lead_id: row for row in campaign.selected_leads}
        for row in list(campaign.selected_leads):
            if row.lead_id not in desired_ids:
                campaign.selected_leads.remove(row)
        for lead in leads:
            row = retained.get(lead.id)
            if row is None:
                campaign.selected_leads.append(
                    CampaignLead(
                        lead_id=lead.id,
                        outcome=CampaignLeadOutcome.PENDING.value,
                    )
                )
                continue
            row.outcome = CampaignLeadOutcome.PENDING.value
            row.skip_code = None
            row.skip_label = None
            row.skip_explanation = None
            row.eligibility_snapshot = None
            row.evaluated_at = None
        campaign.events.append(
            CampaignEvent(
                actor_id=actor.id,
                event_type="campaign.updated",
                details={"selected_count": len(leads), "channel": values.channel.value},
                created_at=datetime.now(UTC),
            )
        )
        self.campaigns.commit()
        return self.get_campaign(campaign.id)

    def generate(
        self, campaign_id: uuid.UUID, *, actor: User
    ) -> CampaignDetailRead:
        campaign = self._get_campaign_for_mutation(campaign_id, actor=actor)
        if campaign.archived_at is not None:
            raise CampaignConflictError("Restore the campaign before generating drafts.")
        if campaign.generated_at is not None:
            return self._detail(campaign)

        offer = self.campaigns.get_offer(campaign.offer_id)
        template = self.campaigns.get_template(campaign.template_id)
        if offer is None or template is None:
            raise CampaignConflictError(
                "The campaign catalogue record no longer exists. Create a new campaign."
            )
        try:
            channel = TemplateChannel(campaign.channel)
        except ValueError as exc:  # pragma: no cover - constrained at creation
            raise CampaignValidationError("Unsupported campaign channel.") from exc
        self._validate_inputs(offer.id, template.id, channel)
        current_offer, current_template = self._snapshots(offer, template)
        current_fingerprint = self._fingerprint(current_offer, current_template)
        if current_fingerprint != campaign.input_fingerprint:
            raise CampaignConflictError(
                "The offer or template changed after this campaign was created. "
                "Create a fresh campaign and preview it again."
            )

        lead_ids = [row.lead_id for row in campaign.selected_leads]
        results = {
            result.lead_id: result
            for result in self.gate.check_many(
                lead_ids,
                campaign.channel,
                actor=actor.email,
                commit=False,
            )
        }
        campaign = self.campaigns.get_campaign(
            campaign_id, include_history=True, for_update=True
        )
        if campaign is None:  # pragma: no cover - locked above
            raise CampaignNotFoundError("Campaign not found.")

        lead_map = {row.lead_id: row.lead for row in campaign.selected_leads}
        generated_at = datetime.now(UTC)
        drafted = 0
        skipped = 0
        try:
            for campaign_lead in campaign.selected_leads:
                lead = lead_map[campaign_lead.lead_id]
                result = results[campaign_lead.lead_id]
                campaign_lead.eligibility_snapshot = self._eligibility_snapshot(
                    result, lead
                )
                campaign_lead.evaluated_at = result.evaluated_at

                if not result.allowed:
                    skip = self._eligibility_skip(lead, result)
                    self._apply_skip(campaign_lead, skip)
                    skipped += 1
                    continue

                rendered, failure = render_draft(template, lead, offer)
                if failure is not None:
                    self._apply_skip(campaign_lead, self._render_skip(lead, failure))
                    skipped += 1
                    continue

                metrics = sms_metrics(rendered) if campaign.channel == "sms" else None
                outreach = Outreach(
                    campaign_id=campaign.id,
                    campaign_lead_id=campaign_lead.id,
                    lead_id=lead.id,
                    offer_id=offer.id,
                    template_id=template.id,
                    channel=campaign.channel,
                    state=OutreachState.DRAFT.value,
                    rendered_body=rendered,
                    offer_snapshot=campaign.offer_snapshot,
                    template_snapshot=campaign.template_snapshot,
                    eligibility_snapshot=campaign_lead.eligibility_snapshot,
                    sms_encoding=metrics.encoding if metrics else None,
                    sms_characters=metrics.characters if metrics else None,
                    sms_units=metrics.units if metrics else None,
                    sms_segments=metrics.segments if metrics else None,
                    generated_at=generated_at,
                )
                campaign_lead.outcome = CampaignLeadOutcome.DRAFTED.value
                campaign_lead.skip_code = None
                campaign_lead.skip_label = None
                campaign_lead.skip_explanation = None
                campaign.outreaches.append(outreach)
                drafted += 1

            campaign.generated_at = generated_at
            campaign.events.append(
                CampaignEvent(
                    actor_id=actor.id,
                    event_type="campaign.generated",
                    details={"drafted": drafted, "skipped": skipped},
                    created_at=generated_at,
                )
            )
            self.campaigns.commit()
        except IntegrityError as exc:
            self.campaigns.rollback()
            raise CampaignConflictError(
                "Draft generation conflicted with another request."
            ) from exc
        except Exception:
            self.campaigns.rollback()
            raise
        return self.get_campaign(campaign.id)

    def archive(
        self, campaign_id: uuid.UUID, *, actor: User
    ) -> CampaignDetailRead:
        campaign = self._get_campaign_for_mutation(campaign_id, actor=actor)
        if campaign.archived_at is None:
            archived_at = datetime.now(UTC)
            campaign.archived_at = archived_at
            campaign.archived_by_id = actor.id
            campaign.events.append(
                CampaignEvent(
                    actor_id=actor.id,
                    event_type="campaign.archived",
                    created_at=archived_at,
                )
            )
            self.campaigns.commit()
        return self.get_campaign(campaign.id)

    def restore(
        self, campaign_id: uuid.UUID, *, actor: User
    ) -> CampaignDetailRead:
        campaign = self._get_campaign_for_mutation(campaign_id, actor=actor)
        if campaign.archived_at is not None:
            restored_at = datetime.now(UTC)
            campaign.archived_at = None
            campaign.archived_by_id = None
            campaign.events.append(
                CampaignEvent(
                    actor_id=actor.id,
                    event_type="campaign.restored",
                    created_at=restored_at,
                )
            )
            self.campaigns.commit()
        return self.get_campaign(campaign.id)

    def _validate_inputs(
        self,
        offer_id: uuid.UUID,
        template_id: uuid.UUID,
        channel: TemplateChannel,
    ) -> tuple[Offer, MessageTemplate]:
        offer = self.campaigns.get_offer(offer_id)
        template = self.campaigns.get_template(template_id)
        if offer is None or not offer.is_active:
            raise CampaignValidationError("Choose an active offer.")
        if template is None or not template.is_active:
            raise CampaignValidationError("Choose an active template.")
        if template.offer_id != offer.id:
            raise CampaignValidationError("The selected template belongs to another offer.")
        if template.channel != channel:
            raise CampaignValidationError("The selected template uses another channel.")
        return offer, template

    def _validate_leads(self, lead_ids: list[uuid.UUID]) -> list[Lead]:
        if not 1 <= len(lead_ids) <= 200:
            raise CampaignValidationError("Select between 1 and 200 leads.")
        if len(lead_ids) != len(set(lead_ids)):
            raise CampaignValidationError("Select each lead only once.")
        leads = self.campaigns.get_leads(lead_ids)
        if len(leads) != len(lead_ids):
            raise CampaignNotFoundError("One or more selected leads no longer exist.")
        position = {lead_id: index for index, lead_id in enumerate(lead_ids)}
        return sorted(leads, key=lambda lead: position[lead.id])

    def _get_campaign_for_mutation(
        self, campaign_id: uuid.UUID, *, actor: User
    ) -> Campaign:
        campaign = self.campaigns.get_campaign(
            campaign_id, include_history=True, for_update=True
        )
        if campaign is None:
            raise CampaignNotFoundError("Campaign not found.")
        self._require_mutation(campaign, actor)
        return campaign

    def _get_mutable_campaign(
        self, campaign_id: uuid.UUID, *, actor: User
    ) -> Campaign:
        campaign = self.campaigns.get_campaign(
            campaign_id, include_history=True, for_update=True
        )
        if campaign is None:
            raise CampaignNotFoundError("Campaign not found.")
        self._require_mutation(campaign, actor)
        if campaign.archived_at is not None:
            raise CampaignConflictError("Restore the campaign before changing it.")
        if campaign.generated_at is not None:
            raise CampaignConflictError("Generated campaigns are immutable.")
        return campaign

    @staticmethod
    def _require_mutation(campaign: Campaign, actor: User) -> None:
        if actor.role is not UserRole.ADMIN and campaign.owner_id != actor.id:
            raise CampaignPermissionError(
                "Only the campaign creator or an administrator can change this campaign."
            )

    @staticmethod
    def _snapshots(
        offer: Offer, template: MessageTemplate
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        offer_snapshot = {
            "id": str(offer.id),
            "name": offer.name,
            "slug": offer.slug,
            "description": offer.description,
            "price_min": (
                f"{Decimal(offer.price_min):.2f}"
                if offer.price_min is not None
                else None
            ),
            "price_max": (
                f"{Decimal(offer.price_max):.2f}"
                if offer.price_max is not None
                else None
            ),
            "currency": offer.currency,
            "pitch_angle": offer.pitch_angle,
            "is_active": offer.is_active,
            "updated_at": offer.updated_at.isoformat(),
        }
        template_snapshot = {
            "id": str(template.id),
            "offer_id": str(template.offer_id),
            "channel": template.channel.value,
            "name": template.name,
            "variant": template.variant,
            "body": template.body,
            "variables": list(template.variables),
            "is_active": template.is_active,
            "updated_at": template.updated_at.isoformat(),
        }
        return offer_snapshot, template_snapshot

    @staticmethod
    def _fingerprint(
        offer_snapshot: dict[str, Any], template_snapshot: dict[str, Any]
    ) -> str:
        payload = {"offer": offer_snapshot, "template": template_snapshot}
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode()).hexdigest()

    def _eligibility_snapshot(
        self, result: OutreachGateResult, lead: Lead
    ) -> dict[str, object]:
        return {
            "allowed": result.allowed,
            "compliance_status": result.compliance_status,
            "channel_status": result.channel_status,
            "technical_available": result.technical_available,
            "decision_current": result.decision_current,
            "decision_type": result.decision_type,
            "policy_id": result.policy_id,
            "policy_version": result.policy_version,
            "policy_fingerprint": result.policy_fingerprint,
            "policy_approved_by": result.policy_approved_by,
            "policy_approval_reference": result.policy_approval_reference,
            "evidence_references": result.evidence_references,
            "input_fingerprint": result.input_fingerprint,
            "reason_codes": result.reason_codes,
            "explanation": result.explanation,
            "evaluated_at": result.evaluated_at.isoformat(),
            **self._research_metadata(lead),
        }

    @staticmethod
    def _apply_skip(campaign_lead: CampaignLead, skip: CampaignSkipRead) -> None:
        campaign_lead.outcome = CampaignLeadOutcome.SKIPPED.value
        campaign_lead.skip_code = skip.code
        campaign_lead.skip_label = skip.label
        campaign_lead.skip_explanation = skip.explanation

    def _eligibility_skip(
        self, lead: Lead, result: OutreachGateResult
    ) -> CampaignSkipRead:
        reasons = set(result.reason_codes)
        phone = lead.phone or ""
        if result.channel_status == "blocked" or any(
            "suppressed" in reason or "opted_out" in reason
            for reason in reasons
        ):
            label = "Opted out or restricted"
            explanation = "A terminal restriction excludes this lead from SMS outreach."
            code = "suppressed"
        elif any(reason.startswith("review_stale") for reason in reasons):
            label = "Eligibility review is stale"
            explanation = "The contact or evidence changed after the previous review."
            code = "review_stale"
        elif not result.technical_available:
            if (
                phone.startswith("+254")
                and len(phone) > 4
                and phone[4] in "23456"
            ):
                label = "Landline only"
                explanation = "SMS cannot be delivered to this landline number."
            else:
                label = "No usable SMS number"
                explanation = "This lead does not have a usable SMS contact."
            code = "technical_unavailable"
        elif any(
            reason.startswith("missing_provenance")
            or reason.startswith("incomplete_provenance")
            for reason in reasons
        ):
            label = "Source information incomplete"
            explanation = "Add the required source context before this lead can proceed."
            code = "provenance_incomplete"
        elif result.channel_status == "needs_review":
            label = "Needs review"
            explanation = "SMS needs a current policy match or complete human review."
            code = "needs_review"
        else:
            label = "Not eligible for SMS"
            explanation = result.explanation
            code = "ineligible"
        return CampaignSkipRead(
            lead_id=lead.id,
            business_name=lead.business_name,
            code=code,
            label=label,
            explanation=explanation,
            reason_codes=result.reason_codes,
        )

    @staticmethod
    def _render_skip(lead: Lead, failure: RenderFailure) -> CampaignSkipRead:
        label = (
            "Price guidance missing"
            if "price_range" in failure.code
            else "Template data missing"
        )
        return CampaignSkipRead(
            lead_id=lead.id,
            business_name=lead.business_name,
            code=failure.code,
            label=label,
            explanation=failure.message,
            reason_codes=[failure.code],
        )

    def _summary(self, campaign: Campaign) -> CampaignSummaryRead:
        drafted = sum(
            row.outcome == CampaignLeadOutcome.DRAFTED.value
            for row in campaign.selected_leads
        )
        skipped = sum(
            row.outcome == CampaignLeadOutcome.SKIPPED.value
            for row in campaign.selected_leads
        )
        return CampaignSummaryRead(
            id=campaign.id,
            name=campaign.name,
            goal=campaign.goal,
            channel=TemplateChannel(campaign.channel),
            owner_id=campaign.owner_id,
            owner_email=campaign.owner.email,
            offer_id=campaign.offer_id,
            offer_name=campaign.offer.name,
            template_id=campaign.template_id,
            template_name=campaign.template.name,
            selected_count=campaign.selected_count,
            draft_count=drafted,
            skip_count=skipped,
            status=self._status(campaign),
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            last_activity_at=campaign.updated_at,
            generated_at=campaign.generated_at,
            archived_at=campaign.archived_at,
            archived_by_email=(
                campaign.archived_by.email if campaign.archived_by is not None else None
            ),
        )

    def _detail(self, campaign: Campaign) -> CampaignDetailRead:
        summary = self._summary(campaign)
        drafts = [
            CampaignDraftRead(
                id=row.id,
                lead_id=row.lead_id,
                business_name=row.lead.business_name,
                sector=row.lead.sector,
                area=row.lead.area,
                channel=TemplateChannel(row.channel),
                state="draft",
                rendered_body=row.rendered_body,
                sms_encoding=row.sms_encoding,
                sms_characters=row.sms_characters,
                sms_units=row.sms_units,
                sms_segments=row.sms_segments,
                eligibility_snapshot=row.eligibility_snapshot,
                template_snapshot=row.template_snapshot,
                offer_snapshot=row.offer_snapshot,
                generated_at=row.generated_at,
                research_date=(
                    date.fromisoformat(str(row.eligibility_snapshot["research_date"]))
                    if row.eligibility_snapshot
                    and row.eligibility_snapshot.get("research_date")
                    else None
                ),
                research_stale=bool(
                    (row.eligibility_snapshot or {}).get("research_stale", False)
                ),
            )
            for row in campaign.outreaches
        ]
        skips = [
            CampaignSkipRead(
                lead_id=row.lead_id,
                business_name=row.lead.business_name,
                code=row.skip_code or "skipped",
                label=row.skip_label or "Skipped",
                explanation=row.skip_explanation or "This lead was skipped.",
                reason_codes=[
                    str(value)
                    for value in (
                        row.eligibility_snapshot or {}
                    ).get("reason_codes", [])
                ],
            )
            for row in campaign.selected_leads
            if row.outcome == CampaignLeadOutcome.SKIPPED.value
        ]
        return CampaignDetailRead(
            **summary.model_dump(),
            offer_snapshot=campaign.offer_snapshot,
            template_snapshot=campaign.template_snapshot,
            input_fingerprint=campaign.input_fingerprint,
            selection_context=campaign.selection_context,
            selected_lead_ids=[row.lead_id for row in campaign.selected_leads],
            drafts=drafts,
            skips=skips,
            events=[
                CampaignEventRead(
                    event_type=event.event_type,
                    actor_email=event.actor.email if event.actor else None,
                    details=event.details,
                    created_at=event.created_at,
                )
                for event in campaign.events
            ],
        )

    @staticmethod
    def _status(campaign: Campaign) -> str:
        if campaign.archived_at is not None:
            return "archived"
        if campaign.generated_at is not None:
            return "generated"
        return "draft"

    @staticmethod
    def _research_metadata(lead: Lead) -> dict[str, object]:
        collected = lead.provenance.collection_date if lead.provenance else None
        return {
            "research_date": collected.isoformat() if collected else None,
            "research_stale": bool(
                collected is None or collected < date.today() - timedelta(days=90)
            ),
        }
