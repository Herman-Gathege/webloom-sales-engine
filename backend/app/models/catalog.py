"""Commercial offers and reusable Sales Engine message templates."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.database.base import Base


class TemplateChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"


template_channel_type = Enum(
    TemplateChannel,
    name="template_channel",
    native_enum=False,
    length=16,
    validate_strings=True,
    create_constraint=True,
    values_callable=lambda channels: [channel.value for channel in channels],
)


class Offer(Base):
    """Something Webloom can sell."""

    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    price_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    price_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="KES", server_default="KES"
    )
    pitch_angle: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    templates: Mapped[list["MessageTemplate"]] = relationship(
        back_populates="offer",
        order_by="MessageTemplate.created_at, MessageTemplate.id",
    )

    __table_args__ = (
        CheckConstraint("name <> ''", name="name_not_blank"),
        CheckConstraint("slug <> ''", name="slug_not_blank"),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="currency_three_uppercase"),
        CheckConstraint("price_min IS NULL OR price_min >= 0", name="price_min_non_negative"),
        CheckConstraint("price_max IS NULL OR price_max >= 0", name="price_max_non_negative"),
        CheckConstraint(
            "price_min IS NULL OR price_max IS NULL OR price_min <= price_max",
            name="price_range_valid",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Offer {self.slug!r}>"


class MessageTemplate(Base):
    """Approved Sales Engine copy; FikaTu templates are a separate concern."""

    __tablename__ = "message_templates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    offer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("offers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    channel: Mapped[TemplateChannel] = mapped_column(template_channel_type, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    variant: Mapped[str] = mapped_column(String(16), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    offer: Mapped[Offer] = relationship(back_populates="templates")

    __table_args__ = (
        CheckConstraint("name <> ''", name="name_not_blank"),
        CheckConstraint("variant <> ''", name="variant_not_blank"),
        CheckConstraint("body <> ''", name="body_not_blank"),
        CheckConstraint("jsonb_typeof(variables) = 'array'", name="variables_array"),
        UniqueConstraint("offer_id", "channel", "variant", name="offer_channel_variant"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<MessageTemplate {self.channel.value}:{self.variant}>"
