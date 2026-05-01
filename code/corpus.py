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


@dataclass
class Document:
    path: str
    domain: str        # HackerRank | Claude | Visa
    category: str      # subdirectory name (e.g. "screen", "privacy-and-legal")
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
                title=title,
                content=content,
            ))

    return docs
