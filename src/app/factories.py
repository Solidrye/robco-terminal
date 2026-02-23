from src.rendering.terminal_screen import TerminalScreen
from src.assets.font_loader import FileFontLoader
from src.rendering.text_renderer import TextRenderer
from src.handlers.input_handler import TerminalInputHandler
from src.app.constants import BLACK, GREEN

class ScreenFactory:
    @staticmethod
    def create_screen(config):
        return TerminalScreen(config.screen_width, config.screen_height, BLACK)

class FontLoaderFactory:
    @staticmethod
    def create_font_loader(config):
        return FileFontLoader(config.font_path, config.font_size)

class TextRendererFactory:
    @staticmethod
    def create_text_renderer(screen, font):
        margin = (50, 50)
        max_width = screen.width - 2 * margin[0]
        max_height = screen.height - 2 * margin[1]
        return TextRenderer(screen, font, GREEN, margin=margin, max_width=max_width, max_height=max_height)

class InputHandlerFactory:
    @staticmethod
    def create_input_handler():
        return TerminalInputHandler()
