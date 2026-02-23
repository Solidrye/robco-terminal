"""
Pip-Boy style Termlink boot sequence: Phase 0 = brief Robco OS ASCII, Phase 1 = kernel scroll,
Phase 2 = system loader diagnostic with typewriter, Phase 3 = scroll off then terminal.
"""
import random
import time
import pygame
from src.scenes.base_scene import BaseScene
from src.app.constants import BLACK

# Opaque black for overlay (required for SRCALPHA surface + CRT shader)
BLACK_OPAQUE = (0, 0, 0, 255)

# Phase 0: RobCo logo (user-provided block art)
_PHASE0_ASCII = [
    "#@@@@@@@@@@@@@@@@@@*.                    %@@@@@@%-          .*@@@@@@@@@@@@@@@@@*.                   ",
    "#@@@@@@@@@@@@@@@@@@@#                    %@@@@@@@-          *@@@@@@@@@@@@@@@@@@@@=                  ",
    "#@@@@@@@@@@@@@@@@@@@#                    %@@@@@@@-          *@@@@@@@@@@@@@@@@@@@@=                  ",
    "#@@@@@@@@@@@@@@@@@@@#                    %@@@@@@@-          *@@@@@@@@@@@@@@@@@@@@=                  ",
    "#@@@@@@*    #@@@@@@@#                    %@@@@@@@-          *@@@@@@@.   +@@@@@@@@=                  ",
    "#@@@@@@*    #@@@@@@@#                    %@@@@@@@-          *@@@@@@@.   *@@@@@@@@=                  ",
    "#@@@@@@*    *@@@@@@@#                    %@@@@@@@-          *@@@@@@@.   *@@@@@@@@=                  ",
    "#@@@@@@*    *@@@@@@@# +@@@@@@@@@@@@@@@@# %@@@@@@@@@@@@@@@@# *@@@@@@@.   +########-*@@@@@@@@@@@@@@@@*",
    "#@@@@@@*-***#@@@@@@@# *@@@@@@@@@@@@@@@@@ %@@@@@@@@@@@@@@@@@:*@@@@@@@.             #@@@@@@@@@@@@@@@@#",
    "#@@@@@@*+@@@@@@@@@@@# *@@@@@@@@@@@@@@@@@ %@@@@@@@@@@@@@@@@@:*@@@@@@@.             #@@@@@@@@@@@@@@@@#",
    "#@@@@@@*+@@@@@@@@@@@# *@@@@@@@%%@@@@@@@@ %@@@@@@@@@@@@@@@@@:*@@@@@@@.             #@@@@@@@%@@@@@@@@#",
    "#@@@@@@*+@@@@@@@@@@*: *@@@@@@*  @@@@@@@@ %@@@@@@@* #@@@@@@@:*@@@@@@@.             #@@@@@@+ -@@@@@@@#",
    "#@@@@@@*+@@@@@@@-     *@@@@@@*  @@@@@@@@ %@@@@@@@* #@@@@@@@:*@@@@@@@.             #@@@@@@+ -@@@@@@@#",
    "#@@@@@@*+@@@@@@@%-    *@@@@@@*  @@@@@@@@ %@@@@@@@* #@@@@@@@:*@@@@@@@.   +@@@@@@@@-#@@@@@@+ -@@@@@@@#",
    "#@@@@@@*+@@@@@@@@*    *@@@@@@*  @@@@@@@@ %@@@@@@@* #@@@@@@@:*@@@@@@@.   +@@@@@@@@-#@@@@@@+ -@@@@@@@#",
    "#@@@@@@*-%@@@@@@@@+   *@@@@@@*  @@@@@@@@ %@@@@@@@* #@@@@@@@:*@@@@@@@.   +@@@@@@@@-#@@@@@@+ -@@@@@@@#",
    "#@@@@@@* -@@@@@@@@@+  *@@@@@@*  @@@@@@@@ %@@@@@@@* #@@@@@@@:*@@@@@@@....=@@@@@@@@-#@@@@@@+ -@@@@@@@#",
    "#@@@@@@*  +@@@@@@@@#  *@@@@@@@@@@@@@@@@@ %@@@@@@@@@@@@@@@@@:*@@@@@@@@@@@@@@@@@@@@-#@@@@@@@@@@@@@@@@#",
    "#@@@@@@*  :#@@@@@@@@* *@@@@@@@@@@@@@@@@@ %@@@@@@@@@@@@@@@@@:*@@@@@@@@@@@@@@@@@@@@-#@@@@@@@@@@@@@@@@#",
    "#@@@@@@*    %@@@@@@@@+*@@@@@@@@@@@@@@@@@ %@@@@@@@@@@@@@@@@@:*@@@@@@@@@@@@@@@@@@@@-#@@@@@@@@@@@@@@@@#",
    "#@@@@@@*    +@@@@@@@@*=@@@@@@@@@@@@@@@@+ %@@@@@@@@@@@@@@@@=  *@@@@@@@@@@@@@@@@@#. +@@@@@@@@@@@@@@@@+",
]


