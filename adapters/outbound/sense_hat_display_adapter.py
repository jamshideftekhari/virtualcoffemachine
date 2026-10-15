from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass

from sense_hat import SenseHat

from adapters.outbound import sense_hat_icons as icons

logger = logging.getLogger("coffee_machine.display")

BREWING_SECONDS = 10.0
SCROLL_SPEED = 0.06  # seconds per column when scrolling text


@dataclass(frozen=True)
class _Animation:
    frames: tuple[list[icons.Pixel], ...]
    frame_seconds: float
    total_seconds: float


@dataclass(frozen=True)
class _Text:
    text: str
    colour: icons.Pixel


@dataclass(frozen=True)
class _Scene:
    """A sequence of steps played in a loop."""

    steps: tuple[_Animation | _Text, ...]


def _ready_scene() -> _Scene:
    return _Scene((
        _Animation((icons.MACHINE, icons.MACHINE_LED_OFF), 0.5, 3.0),
        _Text("Welcome", icons.TEXT_WHITE),
    ))


def _brewing_scene(beverage_name: str) -> _Scene:
    return _Scene((
        _Animation((icons.CUP_STEAM_1, icons.CUP_STEAM_2), 0.3, 2.0),
        _Text(beverage_name, icons.TEXT_COFFEE),
    ))


def _error_scene(message: str) -> _Scene:
    return _Scene((
        _Animation((icons.ERROR, icons.BLANK), 0.5, 2.0),
        _Text(message, icons.TEXT_RED),
    ))


def _rejected_scene(message: str) -> _Scene:
    return _Scene((
        _Animation((icons.WARNING,), 1.5, 1.5),
        _Text(message, icons.TEXT_YELLOW),
    ))


class SenseHatDisplayAdapter:
    """
    Driven adapter — shows the machine status on the Raspberry Pi Sense HAT LED matrix.

    The port methods only swap the current scene; a background thread does the
    drawing, so API requests never wait for the (slow, blocking) LED rendering.

    Two layers:
    - base scene: follows the machine state (READY → welcome, ERROR → error)
    - overlay:    a temporary scene (brewing, rejected) played on top of the base
                  until it has run for its duration, then the base comes back
    """

    def __init__(self, rotation: int = 0) -> None:
        self._sense = SenseHat()  # raises OSError when no Sense HAT is attached
        self._sense.set_rotation(rotation)

        self._lock = threading.Lock()
        self._wake = threading.Event()  # set whenever the visible scene changes
        self._stop = threading.Event()
        self._version = 0
        self._base = _ready_scene()
        self._overlay: _Scene | None = None
        self._overlay_until = 0.0

        self._thread = threading.Thread(target=self._run, name="sense-hat-display", daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    # DisplayPort
    # ------------------------------------------------------------------

    def show_ready(self) -> None:
        self._set_base(_ready_scene())

    def show_error(self, message: str) -> None:
        self._set_base(_error_scene(message), clear_overlay=True)

    def show_brewing(self, beverage_name: str) -> None:
        self._set_overlay(_brewing_scene(beverage_name), BREWING_SECONDS)

    def show_rejected(self, message: str) -> None:
        self._set_overlay(_rejected_scene(message), 0.0)  # play once

    def close(self) -> None:
        """Stop the render thread and switch the LEDs off."""
        self._stop.set()
        self._wake.set()
        # A text scroll in progress can't be interrupted, so allow it to finish.
        self._thread.join(timeout=10)

    # ------------------------------------------------------------------
    # Scene switching (called from request threads)
    # ------------------------------------------------------------------

    def _set_base(self, scene: _Scene, clear_overlay: bool = False) -> None:
        with self._lock:
            self._base = scene
            if clear_overlay:
                self._overlay = None
            if self._overlay is None:  # base is visible → redraw now
                self._interrupt()

    def _set_overlay(self, scene: _Scene, seconds: float) -> None:
        with self._lock:
            self._overlay = scene
            self._overlay_until = time.monotonic() + seconds
            self._interrupt()

    def _interrupt(self) -> None:
        # Caller holds self._lock
        self._version += 1
        self._wake.set()

    # ------------------------------------------------------------------
    # Rendering (background thread)
    # ------------------------------------------------------------------

    def _run(self) -> None:
        while not self._stop.is_set():
            with self._lock:
                self._wake.clear()
                version = self._version
                is_overlay = self._overlay is not None
                scene = self._overlay if is_overlay else self._base

            try:
                completed = self._play(scene)
            except Exception:
                logger.exception("Sense HAT rendering failed")
                self._stop.wait(1.0)
                continue

            if completed and is_overlay:
                with self._lock:
                    if self._version == version and time.monotonic() >= self._overlay_until:
                        self._overlay = None

        self._sense.clear()

    def _play(self, scene: _Scene) -> bool:
        """Play one pass of the scene. Returns False if interrupted by a scene change."""
        for step in scene.steps:
            if self._wake.is_set():
                return False
            if isinstance(step, _Text):
                self._sense.show_message(step.text, scroll_speed=SCROLL_SPEED, text_colour=step.colour)
            elif not self._animate(step):
                return False
        return not self._wake.is_set()

    def _animate(self, animation: _Animation) -> bool:
        deadline = time.monotonic() + animation.total_seconds
        frame = 0
        while time.monotonic() < deadline:
            self._sense.set_pixels(animation.frames[frame % len(animation.frames)])
            frame += 1
            if self._wake.wait(animation.frame_seconds):
                return False
        return True
