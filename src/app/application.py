import os
import pygame
from pygame import mixer
from src.scenes.scene_factory import SceneFactory
from src.shell.shell_runner import ShellRunner
from src.app.crt_settings import CRTSettings
import random
import time  # Import time for calculating elapsed time

class Application:
    def __init__(self, screen, text_renderer, input_handler, config):
        self.screen = screen
        self.text_renderer = text_renderer
        self.input_handler = input_handler
        self.config = config
        self.crt_settings = CRTSettings.load()
        self.shell_runner = ShellRunner(
            config.shell_command, config.shell_cwd, config.shell_use_pty
        )
        self.scenes = SceneFactory.create_scenes(self, config)
        self.active_scene = None
        self.previous_scene_name = "shell_scene"
        self.is_rendering = True
        self.state_transition = False
        self.standard_sounds, self.enter_sounds, self.return_sound, self.poweron_sound, self.hum_sound, self.boot_scroll_sound, self.boot_type_sound, self.boot_wipe_sound = self._load_sounds()
        self.text_renderer.on_output_added = self.play_return_sound
        self._last_return_sound_time = 0.0
        self._return_sound_debounce_sec = 0.15
        self.start_time = time.time()  # Track the start time

    def run(self):
        self._initialize()
        self._start_background_hum()
        self._play_poweron_sound()
        clock = pygame.time.Clock()
        done = False

        while not done:
            current_time = time.time() - self.start_time  # Calculate elapsed time
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F10:
                        self.open_settings()
                        continue
                    self._play_key_sound(event.key)
                done |= self.active_scene.handle_event(event)

            self.active_scene.update()
            self.screen.clear()
            self.active_scene.render()
            self.screen.display(current_time, self.crt_settings)
            clock.tick(60)

        self._stop_background_hum()
        pygame.quit()

    def _initialize(self):
        self.screen.initialize()
        self.set_scene(self.config.initial_scene)

    def set_scene(self, scene_name):
        self.active_scene = self.scenes[scene_name]
        self.text_renderer.reset_previous_lines()
        self.active_scene.enter()

    def open_settings(self):
        """Switch to settings scene; remember current scene to return to."""
        for name, scene in self.scenes.items():
            if scene is self.active_scene:
                self.previous_scene_name = name
                break
        self.set_scene("settings_scene")

    def _load_sounds(self):
        mixer.init()
        mixer.set_num_channels(16)

        def _load(path):
            try:
                return mixer.Sound(path) if path and os.path.exists(path) else None
            except Exception:
                return None

        def _load_list(paths):
            out = []
            for p in paths:
                s = _load(p)
                if s is not None:
                    out.append(s)
            return out

        standard_sounds = _load_list(self.config.standard_sound_files)
        enter_sounds = _load_list(self.config.enter_sound_files)
        if not standard_sounds:
            standard_sounds = enter_sounds
        if not enter_sounds:
            enter_sounds = standard_sounds
        return_sound = _load(getattr(self.config, "return_sound_file", None))
        poweron_sound = _load(getattr(self.config, "poweron_sound_file", None))
        hum_sound = _load(getattr(self.config, "hum_sound_file", None))
        boot_scroll_sound = _load(getattr(self.config, "boot_scroll_sound_file", None))
        boot_type_sound = _load(getattr(self.config, "boot_type_sound_file", None))
        boot_wipe_sound = _load(getattr(self.config, "boot_wipe_sound_file", None))
        return standard_sounds, enter_sounds, return_sound, poweron_sound, hum_sound, boot_scroll_sound, boot_type_sound, boot_wipe_sound

    def _play_key_sound(self, key):
        sound_list = self.enter_sounds if key == pygame.K_RETURN else self.standard_sounds
        if not sound_list:
            return
        sound = random.choice(sound_list)
        sound.play()

    def play_return_sound(self):
        if self.return_sound is None:
            return
        now = time.time()
        if now - self._last_return_sound_time < self._return_sound_debounce_sec:
            return
        self._last_return_sound_time = now
        self.return_sound.play()

    def _play_poweron_sound(self):
        if self.poweron_sound is not None:
            self.poweron_sound.play()

    def _start_background_hum(self):
        if self.hum_sound is not None:
            self.hum_sound.play(loops=-1)

    def _stop_background_hum(self):
        if self.hum_sound is not None:
            self.hum_sound.stop()
