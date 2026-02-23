import time

class TextRenderer:
    """
    A class to render text on a screen with a typewriter-like effect. It manages
    text wrapping, scrolling, and rendering with a cursor for user text input.
    """

    def __init__(self, screen, font, color, char_delay=0.0001, margin=(50, 50), 
                 line_height=30, max_width=700, max_height=500):
        """
        Initializes the TextRenderer.

        Args:
            screen: A surface on which the text will be rendered.
            font: Font to be used for rendering text.
            color: Color of the text.
            char_delay: Delay between rendering characters for the typewriter effect.
            margin: Tuple specifying margin (left, top) in pixels.
            line_height: Height of each line in pixels.
            max_width: Maximum width of the text area in pixels.
            max_height: Maximum height of the text area in pixels.
        """
        self.screen = screen
        self.font = font
        self.color = color
        self.char_delay = char_delay
        self.margin = margin
        self.line_height = line_height
        self.max_width = max_width
        self.max_height = max_height
        self.text_buffer = []
        self.full_text_lines = []
        self.previous_text_lines = []
        self.current_line_index = 0
        self.current_char_index = 0
        self.last_update_time = time.time()
        self.is_rendering_complete = False
        self.finish_rendering_requested = False
        self.is_active_rendering = False
        self.scroll_position = 0
        self.user_input_text = ""
        self.cursor_enabled = True
        self._last_logical_line_wrapped_count = 0
        self.on_output_added = None  # optional callback when output is appended (e.g. play return sound)
        self.on_char_typed = None   # optional callback when typewriter adds char(s), e.g. play keypress sound
        self.centered_line_indices = set()  # line indices to center horizontally (e.g. {0} for welcome line)

    def set_text(self, text_lines):
        """
        Set the text to be rendered and resets the rendering state.

        Args:
            text_lines: List of strings to be rendered.
        """
        self.full_text_lines = self._wrap_text(text_lines)
        self._last_logical_line_wrapped_count = (
            len(self._wrap_text([text_lines[-1]])) if text_lines else 0
        )
        self._reset_state()
        if text_lines and self.on_output_added:
            self.on_output_added()

    def update(self):
        """
        Updates the internal state based on the time since the last update.
        """
        if self._is_time_to_update():
            self._update_text_buffer()

    def render(self):
        """
        Renders the text buffer, user input, and scroll indicators on the screen.
        """
        visible_lines = self._get_visible_lines()
        max_visible_lines = self._get_max_visible_lines()
        y = self.margin[1]
        for i, line in enumerate(visible_lines):
            line_index = self.scroll_position + i
            self._render_line(line, y, line_index=line_index)
            y += self.line_height
        self._render_user_input(y)
        self._render_scroll_indicators()

    def finish_rendering(self):
        """
        Completes the rendering immediately by rendering all remaining text at once.
        """
        self.finish_rendering_requested = True
        self._update_text_buffer()

    def append_text(self, text):
        """
        Appends new text to the existing text and starts rendering (typewriter).
        on_output_added is triggered when each line *finishes* animating, not here.
        Does not call update() here to avoid recursion when on_output_added appends more text.
        """
        self.previous_text_lines = self.full_text_lines.copy()
        self.full_text_lines.extend(self._wrap_text([text]))
        self.is_active_rendering = True

    def append_lines_instant(self, lines):
        """
        Appends lines to the buffer and updates the display immediately
        (no typewriter effect). Used for live shell output.

        Args:
            lines: List of strings to append.
        """
        if not lines:
            return
        for line in lines:
            wrapped = self._wrap_text([line])
            self.full_text_lines.extend(wrapped)
            self._last_logical_line_wrapped_count = len(wrapped)
        self._render_full_text()
        if self.on_output_added:
            self.on_output_added()

    def replace_last_line(self, text):
        """
        Replaces the last logical line with the given text (e.g. for \\r progress updates).
        No-op if there are no lines.
        """
        if not self.full_text_lines or self._last_logical_line_wrapped_count <= 0:
            return
        n = self._last_logical_line_wrapped_count
        wrapped = self._wrap_text([text])
        self.full_text_lines = self.full_text_lines[:-n] + wrapped
        self._last_logical_line_wrapped_count = len(wrapped)
        self._render_full_text()
        if self.on_output_added:
            self.on_output_added()

    def is_rendering(self):
        """
        Checks if the text is still being rendered.

        Returns:
            bool: True if rendering is not complete, False otherwise.
        """
        return not self.is_rendering_complete

    def get_text_buffer(self):
        """
        Gets the current text buffer.

        Returns:
            list: Current list of rendered lines.
        """
        return self.text_buffer

    def reset_previous_lines(self):
        """
        Resets the previously rendered lines.
        """
        self.previous_text_lines = []

    def scroll_up(self):
        """
        Scrolls the visible text up by one line.
        """
        if self.scroll_position > 0:
            self.scroll_position -= 1

    def scroll_down(self):
        """
        Scrolls the visible text down by one line.
        """
        max_scroll = max(0, len(self.text_buffer) - self._get_max_visible_lines())
        if self.scroll_position < max_scroll:
            self.scroll_position += 1

    def scroll_page_up(self):
        """
        Scrolls the visible text up by one page (max visible lines).
        """
        page_size = self._get_max_visible_lines()
        self.scroll_position = max(0, self.scroll_position - page_size)

    def scroll_page_down(self):
        """
        Scrolls the visible text down by one page (max visible lines).
        """
        max_scroll = max(0, len(self.text_buffer) - self._get_max_visible_lines())
        page_size = self._get_max_visible_lines()
        self.scroll_position = min(max_scroll, self.scroll_position + page_size)

    def set_user_input_text(self, text):
        """
        Sets the text for user input.

        Args:
            text: Text to be shown as user input.
        """
        self.user_input_text = text

    def scroll_to_bottom(self):
        """
        Scrolls the visible text to the bottom.
        """
        self.scroll_position = max(0, len(self.full_text_lines) - self._get_max_visible_lines())
        self._render_full_text()

    def _wrap_text(self, text_lines):
        """
        Wraps text lines to fit within the maximum width.

        Args:
            text_lines: List of strings to be wrapped.

        Returns:
            list: Wrapped text lines.
        """
        wrapped_lines = []
        for line in text_lines:
            if line.strip() == "":
                wrapped_lines.append("")
            else:
                for subline in line.split('\n'):
                    while subline:
                        max_width = self.max_width - self.margin[0]
                        split_pos = len(subline)
                        while self.font.size(subline[:split_pos])[0] > max_width and split_pos > 0:
                            split_pos -= 1
                        if split_pos < len(subline):
                            split_pos = subline[:split_pos].rfind(' ')
                            if split_pos == -1:
                                split_pos = len(subline)
                        wrapped_lines.append(subline[:split_pos])
                        subline = subline[split_pos:].strip()
        return wrapped_lines

    def _wrap_user_input(self):
        """
        Wraps user input text to fit within the maximum width.

        Returns:
            list: Wrapped user input text lines.
        """
        return self._wrap_text(self.user_input_text.splitlines())

    def _reset_state(self):
        """
        Resets the state for rendering.
        """
        self.text_buffer = self.previous_text_lines.copy()
        self.current_line_index = len(self.previous_text_lines)
        self.current_char_index = 0
        self.last_update_time = time.time()
        self.is_rendering_complete = False
        self.finish_rendering_requested = False
        self.is_active_rendering = True
        self.scroll_position = 0
        self.user_input_text = ""

    def _is_time_to_update(self):
        """
        Determines if it's time to update the rendering based on the delay.
        Does not update last_update_time; _update_text_buffer() does that so
        multiple chars can be added per frame when behind schedule.
        """
        if self.finish_rendering_requested:
            return True
        return (time.time() - self.last_update_time) >= self.char_delay

    def _update_text_buffer(self):
        """
        Updates the text buffer by adding characters. Adds multiple characters per
        frame when behind schedule (so pacing matches char_delay regardless of frame rate).
        """
        if self.current_line_index < len(self.full_text_lines):
            self.is_active_rendering = True
            current_line = self.full_text_lines[self.current_line_index]
            if self.current_char_index < len(current_line):
                if self.finish_rendering_requested:
                    self.current_char_index = len(current_line)
                else:
                    current_time = time.time()
                    elapsed = current_time - self.last_update_time
                    remaining = len(current_line) - self.current_char_index
                    chars_to_add = min(remaining, max(1, int(elapsed / self.char_delay)))
                    self.current_char_index += chars_to_add
                    self.last_update_time += chars_to_add * self.char_delay
                    if chars_to_add > 0 and self.on_char_typed:
                        self.on_char_typed()
            else:
                if self.on_output_added:
                    self.on_output_added()
                self._move_to_next_line()
                if self.finish_rendering_requested:
                    self._update_text_buffer()
        else:
            self.is_rendering_complete = True
            self.is_active_rendering = False
        self._recreate_text_buffer()

    def _render_full_text(self):
        """
        Renders the full text by copying all lines to the text buffer.
        """
        self.text_buffer = self.full_text_lines.copy()
        self.is_rendering_complete = True
        self.finish_rendering_requested = True
        self.is_active_rendering = False

    def _recreate_text_buffer(self):
        """
        Recreates the text buffer with the current state of rendering.
        """
        self.text_buffer = []
        for i in range(self.current_line_index):
            self.text_buffer.append(self.full_text_lines[i])
        if self.current_line_index < len(self.full_text_lines):
            current_line = self.full_text_lines[self.current_line_index]
            self.text_buffer.append(current_line[:self.current_char_index])

    def _move_to_next_line(self):
        """
        Moves to the next line in the text.
        """
        self.current_char_index = 0
        self.current_line_index += 1

    def _get_max_visible_lines(self):
        """
        Calculates the maximum number of visible lines based on the height.

        Returns:
            int: Maximum number of visible lines.
        """
        available_height = self.max_height - self.margin[1] - self.line_height
        return available_height // self.line_height

    def _get_visible_lines(self):
        """
        Gets the visible lines based on the current scroll position.

        Returns:
            list: List of visible lines.
        """
        max_visible_lines = self._get_max_visible_lines()
        return self.text_buffer[self.scroll_position:self.scroll_position + max_visible_lines]

    def enable_cursor(self):
        """
        Enables the cursor for user input.
        """
        self.cursor_enabled = True

    def disable_cursor(self):
        """
        Disables the cursor for user input.
        """
        self.cursor_enabled = False

    def _render_cursor(self, x, y):
        """
        Renders the cursor at the specified position if enabled.

        Args:
            x: X coordinate for the cursor.
            y: Y coordinate for the cursor.
        """
        if self.cursor_enabled and int(time.time() * 2) % 2 == 0:
            cursor_surface = self.font.render("█", True, self.color)
            self.screen.blit(cursor_surface, (x, y))

    def _render_user_input(self, y):
        """
        Renders the user input text and the cursor.

        Args:
            y: Y coordinate for the user input text.
        """
        user_input_lines = self._wrap_user_input()
        if user_input_lines:
            for line in user_input_lines:
                user_input_surface = self.font.render(line, True, self.color)
                self.screen.blit(user_input_surface, (self.margin[0], y))
                y += self.line_height

            cursor_y = y - self.line_height
            cursor_x = self.margin[0] + self.font.size(user_input_lines[-1])[0]
        else:
            cursor_y = y
            cursor_x = self.margin[0]

        self._render_cursor(cursor_x, cursor_y)

    def _render_line(self, line, y, line_index=None):
        """
        Renders a single line of text.

        Args:
            line: String to be rendered.
            y: Y coordinate for the line.
            line_index: Optional global line index (for centered_line_indices).
        """
        rendered_text = self.font.render(line, True, self.color)
        if getattr(self, "centered_line_indices", None) and line_index is not None and line_index in self.centered_line_indices:
            w = getattr(self.screen, "get_width", None)
            surface_w = w() if callable(w) else getattr(self.screen, "width", self.max_width)
            x = (surface_w - rendered_text.get_width()) // 2
        else:
            x = self.margin[0]
        self.screen.blit(rendered_text, (x, y))

    def _render_scroll_indicators(self):
        """
        Renders scroll indicators if scrolling is possible.
        """
        max_visible_lines = self._get_max_visible_lines()
        if self.scroll_position > 0:
            up_indicator = self.font.render("^", True, self.color)
            self.screen.blit(up_indicator, (self.max_width - 20, self.margin[1] - 20))
        if len(self.text_buffer) > self.scroll_position + max_visible_lines:
            down_indicator = self.font.render("v", True, self.color)
            self.screen.blit(down_indicator, (self.max_width - 20, self.max_height - self.margin[1]))
