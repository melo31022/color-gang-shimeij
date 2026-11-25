"""Download and cache the original Shimeji character assets."""
from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable

UPSTREAM_REPOSITORY = "Skittlq/alan-beckers-stickfigures-unofficial"
UPSTREAM_COMMIT = "6e32aeb3956912c1d7d8396d885cb2b61be63193"
ARCHIVE_URL = (
    f"https://api.github.com/repos/{UPSTREAM_REPOSITORY}/zipball/{UPSTREAM_COMMIT}"
)

CHARACTERS = {
    "Blue": "Blue",
    "Green": "Green",
    "Orange": "Orange",
    "Purple": "Purple",
    "Red": "Red",
    "TCO": "The Second Coming",
    "TDL": "The Dark Lord",
    "Yellow": "Yellow",
    "victim": "Victim",
}

MAX_ARCHIVE_BYTES = 100 * 1024 * 1024


def assets_ready(project_root: Path) -> bool:
    image_root = project_root / "assets" / "img"
    for character in CHARACTERS:
        folder = image_root / character
        if not (folder / "conf" / "actions.xml").is_file():
            return False
        if not any(folder.glob("*.png")):
            return False
    return True


def ensure_assets(
    project_root: Path,
    progress: Callable[[str], None] | None = None,
) -> Path:
    """Download the pinned upstream archive and extract only character assets.

    Java sources, compiled classes, JARs, installers and unrelated files are
    deliberately not extracted. The local assets directory is a cache.
    """
    image_root = project_root / "assets" / "img"
    if assets_ready(project_root):
        return image_root

    def report(message: str) -> None:
        if progress:
            progress(message)

    report("Baixando os assets originais do repositório Skittlq...")
    request = urllib.request.Request(
        ARCHIVE_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Color-Gang-Shimeji-Python/0.2",
        },
    )

    with urllib.request.urlopen(request, timeout=45) as response:
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_ARCHIVE_BYTES:
            raise RuntimeError(
                f"O arquivo de assets excede o limite de {MAX_ARCHIVE_BYTES // (1024 * 1024)} MB."
            )
        archive_bytes = response.read(MAX_ARCHIVE_BYTES + 1)

    if len(archive_bytes) > MAX_ARCHIVE_BYTES:
        raise RuntimeError("O arquivo de assets recebido é grande demais.")

    report("Extraindo os sprites e as configurações de animação...")
    image_root.mkdir(parents=True, exist_ok=True)
    extracted = 0

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue

            parts = PurePosixPath(item.filename).parts
            try:
                img_index = parts.index("img")
            except ValueError:
                continue

            relative = parts[img_index + 1 :]
            if len(relative) < 2 or relative[0] not in CHARACTERS:
                continue

            relative_path = PurePosixPath(*relative)
            is_sprite = relative_path.suffix.lower() == ".png"
            is_animation_config = (
                len(relative) == 3
                and relative[1] == "conf"
                and relative[2] in {"actions.xml", "behaviors.xml"}
            )
            if not (is_sprite or is_animation_config):
                continue

            destination = (image_root / Path(*relative)).resolve()
            try:
                destination.relative_to(image_root.resolve())
            except ValueError as exc:
                raise RuntimeError("O arquivo de assets contém um caminho inválido.") from exc

            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(item) as source, destination.open("wb") as output:
                while chunk := source.read(1024 * 1024):
                    output.write(chunk)
            extracted += 1

    if not assets_ready(project_root):
        raise RuntimeError(
            "O pacote foi extraído, mas faltam arquivos de personagens ou actions.xml."
        )

    report(f"{extracted} arquivos de assets originais preparados.")
    return image_root
