"""Animated desktop pets driven by the original Shimeji-ee assets."""
from __future__ import annotations

import ctypes
import json
import os
import random
import sys
import time
import tkinter as tk
from collections import OrderedDict
from pathlib import Path
from tkinter import messagebox

from PIL import Image, ImageOps, ImageTk

from .assets import CHARACTERS, ensure_assets
from .core import AnimationFrame, CharacterAssets, load_character_assets


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRANSPARENT_COLOR = "#ff00ff"

DEFAULT_SETTINGS = {
    "start_all_characters": True,
    "max_characters": 20,
    "speed": 1.35,
    "tick_ms": 32,
    "random_action_min_seconds": 3.0,
    "random_action_max_seconds": 9.0,
    "dance_probability": 0.22,
    "sit_probability": 0.20,
}


def load_settings(project_root: Path) -> dict:
    path = project_root / "settings.json"
    if not path.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        supplied = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido em {path}: {exc}") from exc
    if not isinstance(supplied, dict):
        raise ValueError("settings.json precisa conter um objeto JSON.")

    settings = DEFAULT_SETTINGS | supplied
    settings["max_characters"] = max(1, min(50, int(settings["max_characters"])))
    settings["tick_ms"] = max(16, min(100, int(settings["tick_ms"])))
    settings["speed"] = max(0.2, min(8.0, float(settings["speed"])))
    settings["dance_probability"] = max(
        0.0, min(1.0, float(settings["dance_probability"]))
    )
    settings["sit_probability"] = max(
        0.0, min(1.0, float(settings["sit_probability"]))
    )
    settings["random_action_min_seconds"] = max(
        0.5, float(settings["random_action_min_seconds"])
    )
    settings["random_action_max_seconds"] = max(
        settings["random_action_min_seconds"],
        float(settings["random_action_max_seconds"]),
    )
    return settings


def get_work_area(root: tk.Tk) -> tuple[int, int, int, int]:
    if os.name == "nt":
        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        rect = RECT()
        try:
            ok = ctypes.windll.user32.SystemParametersInfoW(
                0x0030, 0, ctypes.byref(rect), 0
            )
            if ok:
                return rect.left, rect.top, rect.right, rect.bottom
        except (AttributeError, OSError):
            pass

    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


class FrameCache:
    """Small LRU cache to avoid keeping every dance frame in RAM."""

    def __init__(self, master: tk.Tk, capacity: int = 180) -> None:
        self.master = master
        self.capacity = capacity
        self.cache: OrderedDict[tuple[Path, bool], ImageTk.PhotoImage] = OrderedDict()

    def get(self, frame: AnimationFrame, mirror: bool) -> ImageTk.PhotoImage:
        key = (frame.image, mirror)
        cached = self.cache.get(key)
        if cached is not None:
            self.cache.move_to_end(key)
            return cached

        with Image.open(frame.image) as opened:
            image = opened.convert("RGBA")
        if mirror:
            image = ImageOps.mirror(image)

        photo = ImageTk.PhotoImage(image, master=self.master)
        self.cache[key] = photo
        self.cache.move_to_end(key)
        while len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
        return photo


