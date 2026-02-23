from src.assets.file_loader import FileLoader


class Config:
    def __init__(self):
        file_loader = FileLoader()
        self.shell_command = "cmd.exe"
        self.shell_cwd = None  # None = use current working directory when app runs
        self.shell_use_pty = True  # Use PTY so SSH and other TTY programs work; fallback to pipes if unavailable
        self.font_path = file_loader.get_path("assets/fonts/Perfect DOS VGA 437 Win.ttf")
        self.screen_width = 800
        self.screen_height = 600
        self.font_size = 20
        self.initial_scene = "termlink_boot_scene"
        self.scene_after_boot = "shell_scene"
        self.password = "password123"
        self.standard_sound_files = [
            file_loader.get_path("assets/sounds/single_keypress_01.wav"),
            file_loader.get_path("assets/sounds/single_keypress_02.wav"),
            file_loader.get_path("assets/sounds/single_keypress_03.wav"),
            file_loader.get_path("assets/sounds/single_keypress_04.wav"),
            file_loader.get_path("assets/sounds/single_keypress_05.wav"),
            file_loader.get_path("assets/sounds/single_keypress_06.wav"),
        ]
        self.enter_sound_files = [
            file_loader.get_path("assets/sounds/enter_keypress_01.wav"),
            file_loader.get_path("assets/sounds/enter_keypress_02.wav"),
            file_loader.get_path("assets/sounds/enter_keypress_03.wav"),
        ]
        self.poweron_sound_file = file_loader.get_path("assets/sounds/poweron.wav")
        self.return_sound_file = file_loader.get_path("assets/sounds/return.wav")
        self.hum_sound_file = file_loader.get_path("assets/sounds/hum.wav")
        self.boot_scroll_sound_file = file_loader.get_path("assets/sounds/boot-scroll.wav")
        self.boot_type_sound_file = file_loader.get_path("assets/sounds/boot-type.wav")
        self.boot_wipe_sound_file = file_loader.get_path("assets/sounds/boot-wipe.wav")