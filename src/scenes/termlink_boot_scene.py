"""
Pip-Boy style Termlink boot sequence: Phase 1 = high-speed memory dump scroll,
Phase 2 = system loader diagnostic with typewriter, Phase 3 = scroll off then terminal.
"""
import random
import pygame
from src.scenes.base_scene import BaseScene
from src.app.constants import BLACK


def _random_hex_line():
    """Generate a random hex/kernel-style line for Phase 1."""
    templates = [
        lambda: f"0x{random.randint(0, 0xFFFF):04X}{random.randint(0, 0xFFFF):04X}",
        lambda: f"CPU0: starting cell 0x{random.randint(0, 0xFF):02X}",
        lambda: f"relocation 0x{random.randint(0, 0xFFFFFF):06X}",
        lambda: "memory discovery",
        lambda: "kernel init",
        lambda: f"0x{random.randint(0, 0xFFFFFFFF):08X}",
        lambda: f"load segment 0x{random.randint(0, 0xFF):02X}",
        lambda: "BIOS check",
        lambda: f"stack 0x{random.randint(0, 0xFFFF):04X}",
        lambda: "IRQ init",
    ]
    return random.choice(templates)()


# Phase 2 lines: (time in seconds from scene start, text)
_PHASE2_LINES = [
    (4.5, "********** WELCOME TO ROBCO INDUSTRIES (TM) TERMLINK **********"),
    (5.5, "COPYRIGHT 2075 ROBCO(R)"),
    (6.0, "R0B51-V6.0"),
    (6.5, "EXEC VERSION 41.10"),
    (7.0, "64k RAM SYSTEM"),
    (7.5, "38911 BYTES FREE"),
    (8.0, "NO HOLOTAPE FOUND"),
    (8.5, "ESTABLISHING CONNECTION TO LOCAL HUB..."),
]


class TermlinkBootScene(BaseScene):
    """Pip-Boy style boot: Phase 1 = fast hex scroll, Phase 2 = typewriter loader, Phase 3 = scroll off then terminal."""

    PHASE1_DURATION = 3.3
    BLACK_BLINK_DURATION = 0.2
    LINE_INTERVAL_MS = 25
    TYPEWRITER_CHAR_DELAY = 0.025
    PHASE3_SCROLL_SPEED = 120  # pixels per second

    def __init__(self, app):
        super().__init__(app)
        self._phase = 1
        self._start_time_sec = 0.0
        self._black_until_sec = None
        self._phase1_lines = []
        self._phase1_scroll_y = 0
        self._last_line_time_sec = 0.0
        self._phase2_line_index = 0
        self._saved_char_delay = None
        self._phase3_scroll_y = 0.0
        self._phase3_start_sec = 0.0
        self._phase3_lines = []

    def enter(self):
        self._phase = 1
        self._start_time_sec = pygame.time.get_ticks() / 1000.0
        self._black_until_sec = None
        self._phase1_lines = []
        self._phase1_scroll_y = 0
        self._last_line_time_sec = self._start_time_sec
        self._phase2_line_index = 0
        self._phase3_scroll_y = 0.0
        self._phase3_start_sec = 0.0
        self._phase3_lines = []
        self.app.text_renderer.set_text([])
        self.app.text_renderer.finish_rendering()
        self.app.is_rendering = True
        self.app.state_transition = False
        self._saved_char_delay = self.app.text_renderer.char_delay
        self.app.text_renderer.char_delay = self.TYPEWRITER_CHAR_DELAY
        if getattr(self.app, "boot_scroll_sound", None) is not None:
            self.app.boot_scroll_sound.play()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            return False
        return False

    def update(self):
        t = pygame.time.get_ticks() / 1000.0 - self._start_time_sec

        if self._phase == 1:
            if t >= self.PHASE1_DURATION:
                self._black_until_sec = t + self.BLACK_BLINK_DURATION
                self._phase = "black"
                return
            if t - self._last_line_time_sec >= self.LINE_INTERVAL_MS / 1000.0:
                self._last_line_time_sec = t
                self._phase1_lines.append(_random_hex_line())
            self._phase1_scroll_y += self.app.text_renderer.line_height * 0.5
            return

        if self._phase == "black":
            if t >= self._black_until_sec:
                self._phase = 2
                if getattr(self.app, "boot_type_sound", None) is not None:
                    self.app.boot_type_sound.play()
            return

        if self._phase == 2:
            for i, (line_time, line_text) in enumerate(_PHASE2_LINES):
                if i == self._phase2_line_index and t >= line_time:
                    self.app.text_renderer.append_text(line_text)
                    self._phase2_line_index += 1
                    break
            if self._phase2_line_index >= len(_PHASE2_LINES):
                if not self.app.text_renderer.is_rendering() or t > 12.0:
                    self._phase = 3
                    self._phase3_lines = list(self.app.text_renderer.full_text_lines)
                    self._phase3_start_sec = t
                    if getattr(self.app, "boot_wipe_sound", None) is not None:
                        self.app.boot_wipe_sound.play()
                    if self._saved_char_delay is not None:
                        self.app.text_renderer.char_delay = self._saved_char_delay
            return

        if self._phase == 3:
            self._phase3_scroll_y = (t - self._phase3_start_sec) * self.PHASE3_SCROLL_SPEED
            line_height = self.app.text_renderer.line_height
            margin_y = self.app.text_renderer.margin[1]
            total_height = margin_y + len(self._phase3_lines) * line_height
            if self._phase3_scroll_y >= total_height:
                self.app.set_scene(self.app.config.scene_after_boot)

    def render(self):
        t = pygame.time.get_ticks() / 1000.0 - self._start_time_sec

        if self._phase == "black":
            self.app.screen.overlay.fill(BLACK)
            return

        if self._phase == 1:
            self._render_phase1()
            return

        if self._phase == 2:
            self.app.text_renderer.update()
            self.app.is_rendering = self.app.text_renderer.is_rendering()
            self.app.text_renderer.enable_cursor()
            self.app.text_renderer.render()
            return

        if self._phase == 3:
            self._render_phase3()
            return

    def _render_phase1(self):
        """Draw scrolling hex lines (bottom to top)."""
        overlay = self.app.screen.overlay
        overlay.fill(BLACK)
        font = self.app.text_renderer.font
        color = self.app.text_renderer.color
        line_height = self.app.text_renderer.line_height
        margin_x = self.app.text_renderer.margin[0]
        h = overlay.get_height()

        for i, line in enumerate(self._phase1_lines):
            y = h - self._phase1_scroll_y + i * line_height
            if y < -line_height or y > h + line_height:
                continue
            surf = font.render(line, True, color)
            overlay.blit(surf, (margin_x, y))

    def _render_phase3(self):
        """Scroll Phase 2 lines up and off the screen."""
        overlay = self.app.screen.overlay
        overlay.fill(BLACK)
        if not self._phase3_lines:
            return
        font = self.app.text_renderer.font
        color = self.app.text_renderer.color
        line_height = self.app.text_renderer.line_height
        margin_x = self.app.text_renderer.margin[0]
        margin_y = self.app.text_renderer.margin[1]
        h = overlay.get_height()

        for i, line in enumerate(self._phase3_lines):
            y = margin_y - self._phase3_scroll_y + i * line_height
            if y < -line_height or y > h + line_height:
                continue
            surf = font.render(line, True, color)
            overlay.blit(surf, (margin_x, y))