class DesktopPet:
    def __init__(
        self,
        app: "ShimejiApp",
        character: CharacterAssets,
        x: int,
    ) -> None:
        self.app = app
        self.character = character
        self.left, self.top, self.right, self.bottom = app.work_area
        self.x = float(x)
        self.y = float(self.bottom - 128)
        self.width = 128
        self.height = 128

        self.direction = random.choice((-1, 1))
        self.action_name = ""
        self.frames: tuple[AnimationFrame, ...] = ()
        self.frame_index = 0
        self.frame_elapsed = 0.0
        self.photo: ImageTk.PhotoImage | None = None
        self.last_geometry: tuple[int, int] | None = None
        self.dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.next_decision = time.monotonic() + random.uniform(2.0, 6.0)
        self.action_loop = True

        self.window = tk.Toplevel(app.root)
        self.window.overrideredirect(True)
        self.window.configure(bg=TRANSPARENT_COLOR)
        self.window.wm_attributes("-topmost", True)
        try:
            self.window.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        except tk.TclError as exc:
            self.window.destroy()
            raise RuntimeError(
                "O Tk instalado não oferece transparência por cor. "
                "Use Python para Windows com Tk 8.6."
            ) from exc

        self.label = tk.Label(
            self.window,
            bg=TRANSPARENT_COLOR,
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=0,
            cursor="hand2",
        )
        self.label.pack()
        self.label.bind("<ButtonPress-1>", self.on_drag_start)
        self.label.bind("<B1-Motion>", self.on_drag_motion)
        self.label.bind("<ButtonRelease-1>", self.on_drag_end)
        self.label.bind("<Button-3>", self.on_context_menu)

        initial = "Stand" if "Stand" in character.animations else next(iter(character.animations))
        self.set_action(initial)
        self.render()

    def _mirror_for(self, frame: AnimationFrame) -> bool:
        default_direction = -1 if frame.velocity_x < 0 else 1
        if frame.velocity_x == 0:
            default_direction = -1
        return self.direction != default_direction

    def set_action(
        self,
        name: str,
        *,
        direction: int | None = None,
        loop: bool = True,
    ) -> None:
        if direction in (-1, 1):
            self.direction = direction

        frames = self.character.clip(name)
        if not frames:
            fallback = self.character.animations.get("Stand")
            if not fallback:
                return
            name = "Stand"
            frames = fallback

        self.action_name = name
        self.frames = frames
        self.frame_index = 0
        self.frame_elapsed = 0.0
        self.action_loop = loop
        self.show_frame()

    def show_frame(self) -> None:
        if not self.frames:
            return
        frame = self.frames[self.frame_index]
        self.photo = self.app.frame_cache.get(frame, self._mirror_for(frame))
        self.width = self.photo.width()
        self.height = self.photo.height()
        self.label.configure(image=self.photo)
        self.render()

    def render(self) -> None:
        position = (round(self.x), round(self.y))
        if position != self.last_geometry:
            self.window.geometry(
                f"{self.width}x{self.height}+{position[0]}+{position[1]}"
            )
            self.last_geometry = position

    def _choose_random_action(self, now: float) -> None:
        available = self.character.animations
        choices: list[str] = []

        if "Walk" in available:
            choices.extend(["Walk"] * 5)
        if "Stand" in available:
            choices.extend(["Stand"] * 3)
        if "Sit" in available and random.random() < self.app.settings["sit_probability"]:
            choices.extend(["Sit"] * 3)
        if "Dance" in available and random.random() < self.app.settings["dance_probability"]:
            choices.extend(["Dance"] * 4)
        if "Sprawl" in available and random.random() < 0.12:
            choices.append("Sprawl")
        if "Tripping" in available and random.random() < 0.06:
            choices.append("Tripping")

        if not choices:
            choices = list(available)
        action = random.choice(choices)
        direction = random.choice((-1, 1)) if action in {"Walk", "Run", "Dash"} else None
        self.set_action(action, direction=direction)
        self.next_decision = now + random.uniform(
            self.app.settings["random_action_min_seconds"],
            self.app.settings["random_action_max_seconds"],
        )

    def step(self, delta_ms: float, now: float) -> None:
        if self.dragging:
            return

        if now >= self.next_decision:
            self._choose_random_action(now)

        if self.action_name in {"Walk", "Run", "Dash", "RunAffordance"}:
            frame = self.frames[self.frame_index]
            source_speed = abs(frame.velocity_x) or 4.0
            speed_scale = max(0.65, min(2.8, source_speed / 4.0))
            self.x += (
                self.direction
                * self.app.settings["speed"]
                * speed_scale
                * (delta_ms / 32.0)
            )

            max_x = max(self.left, self.right - self.width)
            if self.x <= self.left:
                self.x = float(self.left)
                self.set_action("Walk", direction=1)
            elif self.x >= max_x:
                self.x = float(max_x)
                self.set_action("Walk", direction=-1)

        self.frame_elapsed += delta_ms
        advanced = False
        while self.frames and self.frame_elapsed >= self.frames[self.frame_index].duration_ms:
            self.frame_elapsed -= self.frames[self.frame_index].duration_ms
            if self.frame_index + 1 < len(self.frames):
                self.frame_index += 1
            elif self.action_loop:
                self.frame_index = 0
            else:
                self.set_action("Stand")
                break
            advanced = True

        if advanced:
            self.show_frame()
        self.render()

    def on_drag_start(self, event: tk.Event) -> None:
        self.dragging = True
        self.drag_offset_x = event.x_root - round(self.x)
        self.drag_offset_y = event.y_root - round(self.y)
        self.window.lift()
        if "Pinched" in self.character.animations:
            self.set_action("Pinched")

    def on_drag_motion(self, event: tk.Event) -> None:
        if not self.dragging:
            return
        self.x = max(
            self.left,
            min(self.right - self.width, event.x_root - self.drag_offset_x),
        )
        self.y = max(
            self.top,
            min(self.bottom - self.height, event.y_root - self.drag_offset_y),
        )
        self.render()

    def on_drag_end(self, _event: tk.Event) -> None:
        self.dragging = False
        self.set_action("Stand")
        self.next_decision = time.monotonic() + random.uniform(1.0, 3.0)

    def on_context_menu(self, event: tk.Event) -> None:
        self.app.show_context_menu(self, event)

    def bring_to_front(self) -> None:
        self.window.attributes("-topmost", True)
        self.window.lift()

    def destroy(self) -> None:
        try:
            self.window.destroy()
        except tk.TclError:
            pass


