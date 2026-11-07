"""Pure, monotonic event-storm circuit breaker for unattended detectors.

Counts actual recording duration, including sequential rollover clips, in a
rolling window. Never deletes recordings; a trip saves the active MP4 and
suppresses further motion events for a bounded cooldown.
"""
from collections import deque


class StormGuard:
    def __init__(self, enabled=True, trigger_seconds=600, window_seconds=900,
                 cooldown_seconds=900):
        self.enabled = enabled
        self.trigger_seconds = float(trigger_seconds)
        self.window_seconds = float(window_seconds)
        self.cooldown_seconds = float(cooldown_seconds)
        self.intervals = deque()
        self.active_since = None
        self.cooldown_until = 0.0

    def set_config(self, settings):
        self.enabled = bool(settings.get('storm_enabled', True))
        self.trigger_seconds = float(settings.get('storm_trigger_minutes', 10)) * 60
        self.window_seconds = float(settings.get('storm_window_minutes', 15)) * 60
        self.cooldown_seconds = float(settings.get('storm_cooldown_minutes', 15)) * 60
        if not 0 < self.trigger_seconds <= self.window_seconds or self.cooldown_seconds <= 0:
            raise ValueError('Invalid event storm settings')
        if not self.enabled:
            self.intervals.clear()
            self.active_since = None
            self.cooldown_until = 0

    def start(self, now):
        if self.active_since is None:
            self.active_since = now

    def finish(self, now):
        if self.active_since is not None:
            self.intervals.append((self.active_since, now))
            self.active_since = None
        self._prune(now)

    def _prune(self, now):
        border = now - self.window_seconds
        while self.intervals and self.intervals[0][1] <= border:
            self.intervals.popleft()

    def time_recorded(self, now):
        self._prune(now)
        border = now - self.window_seconds
        elapsed = sum(max(0, end - max(start, border)) for start, end in self.intervals)
        if self.active_since is not None:
            elapsed += max(0, now - max(self.active_since, border))
        return elapsed

    def cooling(self, now):
        return self.enabled and now < self.cooldown_until

    def remaining(self, now):
        return max(0, self.cooldown_until - now) if self.enabled else 0

    def check(self, now):
        """True once when the configured rolling-time budget is exceeded."""
        if not self.enabled or self.cooling(now):
            return False
        if self.time_recorded(now) < self.trigger_seconds:
            return False
        self.cooldown_until = now + self.cooldown_seconds
        self.intervals.clear()
        self.active_since = None
        return True