def _random_hex_token():
    """Single token for kernel-style lines: hex blocks (incl. 0x0000000100-style), digits, or short tech words."""
    def zero_padded_hex(total_digits, value_bits=16):
        """e.g. 0x0000000100 = 10 digits, value up to 0xFFFF."""
        n = random.randint(2, total_digits)
        zeros = total_digits - n
        val = random.randint(0, min(0xFFFFFFFF, (1 << (n * 4)) - 1))
        return "0x" + "0" * zeros + f"{val:0{n}X}"
    templates = [
        lambda: f"0x{random.randint(0, 0xFF):02X}",
        lambda: f"0x{random.randint(0, 0xFFF):03X}",
        lambda: f"0x{random.randint(0, 0xFFFF):04X}",
        lambda: f"0x{random.randint(0, 0xFFFFFF):06X}",
        lambda: f"0x{random.randint(0, 0xFFFFFFFF):08X}",
        lambda: f"0x{'0' * random.randint(6, 12)}{random.randint(0, 0xFFFF):04X}",
        lambda: "0x" + "0" * random.randint(10, 16) + f"{random.randint(0, 0xFF):02X}",
        # 0x0000000100-style: 8–12 total hex digits with leading zeros
        lambda: zero_padded_hex(8),
        lambda: zero_padded_hex(9),
        lambda: zero_padded_hex(10),
        lambda: zero_padded_hex(11),
        lambda: zero_padded_hex(12),
        lambda: "0x" + "0" * random.randint(4, 10) + f"{random.randint(0, 0xFF):02X}",
        lambda: "0x" + "0" * random.randint(4, 10) + f"{random.randint(0, 0xFFF):03X}",
        lambda: "0x" + "0" * random.randint(4, 10) + f"{random.randint(0, 0xFFFF):04X}",
        lambda: str(random.randint(0, 15)),
        lambda: str(random.randint(0, 255)),
        lambda: "CPU0",
        lambda: "CPU1",
        lambda: "EFID",
        lambda: "EFIO",
        lambda: "BIOS",
        lambda: "IRQ",
        lambda: "init",
        lambda: "stack",
        lambda: "segment",
        lambda: "relocation",
        lambda: "memory",
        lambda: "kernel",
        lambda: "cell",
        lambda: "load",
        lambda: "check",
        lambda: "launch",
        lambda: "start",
        lambda: "starting",
        lambda: "discovery",
    ]
    return random.choice(templates)()


def _random_tech_phrase():
    """Full tech phrase for kernel log lines (like Pip-Boy boot)."""
    phrases = [
        "starting EFID",
        "start memory discovery",
        "starting cell relocation",
        "CPU0 launch EFIO",
        "CPU0 starting EFIO",
        "CPU0 starting cell",
        "memory discovery",
        "kernel init",
        "load segment",
        "BIOS check",
        "stack init",
        "IRQ init",
        "relocation",
        "cell relocation",
        "memory init",
    ]
    return random.choice(phrases)


