"""
CRT effect settings: load/save to JSON and provide defaults.
Tweakable from the settings menu with real-time feedback.
"""
import json
import os


def _settings_path():
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "crt_settings.json")


DEFAULTS = {
    "luminance_intensity": 2.6,
    "bloom_threshold": 0.1,
    "bloom_extract_threshold": 0.15,
    "bloom_strength": 0.8,
    "bloom_offset": 0.0015,
    "bloom_depth": 1.0,
    "blur_strength": 0.2,
    "blur_offset": 0.003,
    "black_level": 0.05,
    "scanline_factor": 0.3,
    "grain_intensity": 0.02,
    "curve_intensity": 0.3,
}


class CRTSettings:
    def __init__(self):
        for k, v in DEFAULTS.items():
            setattr(self, k, v)

    @classmethod
    def load(cls):
        path = _settings_path()
        if not os.path.isfile(path):
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            inst = cls()
            for k in DEFAULTS:
                if k in data and isinstance(data[k], (int, float)):
                    setattr(inst, k, float(data[k]))
            return inst
        except Exception:
            return cls()

    def save(self):
        path = _settings_path()
        data = {k: getattr(self, k) for k in DEFAULTS}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def to_dict(self):
        return {k: getattr(self, k) for k in DEFAULTS}