class ShimejiApp:
    def __init__(
        self,
        root: tk.Tk,
        characters: list[CharacterAssets],
        settings: dict,
    ) -> None:
        self.root = root
        self.root.withdraw()
        self.characters = characters
        self.settings = settings
        self.work_area = get_work_area(root)
        self.frame_cache = FrameCache(root)
        self.pets: list[DesktopPet] = []
        self.paused = False
        self.running = True
        self.last_tick = time.monotonic()

        self.root.title("Color Gang Shimeji - Python")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.spawn_initial_characters()
        self.root.after(self.settings["tick_ms"], self.tick)

    def add_pet(
        self,
        character: CharacterAssets,
        x: int | None = None,
    ) -> None:
        if len(self.pets) >= self.settings["max_characters"]:
            return

        if x is None:
            left, _top, right, _bottom = self.work_area
            x = random.randint(left, max(left, right - 128))
        pet = DesktopPet(self, character, x)
        self.pets.append(pet)

    def spawn_initial_characters(self) -> None:
        selected = self.characters if self.settings["start_all_characters"] else self.characters[:1]
        for character in selected[: self.settings["max_characters"]]:
            self.add_pet(character)

    def remove_pet(self, pet: DesktopPet) -> None:
        if pet in self.pets:
            self.pets.remove(pet)
            pet.destroy()

    def toggle_pause(self) -> None:
        self.paused = not self.paused

    def show_context_menu(self, pet: DesktopPet, event: tk.Event) -> None:
        menu = tk.Menu(self.root, tearoff=0)
        add_menu = tk.Menu(menu, tearoff=0)
        for character in self.characters:
            add_menu.add_command(
                label=character.display_name,
                command=lambda item=character: self.add_pet(item),
            )
        menu.add_cascade(label="Adicionar personagem", menu=add_menu)

        animation_menu = tk.Menu(menu, tearoff=0)
        preferred = [
            ("Stand", "Parado"),
            ("Walk", "Caminhar"),
            ("Run", "Correr"),
            ("Sit", "Sentar"),
            ("Dance", "Dançar"),
            ("Sprawl", "Deitar"),
            ("Tripping", "Tropeçar"),
        ]
        added = 0
        for key, label in preferred:
            if key in pet.character.animations:
                animation_menu.add_command(
                    label=label,
                    command=lambda action=key: pet.set_action(action),
                )
                added += 1
        if added:
            menu.add_cascade(label="Animação", menu=animation_menu)

        menu.add_command(
            label="Retomar todos" if self.paused else "Pausar todos",
            command=self.toggle_pause,
        )
        menu.add_command(
            label="Trazer todos para frente",
            command=lambda: [item.bring_to_front() for item in self.pets],
        )
        menu.add_command(
            label=f"Remover {pet.character.display_name}",
            command=lambda: self.remove_pet(pet),
        )
        menu.add_separator()
        menu.add_command(label="Sair", command=self.close)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def tick(self) -> None:
        if not self.running:
            return
        now = time.monotonic()
        delta_ms = max(1.0, min(100.0, (now - self.last_tick) * 1000.0))
        self.last_tick = now

        if not self.paused:
            for pet in tuple(self.pets):
                pet.step(delta_ms, now)

        self.root.after(self.settings["tick_ms"], self.tick)

    def close(self) -> None:
        if not self.running:
            return
        self.running = False
        for pet in tuple(self.pets):
            pet.destroy()
        self.pets.clear()
        self.root.destroy()


def main() -> int:
    if sys.platform != "win32":
        print("Color Gang Shimeji foi desenvolvido para Windows 10/11.")
        return 1

    try:
        print("Color Gang Shimeji: verificando os assets...")
        image_root = ensure_assets(PROJECT_ROOT, progress=print)
        characters = load_character_assets(image_root, CHARACTERS)
        settings = load_settings(PROJECT_ROOT)

        root = tk.Tk()
        ShimejiApp(root, characters, settings)
        root.mainloop()
        return 0
    except Exception as exc:
        message = (
            f"Não foi possível iniciar o Color Gang Shimeji.\n\n{exc}\n\n"
            "Confira sua conexão com a internet na primeira execução."
        )
        try:
            messagebox.showerror("Color Gang Shimeji", message)
        except tk.TclError:
            print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
