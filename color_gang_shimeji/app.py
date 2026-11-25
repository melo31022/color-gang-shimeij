"""Tkinter desktop-pet application for Windows."""
from __future__ import annotations

import ctypes
import json
import os
import random
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from .core import Character, load_catalog
from .motion import choose_direction, clamp


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRANSPARENT_COLOR = "#ff00ff"

DEFAULT_SETTINGS = {
    "start_all_characters": True,
    "max_characters": 12,
    "speed": 1.35,
    "tick_ms": 32,
    "gravity": 0.46,
    "jump_strength": 8.2,
    "jump_probability": 0.0018,
    "idle_min_seconds": 0.8,
    "idle_max_seconds": 2.8,
    "walk_min_seconds": 1.4,
    "walk_max_seconds": 4.2,
}


def load_settings(project_root: Path) -> dict:
    """Read settings.json, filling in omitted values with safe defaults."""
    path = project_root / "settings.json"
    if not path.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        supplied = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(supplied, dict):
        raise ValueError("settings.json must contain a JSON object.")

    settings = DEFAULT_SETTINGS | supplied
    settings["max_characters"] = max(1, min(50, int(settings["max_characters"])))
    settings["tick_ms"] = max(16, min(100, int(settings["tick_ms"])))
    settings["speed"] = clamp(float(settings["speed"]), 0.2, 8.0)
    settings["gravity"] = clamp(float(settings["gravity"]), 0.1, 2.0)
    settings["jump_strength"] = clamp(float(settings["jump_strength"]), 2.0, 20.0)
    settings["jump_probability"] = clamp(float(settings["jump_probability"]), 0.0, 0.02)
    for low, high in (
        ("idle_min_seconds", "idle_max_seconds"),
        ("walk_min_seconds", "walk_max_seconds"),
    ):
        settings[low] = max(0.1, float(settings[low]))
        settings[high] = max(settings[low], float(settings[high]))
    return settings


def get_work_area(root: tk.Tk) -> tuple[int, int, int, int]:
    """Return the Windows desktop work area, excluding the taskbar."""
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


