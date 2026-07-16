"""
The ORTA agents' knowledge layer -- a small, git-tracked "LLM wiki" the agents
consult (and grow) so they reason from accrued biology + image-analysis knowledge
rather than from a blank slate or from our current parameters.

Storage: one markdown *card* per concept in the unified project wiki (``wiki/``, in domain
subfolders) with YAML frontmatter (name / description / type / tags / sources / links) + a
free-text body. Cards are found recursively; prose pages without frontmatter (literature/,
decisions/) are ignored by this loader but are part of the human wiki. The machine-generated
card list is ``wiki/index-cards.md``; the curated human index is ``wiki/index.md``.
Retrieval is keyword/tag matching over the frontmatter + headings
(no embeddings); the orchestrators call ``relevant_for(...)`` and inject the matched
cards into agent prompts, and agents append new ``finding`` cards via ``write()``.

Cards are never executed -- they are text that informs judgment. The web-literature
accrual that *creates* cited cards is a separate build-time step (``wiki_accrue.py``);
nothing here touches the network.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

WIKI_DIR = Path(__file__).resolve().parents[2] / "wiki"
INDEX = WIKI_DIR / "index-cards.md"   # machine-generated card list; the curated human index is index.md
VALID_TYPES = ("biology", "method", "finding", "reference")
# wiki files that are curated docs / generated indexes, not cards
RESERVED = {"index.md", "index-cards.md", "schema.md", "log.md", "README.md"}
# subfolder a newly written card of each type is filed under
_TYPE_DIR = {"biology": "biology", "method": "methods", "finding": "findings", "reference": "findings"}

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
_TOKEN = re.compile(r"[a-z0-9]+")


@dataclass
class Card:
    name: str
    description: str = ""
    type: str = "reference"
    tags: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    body: str = ""
    path: Path | None = None

    # tokens used for keyword matching (name + description + tags + body headings)
    def _haystack(self) -> set[str]:
        heads = " ".join(re.findall(r"^#{1,6}\s*(.+)$", self.body, re.MULTILINE))
        text = " ".join([self.name, self.description, " ".join(self.tags), heads]).lower()
        return set(_TOKEN.findall(text)) | {t.lower() for t in self.tags}

    def to_markdown(self) -> str:
        fm = {
            "name": self.name, "description": self.description, "type": self.type,
            "tags": self.tags, "sources": self.sources, "links": self.links,
        }
        front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
        return f"---\n{front}\n---\n\n{self.body.strip()}\n"


# ------------------------------------------------------------------- parsing / IO
def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def _parse(path: Path) -> Card | None:
    m = _FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not m:
        return None
    fm = yaml.safe_load(m.group(1)) or {}
    return Card(
        name=str(fm.get("name") or path.stem),
        description=str(fm.get("description") or ""),
        type=str(fm.get("type") or "reference"),
        tags=[str(t) for t in (fm.get("tags") or [])],
        sources=[str(s) for s in (fm.get("sources") or [])],
        links=[str(l) for l in (fm.get("links") or [])],
        body=m.group(2).strip(),
        path=path,
    )


def all_cards() -> list[Card]:
    if not WIKI_DIR.exists():
        return []
    out = []
    for p in sorted(WIKI_DIR.rglob("*.md")):
        if p.name in RESERVED:
            continue
        c = _parse(p)          # prose pages without frontmatter parse to None -> skipped
        if c:
            out.append(c)
    return out


def _find(slug: str) -> Path | None:
    """First markdown file named <slug>.md anywhere under the wiki (cards live in subfolders)."""
    return next((p for p in sorted(WIKI_DIR.rglob(f"{slug}.md"))), None)


def read(name: str) -> Card | None:
    p = _find(_slug(name))
    return _parse(p) if p else None


def expectations(marker: str) -> dict | None:
    """Literature-derived soft expectations for a marker (count / eq_diam_um / coverage),
    read from the `<marker>-biology` card's `expectations:` frontmatter. Used by the
    autofoci score to anchor count/shape/coverage. None if the card has no expectations."""
    p = _find(f"{_slug(marker)}-biology")
    if not p:
        return None
    m = _FRONTMATTER.match(p.read_text(encoding="utf-8"))
    fm = (yaml.safe_load(m.group(1)) or {}) if m else {}
    return fm.get("expectations")


# --------------------------------------------------------------------- retrieval
def search(query: str = "", tags: list[str] | None = None, type: str | None = None,
           limit: int = 6) -> list[Card]:
    """Rank cards by token overlap with ``query`` + ``tags`` (optionally filtered by
    ``type``). Returns the top ``limit`` non-zero matches (description-only fallback)."""
    want = set(_TOKEN.findall(query.lower())) | {t.lower() for t in (tags or [])}
    scored = []
    for c in all_cards():
        if type and c.type != type:
            continue
        hay = c._haystack()
        score = len(want & hay)
        # light boost for an exact tag hit
        score += sum(2 for t in (tags or []) if t.lower() in {x.lower() for x in c.tags})
        if score > 0 or not want:
            scored.append((score, c))
    scored.sort(key=lambda sc: (-sc[0], sc[1].name))
    return [c for _, c in scored[:limit]]


def relevant_for(marker: str | None = None, algorithm: str | None = None,
                 limit: int = 6) -> list[Card]:
    """Convenience: cards relevant to a marker and/or an algorithm family, biased
    toward biology + method + finding cards. Expands one hop along ``links`` so a
    marker surfaces its linked candidate methods (and vice-versa). Used by the
    orchestrators to ground agents."""
    terms = [t for t in (marker, algorithm) if t]
    seed = search(query=" ".join(terms), tags=terms, limit=limit * 2)

    # one-hop link expansion: pull in cards the matches point to
    have = {c.name for c in seed}
    expanded = list(seed)
    for c in seed:
        for ln in c.links:
            if _slug(ln) not in {_slug(n) for n in have}:
                linked = read(ln)
                if linked:
                    expanded.append(linked)
                    have.add(linked.name)

    bio_method = [c for c in expanded if c.type in ("biology", "method", "finding")]
    ordered = bio_method + [c for c in expanded if c not in bio_method]
    return ordered[:limit]


def render_for_prompt(cards: list[Card], max_chars: int = 6000) -> str:
    """Compact text block of cards to inject into an agent prompt."""
    if not cards:
        return "(no relevant wiki cards)"
    parts, used = [], 0
    for c in cards:
        block = (f"### [{c.type}] {c.name}\n{c.description}\n{c.body}".strip()
                 + (f"\nsources: {', '.join(c.sources)}" if c.sources else ""))
        if used + len(block) > max_chars:
            block = block[: max(0, max_chars - used)] + " …"
        parts.append(block)
        used += len(block)
        if used >= max_chars:
            break
    return "\n\n".join(parts)


# ------------------------------------------------------------------------- write
def write(card: Card | dict, *, append_body: bool = False) -> Path:
    """Create or update a card on disk and refresh the card index. If ``append_body`` and the
    card exists, the new body is appended (dated) rather than replacing -- used for
    growing ``finding`` cards across runs."""
    if not isinstance(card, Card):
        data = card if isinstance(card, dict) else (
            card.model_dump() if hasattr(card, "model_dump") else dict(card))
        card = Card(**{k: v for k, v in data.items() if k in Card.__dataclass_fields__})
    if card.type not in VALID_TYPES:
        raise ValueError(f"card type {card.type!r} not in {VALID_TYPES}")
    # update an existing card in place; otherwise file a new one under its type's subfolder
    path = _find(_slug(card.name)) or (
        WIKI_DIR / _TYPE_DIR.get(card.type, "findings") / f"{_slug(card.name)}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    if append_body and path.exists():
        existing = _parse(path)
        if existing:
            merged = dict.fromkeys(existing.tags + card.tags)          # de-dup, keep order
            existing.tags = list(merged)
            existing.sources = list(dict.fromkeys(existing.sources + card.sources))
            existing.body = (existing.body.rstrip() + "\n\n" + card.body.strip()).strip()
            card = existing
    card.path = path
    path.write_text(card.to_markdown(), encoding="utf-8")
    rebuild_index()
    return path


def rebuild_index() -> None:
    """Regenerate wiki/index-cards.md — the machine list of agent-readable cards. Kept separate
    from the curated human index (wiki/index.md), which this never touches."""
    cards = all_cards()
    lines = ["# ORTA wiki — card index (machine-generated)\n",
             "Auto-generated list of agent-readable cards (those with frontmatter `type`). "
             "The curated human index is [index.md](index.md). One line per card.\n"]
    for t in VALID_TYPES:
        group = [c for c in cards if c.type == t]
        if not group:
            continue
        lines.append(f"\n## {t}\n")
        for c in group:
            tagstr = f" `{', '.join(c.tags)}`" if c.tags else ""
            rel = c.path.relative_to(WIKI_DIR).as_posix()
            lines.append(f"- [{c.name}]({rel}) — {c.description}{tagstr}")
    INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")
