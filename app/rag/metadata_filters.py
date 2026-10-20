"""Resolve safe, normalized retrieval filters from a Vietnamese user query."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class MetadataFilter:
    """The subset of chunk metadata that must match before vector ranking."""

    device: str | None = None
    brand: str | None = None


# Values here are the canonical values stored by ``document_processing.chunker``.
# Keep aliases as whole phrases: notably, ``lg`` must not match inside another word.
_DEVICE_ALIASES = {
    "rice_cooker": ("noi com dien", "noi com"),
    "washing_machine": ("may giat",),
    "refrigerator": ("tu lanh",),
    "freezer": ("tu dong",),
    "air_conditioner": ("dieu hoa", "may lanh", "may dieu hoa"),
    "water_heater": ("binh nuoc nong", "may nuoc nong", "binh nong lanh"),
}
_BRANDS = ("ariston", "lg", "panasonic", "samsung", "toshiba", "evn")


def resolve_metadata_filter(
    query: str, *, device: str | None = None, brand: str | None = None
) -> MetadataFilter:
    """Use explicit values first; otherwise infer one device and brand from *query*.

    A missing value deliberately means "do not filter by this field", not
    ``metadata = 'unknown'``. This preserves recall for generic questions.
    """
    normalized_query = _normalize(query)
    return MetadataFilter(
        device=_normalize_value(device) if device else _find_device(normalized_query),
        brand=_normalize_value(brand) if brand else _find_brand(normalized_query),
    )


def _find_device(query: str) -> str | None:
    for device, aliases in _DEVICE_ALIASES.items():
        if any(_contains_phrase(query, alias) for alias in aliases):
            return device
    return None


def _find_brand(query: str) -> str | None:
    return next((brand for brand in _BRANDS if _contains_phrase(query, brand)), None)


def _normalize_value(value: str) -> str:
    return value.strip().lower()


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.lower())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return without_accents.replace("đ", "d")


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\\w){re.escape(phrase)}(?!\\w)", text) is not None
