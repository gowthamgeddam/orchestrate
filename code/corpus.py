"""
Load and index all markdown documents from the support corpus.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"

DOMAIN_MAP = {
    "hackerrank": "HackerRank",
    "claude": "Claude",
    "visa": "Visa",
}


# Maps raw directory names to the normalized product_area labels used in output.
_CATEGORY_NORM: dict[str, str] = {
    "hackerrank_community": "community",
    "privacy-and-legal": "privacy",
    "pro-and-max-plans": "pro_and_max_plans",
    "identity-management-sso-jit-scim": "identity_management",
    "claude-api-and-console": "claude_api",
    "claude-mobile-apps": "claude_mobile",
    "claude-in-chrome": "claude_in_chrome",
    "claude-for-education": "claude_for_education",
    "claude-for-government": "claude_for_government",
    "claude-for-nonprofits": "claude_for_nonprofits",
    "team-and-enterprise-plans": "team_and_enterprise",
    "amazon-bedrock": "amazon_bedrock",
    "general-help": "general_help",
}


def normalize_category(raw: str) -> str:
    if raw in _CATEGORY_NORM:
        return _CATEGORY_NORM[raw]
    return raw.replace("-", "_")


@dataclass
class Document:
    path: str
    domain: str            # HackerRank | Claude | Visa
    category: str          # raw subdirectory name (e.g. "screen", "privacy-and-legal")
    product_area: str      # normalized label to use in output (e.g. "screen", "privacy")
    title: str
    content: str


def _extract_title(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    fm = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', text, re.MULTILINE)
    if fm:
        return fm.group(1).strip()
    return fallback


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].lstrip()
    return text


def load_corpus(domain_filter: Optional[str] = None) -> list[Document]:
    """
    Walk data/ and return all documents.
    domain_filter: 'HackerRank' | 'Claude' | 'Visa' | None (all)
    """
    docs: list[Document] = []

    for domain_dir, domain_label in DOMAIN_MAP.items():
        if domain_filter and domain_label != domain_filter:
            continue

        base = DATA_DIR / domain_dir
        if not base.exists():
            continue

        for md_path in sorted(base.rglob("*.md")):
            rel = md_path.relative_to(base)
            parts = rel.parts
            # category = first subdirectory, or "general" for top-level files
            category = parts[0] if len(parts) > 1 else "general"

            raw = md_path.read_text(encoding="utf-8", errors="replace")
            content = _strip_frontmatter(raw)
            title = _extract_title(raw, fallback=md_path.stem)

            docs.append(Document(
                path=str(md_path.relative_to(REPO_ROOT)),
                domain=domain_label,
                category=category,
                product_area=normalize_category(category),
                title=title,
                content=content,
            ))

    return docs
