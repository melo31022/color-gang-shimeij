"""Parse Shimeji-ee character animation definitions."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AnimationFrame:
    image: Path
    duration_ms: int
    velocity_x: float
    velocity_y: float
    anchor_x: int
    anchor_y: int


@dataclass(frozen=True)
class CharacterAssets:
    character_id: str
    display_name: str
    folder: Path
    animations: dict[str, tuple[AnimationFrame, ...]]

    def clip(self, name: str) -> tuple[AnimationFrame, ...]:
        return self.animations.get(name, self.animations.get("Stand", ()))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _pair(value: str | None, default: tuple[float, float]) -> tuple[float, float]:
    if not value:
        return default
    try:
        first, second = value.split(",", 1)
        return float(first.strip()), float(second.strip())
    except (ValueError, TypeError):
        return default


def parse_actions_xml(
    xml_text: str,
    character_folder: Path,
    character_id: str,
    display_name: str,
) -> CharacterAssets:
    """Convert source actions.xml Pose lists into Python animation clips."""
    root = ET.fromstring(xml_text.lstrip("\ufeff"))
    clips: dict[str, tuple[AnimationFrame, ...]] = {}

    for action in root.iter():
        if _local_name(action.tag) != "Action":
            continue
        action_name = action.attrib.get("Name")
        if not action_name:
            continue

        # Definitions contain Animation as a direct child. Runtime behavior
        # sequences use ActionReference nodes and are skipped here.
        animations = [
            child for child in list(action)
            if _local_name(child.tag) == "Animation"
        ]
        if not animations:
            continue

        frames: list[AnimationFrame] = []
        for animation in animations:
            for pose in animation.iter():
                if _local_name(pose.tag) != "Pose":
                    continue

                image_value = pose.attrib.get("Image", "").strip()
                if not image_value:
                    continue

                image_name = Path(image_value.replace("\\", "/")).name
                image_path = (character_folder / image_name).resolve()
                try:
                    image_path.relative_to(character_folder.resolve())
                except ValueError:
                    continue
                if not image_path.is_file():
                    continue

                try:
                    duration_units = float(pose.attrib.get("Duration", "8"))
                except ValueError:
                    duration_units = 8.0

                velocity_x, velocity_y = _pair(
                    pose.attrib.get("Velocity"), (0.0, 0.0)
                )
                anchor_x, anchor_y = _pair(
                    pose.attrib.get("ImageAnchor"), (64.0, 128.0)
                )
                frames.append(
                    AnimationFrame(
                        image=image_path,
                        duration_ms=max(16, round(duration_units * 10)),
                        velocity_x=velocity_x,
                        velocity_y=velocity_y,
                        anchor_x=round(anchor_x),
                        anchor_y=round(anchor_y),
                    )
                )

        if frames:
            clips[action_name] = tuple(frames)

    if not clips:
        raise ValueError(
            f"Nenhuma animação válida foi encontrada em "
            f"{character_folder / 'conf' / 'actions.xml'}"
        )

    return CharacterAssets(
        character_id=character_id,
        display_name=display_name,
        folder=character_folder,
        animations=clips,
    )


def load_character_assets(
    image_root: Path,
    character_names: dict[str, str],
) -> list[CharacterAssets]:
    characters: list[CharacterAssets] = []
    for character_id, display_name in character_names.items():
        folder = image_root / character_id
        actions_path = folder / "conf" / "actions.xml"
        if not actions_path.is_file():
            raise FileNotFoundError(f"Arquivo ausente: {actions_path}")

        xml_text = actions_path.read_text(encoding="utf-8-sig")
        characters.append(
            parse_actions_xml(xml_text, folder, character_id, display_name)
        )
    return characters
