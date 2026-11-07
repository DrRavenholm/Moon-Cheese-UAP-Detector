"""Conservative local board/sensor capability discovery; no camera stream is opened.

High frame rates on Raspberry Pi 5 are experimental and must be tested in situ.
Sensor capability is not by itself evidence that the encoder can sustain a mode.
"""
from functools import lru_cache
from pathlib import Path

STANDARD_FPS = (5, 10, 15, 20, 24, 25, 30)
PI5_EXPERIMENTAL_FPS = (45, 60)


def describe_capabilities(board, sensor):
    name = (board or '').strip() or 'Unknown device'
    model = (sensor or '').strip().lower() or 'Camera not identified'
    is_pi5 = 'raspberry pi 5' in name.lower()
    is_imx708 = 'imx708' in model
    experimental = is_pi5 and is_imx708
    return {'pi_model': name, 'camera_model': model,
            'max_fps': 60 if experimental else 30,
            'fps_options': STANDARD_FPS + PI5_EXPERIMENTAL_FPS if experimental else STANDARD_FPS,
            'experimental': experimental}


@lru_cache(maxsize=1)
def capture_capabilities():
    try:
        board = Path('/proc/device-tree/model').read_bytes().rstrip(b'\x00').decode('utf-8','replace')
    except OSError:
        board = ''
    sensor = ''
    try:
        from picamera2 import Picamera2
        infos = Picamera2.global_camera_info()
        if infos:
            sensor = str(infos[0].get('Model', infos[0].get('model', '')))
    except (ImportError, OSError, RuntimeError, ValueError):
        pass
    return describe_capabilities(board, sensor)
