"""Shared Anthropic-SDK helper for the ORTA agents: load a persona system prompt and
run one structured (optionally vision) turn, parsing the reply into a pydantic schema.
Reads ANTHROPIC_API_KEY from the environment; model via ORTA_AGENT_MODEL."""

from __future__ import annotations

import os
import json
import base64
from pathlib import Path

PERSONAS = Path(__file__).resolve().parents[1] / "personas"
MODEL = os.environ.get("ORTA_AGENT_MODEL", "claude-sonnet-4-6")


def _persona(name: str) -> str:
    return (PERSONAS / f"{name}.md").read_text(encoding="utf-8")


def _llm_json(system: str, user_text: str, schema, image_path: str | None = None):
    """One structured agent turn via the Anthropic SDK; returns a `schema` object."""
    import anthropic
    client = anthropic.Anthropic()
    content = [{"type": "text", "text": user_text +
                f"\n\nReturn ONLY JSON matching this schema:\n{json.dumps(schema.model_json_schema())}"}]
    if image_path:
        b64 = base64.standard_b64encode(Path(image_path).read_bytes()).decode()
        content.append({"type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": b64}})
    msg = client.messages.create(model=MODEL, max_tokens=1024, system=system,
                                 messages=[{"role": "user", "content": content}])
    text = "".join(b.text for b in msg.content if b.type == "text")
    start, end = text.find("{"), text.rfind("}")
    return schema.model_validate_json(text[start:end + 1])
