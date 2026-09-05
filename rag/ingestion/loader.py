"""Load and chunk clearly labeled demo policy documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentChunk:
    source: str
    section: str
    content: str
    metadata: dict[str, str]


def load_documents(directory: str | Path = "rag/documents") -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for path in sorted(Path(directory).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        headings = text.split("\n## ")
        for part in headings:
            content = part.strip()
            if not content:
                continue
            lines = content.splitlines()
            section = lines[0].lstrip("# ").strip()
            body = "\n".join(lines[1:]).strip() or section
            chunks.append(DocumentChunk(path.name, section, body, {"document_type": "demo-internal-policy"}))
    if not chunks:
        raise FileNotFoundError(f"No markdown evidence documents found in {directory}")
    return chunks
