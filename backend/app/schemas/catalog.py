"""Request and response contracts for offers and Sales Engine templates."""

import re
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import TemplateChannel
from app.schemas.types import UtcDatetime

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
VARIABLE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _normalise_slug(value: str) -> str:
    slug = value.strip().lower()
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError("Use lowercase letters, numbers and single hyphens.")
    return slug


class OfferCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=140)
    description: str | None = None
    price_min: Decimal | None = Field(default=None, ge=0)
    price_max: Decimal | None = Field(default=None, ge=0)
    currency: str = "KES"
    pitch_angle: str | None = None
    is_active: bool = True

    @field_validator("name", "slug")
    @classmethod
    def no_outer_whitespace(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str) -> str:
        return _normalise_slug(value)

    @field_validator("currency")
    @classmethod
    def valid_currency(cls, value: str) -> str:
        currency = value.strip().upper()
        if not CURRENCY_PATTERN.fullmatch(currency):
            raise ValueError("Currency must be a three-letter code, for example KES or USD.")
        return currency

    @model_validator(mode="after")
    def valid_price_range(self):
        if (
            self.price_min is not None
            and self.price_max is not None
            and self.price_min > self.price_max
        ):
            raise ValueError("Minimum price cannot be greater than maximum price.")
        return self


class OfferUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, min_length=1, max_length=140)
    description: str | None = None
    price_min: Decimal | None = Field(default=None, ge=0)
    price_max: Decimal | None = Field(default=None, ge=0)
    currency: str | None = None
    pitch_angle: str | None = None
    is_active: bool | None = None

    @field_validator("name", "slug")
    @classmethod
    def trim_if_present(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str | None) -> str | None:
        return None if value is None else _normalise_slug(value)

    @field_validator("currency")
    @classmethod
    def valid_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        currency = value.strip().upper()
        if not CURRENCY_PATTERN.fullmatch(currency):
            raise ValueError("Currency must be a three-letter code, for example KES or USD.")
        return currency


class OfferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    price_min: Decimal | None
    price_max: Decimal | None
    currency: str
    pitch_angle: str | None
    is_active: bool
    created_at: UtcDatetime
    updated_at: UtcDatetime


class TemplateCreate(BaseModel):
    offer_id: uuid.UUID
    channel: TemplateChannel
    name: str = Field(min_length=1, max_length=120)
    variant: str = Field(min_length=1, max_length=16)
    body: str = Field(min_length=1)
    variables: list[str] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("name", "body")
    @classmethod
    def non_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("variant")
    @classmethod
    def normalise_variant(cls, value: str) -> str:
        variant = value.strip().upper()
        if not variant:
            raise ValueError("Variant cannot be blank.")
        return variant

    @field_validator("variables")
    @classmethod
    def valid_variable_names(cls, values: list[str]) -> list[str]:
        normalised: list[str] = []
        for value in values:
            name = value.strip()
            if not VARIABLE_PATTERN.fullmatch(name):
                raise ValueError(f"Invalid variable name: {value!r}.")
            if name not in normalised:
                normalised.append(name)
        return normalised


class TemplateUpdate(BaseModel):
    offer_id: uuid.UUID | None = None
    channel: TemplateChannel | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    variant: str | None = Field(default=None, min_length=1, max_length=16)
    body: str | None = Field(default=None, min_length=1)
    variables: list[str] | None = None
    is_active: bool | None = None

    @field_validator("name", "body")
    @classmethod
    def trim_if_present(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("variant")
    @classmethod
    def normalise_variant(cls, value: str | None) -> str | None:
        if value is None:
            return None
        variant = value.strip().upper()
        if not variant:
            raise ValueError("Variant cannot be blank.")
        return variant

    @field_validator("variables")
    @classmethod
    def valid_variable_names(cls, values: list[str] | None) -> list[str] | None:
        return None if values is None else TemplateCreate.valid_variable_names(values)


class TemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    offer_id: uuid.UUID
    channel: TemplateChannel
    name: str
    variant: str
    body: str
    variables: list[str]
    is_active: bool
    created_at: UtcDatetime
    updated_at: UtcDatetime
