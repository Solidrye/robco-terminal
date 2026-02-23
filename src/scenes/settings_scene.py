"""
Settings scene: sliders for CRT effect parameters, real-time feedback, Save to persist.
Open with F10 from any scene; Esc or Back returns to previous scene.
"""
import pygame
from src.scenes.base_scene import BaseScene
from src.app.constants import GREEN, BLACK


# (key, label, min, max)
SLIDER_SPECS = [
    ("luminance_intensity", "Luminance", 0.5, 5.0),
    ("bloom_threshold", "Bloom threshold", 0.0, 0.5),
    ("bloom_extract_threshold", "Bloom extract", 0.05, 0.5),
    ("bloom_strength", "Bloom strength", 0.0, 1.0),
    ("bloom_offset", "Bloom offset", 0.0, 0.01),
    ("bloom_depth", "Bloom depth (Z)", 0.0, 1.0),
    ("blur_strength", "Blur strength", 0.0, 0.8),
    ("blur_offset", "Blur offset", 0.0, 0.02),
    ("black_level", "Black level", 0.0, 0.2),
    ("scanline_factor", "Scanlines", 0.0, 0.8),
    ("grain_intensity", "Grain", 0.0, 0.1),
    ("curve_intensity", "Curve", 0.0, 0.8),
]

TRACK_W = 280
TRACK_H = 12
THUMB_W = 14
THUMB_H = 18
SLIDER_Y_OFFSET = 4
MARGIN_LEFT = 50
MARGIN_TOP = 50
LABEL_W = 200
VALUE_W = 80
LINE_HEIGHT = 32
BUTTON_LINE = 420
BUTTON_W = 120
BUTTON_H = 28


