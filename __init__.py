"""MemPalace memory provider — semantic recall via MemPalace CLI.

Context-only provider (no tools exposed). Before each turn,
searches MemPalace for relevant past context and injects it
as prefetched memory.

Requires: mempalace installed and palace initialised.
Config: memory.provider = "mempalace" in config.yaml.
"""

from __future__ import annotations

import logging
import re
import subprocess
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MEMPALACE_BIN = "mempalace"

_TITLE_RE = re.compile(r"^\s*\[(\d+)\]\s+(\S+)\s*/\s*(\S+)", re.MULTILINE)
_SOURCE_RE = re.compile(r"^\s*Source:\s+(\S+)", re.MULTILINE)
_MATCH_RE  = re.compile(r"^\s*Match:\s+cosine=([\d.]+)", re.MULTILINE)


def _run_mempalace_search(query: str, max_results: int = 3) -> str:
    """Run ``mempalace search`` and return raw output, or empty string on failure."""
    try:
        result = subprocess.run(
            [_MEMPALACE_BIN, "search", query, "--results", str(max_results)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            logger.debug("mempalace search non-zero exit: %s", result.returncode)
            return ""
        return result.stdout
    except FileNotFoundError:
        logger.debug("mempalace binary not found — provider inactive")
        return ""
    except subprocess.TimeoutExpired:
        logger.debug("mempalace search timed out")
        return ""
    except Exception as exc:
        logger.debug("mempalace search failed: %s", exc)
        return ""


def _extract_content(raw: str) -> str:
    """Extract the `> …` quoted content lines from mempalace search output.

    The mempalace CLI wraps results with decorators; we only keep the
    verbatim drawer content (lines starting with ``>``), skip metadata
    chrome, and truncate per-result as needed.
    """
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            lines.append(stripped)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

class MemPalaceMemoryProvider(MemoryProvider):
    """Semantic recall from local MemPalace knowledge base."""

    @property
    def name(self) -> str:
        return "mempalace"

    def is_available(self) -> bool:
        """True if mempalace binary is on PATH and the palace exists."""
        try:
            result = subprocess.run(
                [_MEMPALACE_BIN, "status"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def initialize(self, session_id: str, **kwargs) -> None:
        """No-op — mempalace is stateless."""
        logger.debug("MemPalace provider initialised for session %s", session_id)

    def system_prompt_block(self) -> str:
        return (
            "MemPalace memory is active. Past conversation context and "
            "project knowledge will be recalled automatically for each query."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        """Search MemPalace for context relevant to the upcoming turn."""
        if not query or not query.strip():
            return ""

        raw = _run_mempalace_search(query, max_results=3)
        if not raw:
            return ""

        content = _extract_content(raw)
        if not content:
            return ""

        return (
            "<memory-context>\n"
            "[System note: The following is recalled memory context from MemPalace, "
            "NOT new user input. Treat as authoritative reference data.]\n"
            f"{content}\n"
            "</memory-context>"
        )

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """No tools exposed — context-only provider."""
        return []


# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------

def register(ctx):
    """Register this provider with the Hermes memory plugin system."""
    ctx.register_memory_provider(MemPalaceMemoryProvider())
