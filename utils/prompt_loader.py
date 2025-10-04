from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List

_BASE_DIR = Path(__file__).resolve().parent.parent
PROMPT_DIR = _BASE_DIR / "prompts"


def _ensure_prompt_dir() -> Path:
    if not PROMPT_DIR.exists():
        raise FileNotFoundError(f"Prompt directory not found: {PROMPT_DIR}")
    return PROMPT_DIR


@lru_cache(maxsize=None)
def load_prompt(slug: str) -> str:
    path = _ensure_prompt_dir() / f"{slug}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt '{slug}' not found in {PROMPT_DIR}")
    return path.read_text(encoding="utf-8").strip()


@lru_cache(maxsize=1)
def load_all_prompts() -> List[Dict[str, str]]:
    prompts: List[Dict[str, str]] = []
    prompt_dir = _ensure_prompt_dir()
    for file_path in sorted(prompt_dir.glob("*.md")):
        content = file_path.read_text(encoding="utf-8").strip()
        title = file_path.stem.replace("_", " ").title()
        description = ""
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                title = stripped.lstrip("#").strip()
            else:
                description = stripped
                break
        prompts.append(
            {
                "slug": file_path.stem,
                "title": title,
                "description": description,
                "content": content,
            }
        )
    return prompts


def refresh_cache() -> None:
    load_prompt.cache_clear()
    load_all_prompts.cache_clear()
