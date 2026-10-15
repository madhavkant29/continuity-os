"""Deterministic, source-backed organizational knowledge primitives.

No model output is ever treated as a verified corporate fact. Each citation
identifies a specific immutable version of a source and its original line.
"""
from __future__ import annotations

import hashlib
import re

KINDS = frozenset({"DOCUMENT", "TICKET", "CONVERSATION"})
STOP = frozenset("a an the is are was were of for to in with on at about what who which how why do does show find explain from and or this that our their please me workflow source sources documents document ticket tickets chat conversations conversation evidence decision policy support supports process".split())


def passages(content: str, source_id: str) -> list[dict]:
    """Preserve exact original one-based line numbers; never synthesize citations."""
    result = []
    for idx, line in enumerate(content.splitlines(), start=1):
        if line.strip():
            result.append({"id": f"{source_id}:L{idx}", "locator": f"{source_id}#L{idx}",
                           "line": idx, "quote": line})
    return result


def source_identity(workflow_id: str, kind: str, title: str, reference: str, content: str):
    if kind not in KINDS:
        raise ValueError("Unsupported source type")
    key = hashlib.sha256("\0".join((workflow_id, kind, reference.strip() or title.strip())).encode()).hexdigest()[:24]
    fingerprint = hashlib.sha256(content.encode()).hexdigest()
    return "src:" + key + ":" + fingerprint[:20], key, fingerprint


def tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9_]+", text.lower()) if len(t) > 2 and t not in STOP}


def rank_passages(question: str, entries: list[dict], limit: int = 7) -> list[dict]:
    """Literal lexical match only. Empty overlap never becomes a claimed answer."""
    words = tokens(question)
    if not words:
        return entries[:limit]
    ranked=[]
    for entry in entries:
        haystack=tokens(" ".join((entry.get("quote", ""), entry.get("title", ""), entry.get("reference", ""))))
        match=len(words & haystack)
        if match:
            ranked.append((match, entry))
    return [row for _,row in sorted(ranked,key=lambda x:(-x[0],x[1]["locator"]))[:limit]]