class SettingsScene(BaseScene):
    def __init__(self, app):
        super().__init__(app)
        self._dragging_key = None
        self._save_flash_until = 0.0

    def enter(self):
        pass

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.set_scene(self.app.previous_scene_name)
                return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._on_mouse_down(event.pos)
            return False
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging_key = None
            return False
        if event.type == pygame.MOUSEMOTION and self._dragging_key:
            self._on_mouse_drag(event.pos)
            return False
        return False

    def _track_rect(self, index):
        """Return the track rect for slider at index (for hit-test and thumb position)."""
        y = MARGIN_TOP + index * LINE_HEIGHT + SLIDER_Y_OFFSET
        return pygame.Rect(MARGIN_LEFT + LABEL_W, y, TRACK_W, TRACK_H)

    def _slider_rects(self, index):
        """Return (track_rect, thumb_rect) for slider at index (0-based)."""
        track = self._track_rect(index)
        key = SLIDER_SPECS[index][0]
        s = self.app.crt_settings
        val = getattr(s, key)
        spec = SLIDER_SPECS[index]
        mn, mx = spec[2], spec[3]
        t = (val - mn) / (mx - mn) if mx > mn else 0.0
        t = max(0.0, min(1.0, t))
        thumb_x = track.x + t * (track.w - THUMB_W)
        thumb = pygame.Rect(thumb_x, track.centery - THUMB_H // 2, THUMB_W, THUMB_H)
        return track, thumb

    def _slider_row_hit_rect(self, index):
        """Full-row rect for easier clicking: track area + a bit of padding (label/value not included)."""
        track = self._track_rect(index)
        row_y = MARGIN_TOP + index * LINE_HEIGHT
        return pygame.Rect(track.x, row_y, track.w + VALUE_W + 20, LINE_HEIGHT)

    def _value_at_x(self, index, px):
        track = self._track_rect(index)
        spec = SLIDER_SPECS[index]
        mn, mx = spec[2], spec[3]
        rel = (px - track.x) / track.w if track.w else 0
        rel = max(0.0, min(1.0, rel))
        return mn + rel * (mx - mn)

    def _on_mouse_down(self, pos):
        # Check Save button
        save_rect = pygame.Rect(MARGIN_LEFT, BUTTON_LINE, BUTTON_W, BUTTON_H)
        if save_rect.collidepoint(pos):
            self.app.crt_settings.save()
            self._save_flash_until = pygame.time.get_ticks() / 1000.0 + 0.5
            return
        # Check Back button
        back_rect = pygame.Rect(MARGIN_LEFT + BUTTON_W + 20, BUTTON_LINE, BUTTON_W, BUTTON_H)
        if back_rect.collidepoint(pos):
            self.app.set_scene(self.app.previous_scene_name)
            return
        # Check sliders (use full-row hit area so every slider is easy to hit)
        for i in range(len(SLIDER_SPECS)):
            row_rect = self._slider_row_hit_rect(i)
            if row_rect.collidepoint(pos):
                self._dragging_key = SLIDER_SPECS[i][0]
                val = self._value_at_x(i, pos[0])
                setattr(self.app.crt_settings, self._dragging_key, val)
                return

    def _on_mouse_drag(self, pos):
        if not self._dragging_key:
            return
        for i in range(len(SLIDER_SPECS)):
            if SLIDER_SPECS[i][0] == self._dragging_key:
                val = self._value_at_x(i, pos[0])
                spec = SLIDER_SPECS[i]
                val = max(spec[2], min(spec[3], val))
                setattr(self.app.crt_settings, self._dragging_key, val)
                return

    def update(self):
        pass

    def render(self):
        overlay = self.app.screen.overlay
        font = self.app.text_renderer.font
        overlay.fill((0, 0, 0, 255))

        # Title
        title = font.render("CRT Settings (F10 = open, Esc = back)", True, GREEN)
        overlay.blit(title, (MARGIN_LEFT, MARGIN_TOP - 28))

        s = self.app.crt_settings
        for i, (key, label, mn, mx) in enumerate(SLIDER_SPECS):
            y = MARGIN_TOP + i * LINE_HEIGHT
            label_surf = font.render(label + ":", True, GREEN)
            overlay.blit(label_surf, (MARGIN_LEFT, y))
            track, thumb = self._slider_rects(i)
            pygame.draw.rect(overlay, (40, 80, 40), track)
            pygame.draw.rect(overlay, (20, 40, 20), track, 1)
            pygame.draw.rect(overlay, GREEN, thumb)
            pygame.draw.rect(overlay, (0, 180, 0), thumb, 1)
            val = getattr(s, key)
            if key in ("blur_offset", "grain_intensity", "bloom_offset"):
                val_str = f"{val:.4f}"
            elif key == "bloom_depth":
                val_str = f"{val:.2f}"
            else:
                val_str = f"{val:.2f}"
            val_surf = font.render(val_str, True, GREEN)
            overlay.blit(val_surf, (MARGIN_LEFT + LABEL_W + TRACK_W + 10, y - 2))

        # Buttons
        save_rect = pygame.Rect(MARGIN_LEFT, BUTTON_LINE, BUTTON_W, BUTTON_H)
        back_rect = pygame.Rect(MARGIN_LEFT + BUTTON_W + 20, BUTTON_LINE, BUTTON_W, BUTTON_H)
        now = pygame.time.get_ticks() / 1000.0
        save_color = (0, 200, 0) if now < self._save_flash_until else GREEN
        pygame.draw.rect(overlay, save_color, save_rect)
        pygame.draw.rect(overlay, (0, 255, 0), save_rect, 1)
        save_txt = font.render("Save", True, BLACK)
        overlay.blit(save_txt, (save_rect.x + (save_rect.w - save_txt.get_width()) // 2, save_rect.y + 4))
        pygame.draw.rect(overlay, (60, 60, 60), back_rect)
        pygame.draw.rect(overlay, GREEN, back_rect, 1)
        back_txt = font.render("Back", True, GREEN)
        overlay.blit(back_txt, (back_rect.x + (back_rect.w - back_txt.get_width()) // 2, back_rect.y + 4))

        hint = font.render("Sliders: click or drag. Save writes to crt_settings.json", True, (0, 180, 0))
        overlay.blit(hint, (MARGIN_LEFT, BUTTON_LINE + LINE_HEIGHT + 10))
