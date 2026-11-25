"""Configuration and character catalogue helpers."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Character:
    character_id: str
    name: str
    sprite: Path


def load_catalog(project_root: Path) -> list[Character]:
    """Load characters.json and validate each sprite path."""
    catalog_path = project_root / "characters.json"
    try:
        data: dict[str, Any] = json.loads(catalog_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Catalogue not found: {catalog_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {catalog_path}: {exc}") from exc

    records = data.get("characters")
    if not isinstance(records, list) or not records:
        raise ValueError("characters.json must contain a non-empty 'characters' list.")

    characters: list[Character] = []
    seen_ids: set[str] = set()

    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"Character entry #{index} must be a JSON object.")

        character_id = str(record.get("id", "")).strip()
        name = str(record.get("name", "")).strip()
        sprite_name = str(record.get("sprite", "")).strip()

        if not character_id or not name or not sprite_name:
            raise ValueError(
                f"Character entry #{index} needs non-empty 'id', 'name' and 'sprite' fields."
            )
        if character_id in seen_ids:
            raise ValueError(f"Duplicate character id: {character_id}")
        seen_ids.add(character_id)

        root = project_root.resolve()
        sprite = (project_root / sprite_name).resolve()
        try:
            sprite.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Sprite path must stay inside the project: {sprite_name}") from exc

        if not sprite.is_file():
            raise FileNotFoundError(f"Sprite for {name} was not found: {sprite}")

        characters.append(Character(character_id, name, sprite))

    return characters
