from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ThemeEntry:
    theme_id: str
    sleeve: str
    subtheme: str
    primary_keywords: list[str] = field(default_factory=list)
    anchor_phrases: list[str] = field(default_factory=list)
    negatives: list[str] = field(default_factory=list)


@dataclass
class ThemeMatch:
    theme_id: str
    sleeve: str
    subtheme: str
    confidence: float


class KeywordMatcher:
    """Matches text against the 76-theme taxonomy to classify headlines.

    Loads taxonomy from the keyword_taxonomy.md doc so it stays in sync.
    Can also accept a pre-built list of ThemeEntry objects directly.
    """

    MAX_MATCHES = 4

    def __init__(self, themes: list[ThemeEntry] | None = None) -> None:
        if themes is not None:
            self._themes = themes
        else:
            try:
                self._themes = _load_taxonomy_from_markdown()
            except (FileNotFoundError, OSError) as exc:
                logger.warning(
                    "Could not load taxonomy file (%s); "
                    "initializing with empty theme list. "
                    "KeywordMatcher will return no matches until themes are provided.",
                    exc,
                )
                self._themes = []

    def match(self, text: str) -> list[ThemeMatch]:
        """Match text against all themes and return up to MAX_MATCHES results.

        Confidence tiers:
            0.9 — anchor phrase match
            0.7 — multiple primary keyword matches
            0.5 — single primary keyword match
        """
        text_lower = text.lower()
        matches: list[ThemeMatch] = []

        for theme in self._themes:
            # Check disambiguation negatives first — if any are present, skip
            if _any_phrase_in(theme.negatives, text_lower):
                continue

            # Check anchor phrases (highest confidence)
            has_anchor = _any_phrase_in(theme.anchor_phrases, text_lower)

            # Check primary keywords
            keyword_hits = sum(
                1 for kw in theme.primary_keywords if kw.lower() in text_lower
            )

            if keyword_hits == 0 and not has_anchor:
                continue

            # Assign confidence
            if has_anchor:
                confidence = 0.9
            elif keyword_hits >= 2:
                confidence = 0.7
            else:
                confidence = 0.5

            matches.append(
                ThemeMatch(
                    theme_id=theme.theme_id,
                    sleeve=theme.sleeve,
                    subtheme=theme.subtheme,
                    confidence=confidence,
                )
            )

        # Sort by confidence descending, cap at MAX_MATCHES
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches[: self.MAX_MATCHES]


def _any_phrase_in(phrases: list[str], text_lower: str) -> bool:
    """Check if any phrase appears in the lowered text."""
    for phrase in phrases:
        if phrase.lower() in text_lower:
            return True
    return False


# ---------------------------------------------------------------------------
# Taxonomy parser — reads keyword_taxonomy.md into ThemeEntry objects
# ---------------------------------------------------------------------------

_TAXONOMY_PATH = (
    Path(__file__).resolve().parents[3] / "docs" / "keyword_taxonomy.md"
)


def _load_taxonomy_from_markdown(
    path: Path | None = None,
) -> list[ThemeEntry]:
    """Parse the keyword_taxonomy.md file into a list of ThemeEntry."""
    path = path or _TAXONOMY_PATH
    text = path.read_text(encoding="utf-8")

    themes: list[ThemeEntry] = []
    # Split into theme blocks by the ### header pattern
    blocks = re.split(r"###\s+(\w+)\s+--\s+", text)

    # blocks[0] is the preamble, then pairs of (theme_id, block_content)
    i = 1
    while i < len(blocks) - 1:
        theme_id = blocks[i].strip()
        block = blocks[i + 1]
        i += 2

        sleeve = ""
        subtheme = ""
        keywords: list[str] = []
        anchors: list[str] = []
        negatives: list[str] = []

        for line in block.split("\n"):
            line_stripped = line.strip()
            if "**Sleeve / Sub-sleeve**" in line_stripped:
                val = _extract_table_value(line_stripped)
                parts = val.split("/", 1)
                sleeve = parts[0].strip()
                subtheme = parts[1].strip() if len(parts) > 1 else ""
            elif "**Primary keywords**" in line_stripped:
                val = _extract_table_value(line_stripped)
                keywords = [k.strip() for k in val.split(",") if k.strip()]
            elif "**Anchor phrases**" in line_stripped:
                val = _extract_table_value(line_stripped)
                anchors = _parse_quoted_list(val)
            elif "**Disambiguation negatives**" in line_stripped:
                val = _extract_table_value(line_stripped)
                negatives = _parse_quoted_list(val)

        if theme_id and (keywords or anchors):
            themes.append(
                ThemeEntry(
                    theme_id=theme_id,
                    sleeve=sleeve,
                    subtheme=subtheme,
                    primary_keywords=keywords,
                    anchor_phrases=anchors,
                    negatives=negatives,
                )
            )

    return themes


def _extract_table_value(line: str) -> str:
    """Extract the value column from a markdown table row like | Key | Value |."""
    parts = line.split("|")
    if len(parts) >= 3:
        return parts[-2].strip()
    return ""


def _parse_quoted_list(text: str) -> list[str]:
    """Parse a comma-separated list of quoted strings, stripping quotes."""
    items = re.findall(r'"([^"]+)"', text)
    if items:
        return items
    # Fallback: split by comma if no quotes found
    return [s.strip() for s in text.split(",") if s.strip()]