def _random_hex_only_token():
    """Hex or digit only (no tech words) for hex-heavy lines."""
    def zero_padded(total_digits):
        n = random.randint(2, total_digits)
        zeros = total_digits - n
        val = random.randint(0, min(0xFFFFFFFF, (1 << (n * 4)) - 1))
        return "0x" + "0" * zeros + f"{val:0{n}X}"
    hex_templates = [
        lambda: f"0x{random.randint(0, 0xFFFF):04X}",
        lambda: f"0x{random.randint(0, 0xFFFFFFFF):08X}",
        lambda: f"0x{'0' * random.randint(4, 10)}{random.randint(0, 0xFFFF):04X}",
        lambda: "0x" + "0" * random.randint(6, 14) + f"{random.randint(0, 0xFF):02X}",
        lambda: zero_padded(8),
        lambda: zero_padded(9),
        lambda: zero_padded(10),
        lambda: zero_padded(11),
        lambda: zero_padded(12),
        lambda: str(random.randint(0, 255)),
    ]
    return random.choice(hex_templates)()


def _build_full_kernel_line(font, max_width):
    """Build one full-width kernel-style line: lots of hex (0x0000000100-style) + tech phrase."""
    parts = []
    sep_w = font.size(" ")[0]
    width_so_far = 0
    # Heavy hex lead: 4–8 hex/digit tokens so hex dominates
    for _ in range(random.randint(4, 8)):
        token = _random_hex_only_token()
        w = font.size(token)[0]
        if width_so_far + w + (len(parts) * sep_w) <= max_width * 0.75:
            parts.append(token)
            width_so_far += w
        else:
            break
    # One tech phrase in the middle
    phrase = _random_tech_phrase()
    phrase_w = font.size(phrase)[0]
    if width_so_far + sep_w + phrase_w <= max_width:
        parts.append(phrase)
        width_so_far += sep_w + phrase_w
    # Fill remainder with hex/digits (more 0x... variations throughout)
    while width_so_far < max_width - 20:
        token = _random_hex_only_token()
        w = font.size(token)[0]
        if width_so_far + sep_w + w <= max_width:
            parts.append(token)
            width_so_far += sep_w + w
        else:
            break
    return " ".join(parts) if parts else _random_hex_token()


# Phase 2 lines: typewriter plays out in order; next line starts when previous finishes
_PHASE2_LINES = [
    "********** WELCOME TO ROBCO INDUSTRIES (TM) TERMLINK **********",
    "COPYRIGHT 2075 ROBCO(R)",
    "R0B51-V6.0",
    "EXEC VERSION 41.10",
    "64k RAM SYSTEM",
    "38911 BYTES FREE",
    "NO HOLOTAPE FOUND",
    "ESTABLISHING CONNECTION TO LOCAL HUB...",
]