class DesktopPet:
    """One transparent, always-on-top character window."""

    def __init__(
        self,
        app: "ShimejiApp",
        character: Character,
        photo: tk.PhotoImage,
        x: float,
    ) -> None:
        self.app = app
        self.character = character
        self.photo = photo
        self.width = photo.width()
        self.height = photo.height()

        self.left, self.top, self.right, self.bottom = app.work_area
        self.x = clamp(x, self.left, max(self.left, self.right - self.width))
        self.ground_y = max(self.top, self.bottom - self.height)
        self.y = float(self.ground_y)

        self.direction = choose_direction()
        self.mode = "walk"
        self.velocity_y = 0.0
        self.dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.next_decision = time.monotonic() + random.uniform(0.5, 2.0)
        self.last_geometry: tuple[int, int] | None = None

        self.window = tk.Toplevel(app.root)
        self.window.overrideredirect(True)
        self.window.configure(bg=TRANSPARENT_COLOR)
        self.window.wm_attributes("-topmost", True)
        try:
            self.window.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        except tk.TclError as exc:
            self.window.destroy()
            raise RuntimeError(
                "A transparência por cor não está disponível nesta instalação do Tk. "
                "Use Python para Windows com Tcl/Tk 8.6."
            ) from exc

        self.label = tk.Label(
            self.window,
            image=self.photo,
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

        self.render()

    def render(self) -> None:
        position = (round(self.x), round(self.y))
        if position != self.last_geometry:
            self.window.geometry(
                f"{self.width}x{self.height}+{position[0]}+{position[1]}"
            )
            self.last_geometry = position

    def step(self, now: float) -> None:
        if self.dragging:
            return

        settings = self.app.settings

        if self.y < self.ground_y or self.velocity_y != 0:
            self.y += self.velocity_y
            self.velocity_y += settings["gravity"]
            if self.y >= self.ground_y:
                self.y = float(self.ground_y)
                self.velocity_y = 0.0

        if self.velocity_y == 0 and now >= self.next_decision:
            if random.random() < 0.38:
                self.mode = "idle"
                self.direction = 0
                self.next_decision = now + random.uniform(
                    settings["idle_min_seconds"], settings["idle_max_seconds"]
                )
            else:
                self.mode = "walk"
                self.direction = choose_direction()
                self.next_decision = now + random.uniform(
                    settings["walk_min_seconds"], settings["walk_max_seconds"]
                )

        if self.mode == "walk":
            self.x += self.direction * settings["speed"]

        if self.x <= self.left:
            self.x = float(self.left)
            self.direction = 1
            self.mode = "walk"
        elif self.x >= self.right - self.width:
            self.x = float(max(self.left, self.right - self.width))
            self.direction = -1
            self.mode = "walk"

        if self.velocity_y == 0 and random.random() < settings["jump_probability"]:
            self.velocity_y = -settings["jump_strength"]

        self.render()

    def on_drag_start(self, event: tk.Event) -> None:
        self.dragging = True
        self.direction = 0
        self.mode = "idle"
        self.velocity_y = 0.0
        self.drag_offset_x = event.x_root - self.x
        self.drag_offset_y = event.y_root - self.y
        self.window.lift()

    def on_drag_motion(self, event: tk.Event) -> None:
        if not self.dragging:
            return
        self.x = clamp(
            event.x_root - self.drag_offset_x,
            self.left,
            max(self.left, self.right - self.width),
        )
        self.y = clamp(
            event.y_root - self.drag_offset_y,
            self.top,
            max(self.top, self.bottom - self.height),
        )
        self.render()

    def on_drag_end(self, _event: tk.Event) -> None:
        self.dragging = False
        self.next_decision = time.monotonic() + random.uniform(0.5, 1.5)

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
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.withdraw()
        self.settings = load_settings(PROJECT_ROOT)
        self.characters = load_catalog(PROJECT_ROOT)
        self.work_area = get_work_area(root)
        self.photos: dict[str, tk.PhotoImage] = {}
        self.pets: list[DesktopPet] = []
        self.paused = False
        self.running = True

        self.root.title("Color Gang Shimeji")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.spawn_initial_characters()
        self.root.after(self.settings["tick_ms"], self.tick)

    def get_photo(self, character: Character) -> tk.PhotoImage:
        photo = self.photos.get(character.character_id)
        if photo is None:
            photo = tk.PhotoImage(master=self.root, file=str(character.sprite))
            self.photos[character.character_id] = photo
        return photo

    def add_pet(self, character: Character, x: float | None = None) -> None:
        if len(self.pets) >= self.settings["max_characters"]:
            return

        photo = self.get_photo(character)
        left, _top, right, _bottom = self.work_area
        available = max(0, right - left - photo.width())
        if x is None:
            x = random.randint(left, left + available) if available else left

        pet = DesktopPet(self, character, photo, x)
        self.pets.append(pet)

    def spawn_initial_characters(self) -> None:
        if self.settings["start_all_characters"]:
            selected = self.characters
        else:
            selected = self.characters[:1]

        for character in selected[: self.settings["max_characters"]]:
            self.add_pet(character)

    def remove_pet(self, pet: DesktopPet) -> None:
        if pet in self.pets:
            self.pets.remove(pet)
            pet.destroy()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if not self.paused:
            now = time.monotonic()
            for pet in self.pets:
                pet.next_decision = now + random.uniform(0.2, 1.0)

    def show_context_menu(self, pet: DesktopPet, event: tk.Event) -> None:
        menu = tk.Menu(self.root, tearoff=0)
        add_menu = tk.Menu(menu, tearoff=0)
        for character in self.characters:
            add_menu.add_command(
                label=character.name,
                command=lambda item=character: self.add_pet(item),
            )
        menu.add_cascade(label="Adicionar personagem", menu=add_menu)
        menu.add_command(
            label="Retomar todos" if self.paused else "Pausar todos",
            command=self.toggle_pause,
        )
        menu.add_command(
            label="Trazer todos para frente",
            command=lambda: [item.bring_to_front() for item in self.pets],
        )
        menu.add_command(
            label=f"Remover {pet.character.name}",
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
        if not self.paused:
            now = time.monotonic()
            for pet in tuple(self.pets):
                pet.step(now)
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
        root = tk.Tk()
        ShimejiApp(root)
        root.mainloop()
        return 0
    except (OSError, ValueError, FileNotFoundError, RuntimeError, tk.TclError) as exc:
        try:
            messagebox.showerror("Color Gang Shimeji", str(exc))
        except tk.TclError:
            print(f"Color Gang Shimeji: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
