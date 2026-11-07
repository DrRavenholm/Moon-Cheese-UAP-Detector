"""Pure motion-to-clip state machine. No Pi hardware needed for unit tests.

The Picamera2 circular output delivers frames with a delay equal to its
pre-trigger buffer. To retain post-trigger footage, we close the output only
after POST + PRE seconds have elapsed since the last observed movement.
"""
from dataclasses import dataclass


@dataclass
class ClipPlanner:
    pre_seconds: float = 5.0
    post_seconds: float = 5.0
    max_seconds: float = 300.0
    trigger_frames: int = 3
    active: bool = False
    hits: int = 0
    last_motion: float | None = None
    segment_started: float | None = None

    def feed(self, now: float, is_motion: bool) -> str | None:
        """Return 'start', 'stop', 'rollover', or None.

        'rollover' means finish the current output and immediately open another;
        the motion session remains active. The next output is not a new trigger.
        """
        if is_motion:
            self.hits += 1
            if self.active:
                self.last_motion = now
        else:
            self.hits = 0

        if not self.active:
            if self.hits >= self.trigger_frames:
                self.active = True
                self.last_motion = now
                self.segment_started = now
                return 'start'
            return None

        # Priority: when quiet, do not open a needless new segment.
        if now - self.last_motion >= self.pre_seconds + self.post_seconds:
            self.active = False
            self.segment_started = None
            self.last_motion = None
            self.hits = 0
            return 'stop'
        if now - self.segment_started >= self.max_seconds:
            self.segment_started = now
            return 'rollover'
        return None


def detection_decision(profile, general_detected, sky_detected):
    """Select trigger sources without producing separate clips in Combined mode."""
    if profile == 'general':
        return bool(general_detected)
    if profile == 'sky_lights':
        return bool(sky_detected)
    if profile == 'combined':
        return bool(general_detected or sky_detected)
    raise ValueError('Unknown detection profile')