class TermlinkBootScene(BaseScene):
    """Pip-Boy style boot: Phase 0 = Robco OS ASCII, Phase 1 = kernel scroll, Phase 2 = typewriter, Phase 3 = scroll off."""

    PHASE0_DURATION = 1.0   # very brief Robco OS splash before kernel scroll
    PHASE1_DURATION = 4.4   # extended by 1 second from 3.4
    BLACK_BLINK_DURATION = 0.2
    # Phase 1: smooth pixel scroll (kernel-style); twice as fast
    PHASE1_SCROLL_SPEED = 960.0  # pixels per second (was 480)
    PHASE1_LINE_INTERVAL_MS = 10  # add a batch every 10 ms (was 20)
    PHASE1_LINES_PER_BATCH = 6   # more lines per batch (was 4)
    # Phase 2 typing: paced to finish in PHASE2_TARGET_DURATION_SEC (set to match your sound length)
    PHASE2_TARGET_DURATION_SEC = 4.2   # total time for all Phase 2 text; matches sound effect
    PHASE2_BANNER_TIME_RATIO = 0.15    # banner uses 15% of time, rest 85%
    PHASE2_BLANK_LINES_AFTER_BANNER = 2  # vertical space between banner and rest
    PHASE3_DELAY_AFTER_TYPING_SEC = 1.0  # pause before scroll-off starts
    PHASE3_SCROLL_SPEED = 1200  # pixels per second (scroll Phase 2 content up and off)
    PHASE3_DELAY_AFTER_WIPE_SEC = 0.5   # pause after wipe before terminal appears

    def __init__(self, app):
        super().__init__(app)
        self._phase = 0
        self._start_time_sec = 0.0
        self._black_until_sec = None
        self._phase1_lines = []  # full lines only (kernel log)
        self._phase1_scroll_y = 0.0  # smooth pixel offset (increases each frame)
        self._phase1_last_tick_ms = 0
        self._phase1_next_batch_ms = 0
        self._phase2_line_index = 0
        self._phase2_blank_lines_remaining = 0  # blanks between banner and rest
        self._phase2_rest_delay = None  # char_delay for rest of Phase 2 (computed from target duration)
        self._saved_char_delay = None
        self._saved_on_output_added = None  # restored when leaving Phase 2
        self._phase3_scroll_y = 0.0
        self._phase3_start_sec = 0.0
        self._phase3_wipe_sound_played = False
        self._phase3_wipe_done_sec = None
        self._phase3_lines = []

    def enter(self):
        self._phase = 0
        self._start_time_sec = pygame.time.get_ticks() / 1000.0
        self._black_until_sec = None
        self._phase1_lines = []
        self._phase1_scroll_y = 0.0
        self._phase1_last_tick_ms = pygame.time.get_ticks()
        self._phase1_next_batch_ms = self._phase1_last_tick_ms
        # Pre-seed one batch for when Phase 1 starts
        font = self.app.text_renderer.font
        margin_x = self.app.text_renderer.margin[0] if self.app.text_renderer.margin else 50
        w = self.app.screen.overlay.get_width()
        max_width = max(100, w - 2 * margin_x)
        for _ in range(self.PHASE1_LINES_PER_BATCH):
            self._phase1_lines.append(_build_full_kernel_line(font, max_width))
        self._phase2_line_index = 0
        self._phase3_scroll_y = 0.0
        self._phase3_start_sec = 0.0
        self._phase3_wipe_sound_played = False
        self._phase3_wipe_done_sec = None
        self._phase3_lines = []
        self.app.text_renderer.set_text([])
        self.app.text_renderer.finish_rendering()
        self.app.is_rendering = True
        self.app.state_transition = False
        self._saved_char_delay = self.app.text_renderer.char_delay
        # Phase 2 char_delay is set when Phase 2 starts (from PHASE2_TARGET_DURATION_SEC)
        self.app.text_renderer.centered_line_indices = {0}  # center welcome line in Phase 2
        self._saved_on_output_added = self.app.text_renderer.on_output_added

    def _on_phase2_line_finished(self):
        """Append next Phase 2 line when typewriter finishes current line. No return sound in Phase 2."""
        if self._phase2_blank_lines_remaining > 0:
            self._phase2_blank_lines_remaining -= 1
            return
        if self._phase2_line_index >= len(_PHASE2_LINES):
            return
        if self._phase2_line_index == 1:
            # Banner just finished: add blank lines, then queue rest at target-paced delay
            if self._phase2_rest_delay is not None:
                self.app.text_renderer.char_delay = self._phase2_rest_delay
            self._phase2_blank_lines_remaining = self.PHASE2_BLANK_LINES_AFTER_BANNER
            for _ in range(self.PHASE2_BLANK_LINES_AFTER_BANNER):
                self.app.text_renderer.append_text("")
            self.app.text_renderer.append_text(_PHASE2_LINES[1])
            self._phase2_line_index = 2
        else:
            self.app.text_renderer.append_text(_PHASE2_LINES[self._phase2_line_index])
            self._phase2_line_index += 1

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            return False
        return False

    def update(self):
        t = pygame.time.get_ticks() / 1000.0 - self._start_time_sec

        if self._phase == 0:
            if t >= self.PHASE0_DURATION:
                self._phase = 1
                self._phase1_last_tick_ms = pygame.time.get_ticks()
                self._phase1_next_batch_ms = self._phase1_last_tick_ms
                if getattr(self.app, "boot_scroll_sound", None) is not None:
                    self.app.boot_scroll_sound.play()
            return

        if self._phase == 1:
            if t >= self.PHASE1_DURATION:
                self._black_until_sec = t + self.BLACK_BLINK_DURATION
                self._phase = "black"
                return
            now_ms = pygame.time.get_ticks()
            dt_sec = (now_ms - self._phase1_last_tick_ms) / 1000.0
            self._phase1_last_tick_ms = now_ms
            self._phase1_scroll_y += self.PHASE1_SCROLL_SPEED * dt_sec
            if now_ms >= self._phase1_next_batch_ms:
                self._add_phase1_batch()
                self._phase1_next_batch_ms = now_ms + self.PHASE1_LINE_INTERVAL_MS
            line_height = self.app.text_renderer.line_height or 30
            margin_y = self.app.text_renderer.margin[1] if self.app.text_renderer.margin else 50
            h = self.app.screen.overlay.get_height()
            visible_h = h - 2 * margin_y
            max_scroll = max(0.0, len(self._phase1_lines) * line_height - visible_h)
            self._phase1_scroll_y = min(self._phase1_scroll_y, max_scroll)
            return

        if self._phase == "black":
            if t >= self._black_until_sec:
                self._phase = 2
                scroll_sound = getattr(self.app, "boot_scroll_sound", None)
                if scroll_sound is not None:
                    try:
                        scroll_sound.stop()
                    except AttributeError:
                        for i in range(pygame.mixer.get_num_channels()):
                            ch = pygame.mixer.Channel(i)
                            if ch.get_busy() and ch.get_sound() is scroll_sound:
                                ch.stop()
                                break
                self.app.text_renderer.finish_rendering_requested = False  # so Phase 2 typewriter animates
                self.app.text_renderer.on_output_added = self._on_phase2_line_finished
                # Pace typing so it finishes in PHASE2_TARGET_DURATION_SEC (deterministic, sync to sound)
                total_chars = sum(len(s) for s in _PHASE2_LINES)
                banner_chars = len(_PHASE2_LINES[0])
                rest_chars = total_chars - banner_chars
                if banner_chars > 0:
                    banner_time = self.PHASE2_TARGET_DURATION_SEC * self.PHASE2_BANNER_TIME_RATIO
                    self.app.text_renderer.char_delay = banner_time / banner_chars
                if rest_chars > 0:
                    rest_time = self.PHASE2_TARGET_DURATION_SEC * (1.0 - self.PHASE2_BANNER_TIME_RATIO)
                    self._phase2_rest_delay = rest_time / rest_chars
                self.app.text_renderer.last_update_time = time.time()  # so pacing starts from now, not from enter()
                self.app.text_renderer.append_text(_PHASE2_LINES[0])
                self._phase2_line_index = 1
                if getattr(self.app, "boot_type_sound", None) is not None:
                    self.app.boot_type_sound.play()
            return

        if self._phase == 2:
            # Transition to Phase 3 only when all lines are queued and typewriter has finished
            if self._phase2_line_index >= len(_PHASE2_LINES) and not self.app.text_renderer.is_rendering():
                self._phase = 3
                self._phase3_lines = list(self.app.text_renderer.full_text_lines)
                self._phase3_start_sec = t + self.PHASE3_DELAY_AFTER_TYPING_SEC
                self._phase3_wipe_sound_played = False
                self.app.text_renderer.centered_line_indices = set()
                self.app.text_renderer.on_output_added = self._saved_on_output_added
                if self._saved_char_delay is not None:
                    self.app.text_renderer.char_delay = self._saved_char_delay
            return

        if self._phase == 3:
            self._phase3_scroll_y = max(0.0, (t - self._phase3_start_sec) * self.PHASE3_SCROLL_SPEED)
            if not self._phase3_wipe_sound_played and t >= self._phase3_start_sec:
                self._phase3_wipe_sound_played = True
                if getattr(self.app, "boot_wipe_sound", None) is not None:
                    self.app.boot_wipe_sound.play()
            line_height = self.app.text_renderer.line_height
            margin_y = self.app.text_renderer.margin[1]
            total_height = margin_y + len(self._phase3_lines) * line_height
            if self._phase3_scroll_y >= total_height:
                if self._phase3_wipe_done_sec is None:
                    self._phase3_wipe_done_sec = t
                if t - self._phase3_wipe_done_sec >= self.PHASE3_DELAY_AFTER_WIPE_SEC:
                    self.app.set_scene(self.app.config.scene_after_boot)

    def render(self):
        t = pygame.time.get_ticks() / 1000.0 - self._start_time_sec

        if self._phase == 0:
            self._render_phase0()
            return
        if self._phase == "black":
            self.app.screen.overlay.fill(BLACK_OPAQUE)
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

    def _render_phase0(self):
        """Brief Robco OS ASCII splash (centered), then Phase 1 starts."""
        overlay = self.app.screen.overlay
        overlay.fill(BLACK_OPAQUE)
        font = self.app.text_renderer.font
        color = self.app.text_renderer.color
        line_height = self.app.text_renderer.line_height or 30
        w = overlay.get_width()
        h = overlay.get_height()
        total_h = len(_PHASE0_ASCII) * line_height
        y0 = (h - total_h) // 2
        for i, line in enumerate(_PHASE0_ASCII):
            surf = font.render(line, True, color)
            x = (w - surf.get_width()) // 2
            y = y0 + i * line_height
            overlay.blit(surf, (x, y))

    def _add_phase1_batch(self):
        """Append a batch of full kernel-style lines (hex + tech phrases)."""
        font = self.app.text_renderer.font
        margin_x = self.app.text_renderer.margin[0] if self.app.text_renderer.margin else 50
        w = self.app.screen.overlay.get_width()
        max_width = max(100, w - 2 * margin_x)
        for _ in range(self.PHASE1_LINES_PER_BATCH):
            line = _build_full_kernel_line(font, max_width)
            self._phase1_lines.append(line)

    def _render_phase1(self):
        """Kernel-style boot: smooth pixel scroll, full lines only (no typing effect)."""
        overlay = self.app.screen.overlay
        overlay.fill(BLACK_OPAQUE)
        font = self.app.text_renderer.font
        color = self.app.text_renderer.color
        line_height = self.app.text_renderer.line_height or 30
        margin_x = self.app.text_renderer.margin[0] if self.app.text_renderer.margin else 50
        margin_y = self.app.text_renderer.margin[1] if self.app.text_renderer.margin else 50
        h = overlay.get_height()

        for i, line in enumerate(self._phase1_lines):
            y = margin_y + i * line_height - self._phase1_scroll_y
            if y < -line_height or y > h + line_height:
                continue
            surf = font.render(line, True, color)
            overlay.blit(surf, (margin_x, int(y)))

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
            x = (overlay.get_width() - surf.get_width()) // 2 if i == 0 else margin_x
            overlay.blit(surf, (x, y))
