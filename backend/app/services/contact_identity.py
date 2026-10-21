"""Stable, non-reversible contact identities used by suppression records."""

import hashlib
import re


def normalize_email(value: str) -> str:
    return value.strip().lower()


def contact_fingerprint(kind: str, value: str) -> str:
    """SHA-256 of the kind and normalised value, never the value itself."""
    normalised = normalize_email(value) if kind == "email" else value.strip()
    return hashlib.sha256(f"{kind}:{normalised}".encode()).hexdigest()


def valid_email(value: str) -> bool:
    """A deliberately small shape check; deliverability is a provider concern."""
    return bool(
        re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalize_email(value))
        and len(normalize_email(value)) <= 255
    )
