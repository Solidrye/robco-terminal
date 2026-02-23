"""
Shell scene: shows live output from a real shell and one input line at the bottom.
Enter sends the line to the shell. No menus; no typewriter effect.
Right-click pastes from clipboard (Linux-style).
"""
import pygame
import pyperclip
from src.scenes.base_scene import BaseScene


class ShellScene(BaseScene):
    def __init__(self, app, shell_runner):
        super().__init__(app)
        self.runner = shell_runner
        self._last_line_count = 0
        self._last_displayed_line = None  # content of last line, for \\r updates

    def enter(self):
        self.runner.setwinsize(24, 80)
        initial_lines = self.runner.get_output_lines()
        if not initial_lines:
            initial_lines = ["Terminal ready."]
        self.app.text_renderer.set_text(initial_lines)
        self.app.text_renderer.finish_rendering()
        self.app.is_rendering = False
        self.app.state_transition = False
        self.app.input_handler.reset()
        lines = self.runner.get_output_lines()
        self._last_line_count = len(lines)
        self._last_displayed_line = lines[-1] if lines else None

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.USEREVENT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_PAGEUP:
                self.app.text_renderer.scroll_page_up()
                return False
            if event.key == pygame.K_PAGEDOWN:
                self.app.text_renderer.scroll_page_down()
                return False
            if event.key == pygame.K_UP:
                prev = self.runner.history_prev()
                if prev is not None:
                    self.app.input_handler.set_user_input(prev)
                return False
            if event.key == pygame.K_DOWN:
                next_ = self.runner.history_next()
                if next_ is not None:
                    self.app.input_handler.set_user_input(next_)
                return False
            if event.key == pygame.K_c and (event.mod & pygame.KMOD_CTRL):
                self.runner.send_interrupt()
                self.app.text_renderer.append_lines_instant(["^C"])
                return False
            if event.key == pygame.K_m and (event.mod & pygame.KMOD_ALT):
                self.app.set_scene("success_scene")
                return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            try:
                pasted = pyperclip.paste()
                if pasted and isinstance(pasted, str):
                    # One line: append to current input (newlines become spaces)
                    line = pasted.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
                    self.app.input_handler.set_user_input(
                        self.app.input_handler.get_user_input() + line
                    )
            except (pyperclip.PyperclipException, Exception):
                pass
            return False
        self.app.input_handler.handle_event(event)
        if self.app.input_handler.enter_pressed:
            self._handle_enter_pressed()
        return False

    def _handle_enter_pressed(self):
        user_input = self.app.input_handler.get_user_input()
        if user_input:
            self.runner.write(user_input)
        self.app.input_handler.reset()

    def update(self):
        self.app.input_handler.update()
        lines = self.runner.get_output_lines()
        if len(lines) > self._last_line_count:
            new_lines = lines[self._last_line_count:]
            self.app.text_renderer.append_lines_instant(new_lines)
            self.app.text_renderer.scroll_to_bottom()
            self._last_line_count = len(lines)
            self._last_displayed_line = lines[-1] if lines else None
        elif lines and len(lines) == self._last_line_count and lines[-1] != self._last_displayed_line:
            self.app.text_renderer.replace_last_line(lines[-1])
            self._last_displayed_line = lines[-1]

    def render(self):
        self.app.text_renderer.enable_cursor()
        self.app.text_renderer.set_user_input_text(self.app.input_handler.get_user_input())
        self.app.text_renderer.update()
        self.app.is_rendering = self.app.text_renderer.is_rendering()
        self.app.text_renderer.render()
