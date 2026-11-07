"""Experimental detection of small bright points moving between video frames.

This is candidate tracking, not object identification. It will miss objects that
are dim, diffuse, or move too rapidly to persist across the chosen frame count.
Only a downscaled greyscale image is processed to limit work on Raspberry Pi 4.
"""
import cv2
import numpy as np


class SkyLightTracker:
    def __init__(self, brightness=180, min_area=2, max_area=100,
                 confirm_frames=3, min_movement=2, max_jump=36):
        if not (0 < min_area <= max_area):
            raise ValueError('Invalid bright-point size range')
        self.brightness = int(brightness)
        self.min_area = int(min_area)
        self.max_area = int(max_area)
        self.confirm_frames = max(2, int(confirm_frames))
        self.min_movement = float(min_movement)
        self.max_jump = float(max_jump)
        self.background = None
        self.tracks = []
        self.frame_no = 0

    def clear(self):
        """Forget previous frames after a temporary camera preview."""
        self.background = None
        self.tracks = []
        self.frame_no = 0

    def feed(self, gray):
        """Return (moving_bright_point, candidate_pixel_score).

        Consecutive location matches are required, reducing false triggers from
        random noise and stationary stars. Large cloud areas are ignored.
        """
        if gray.ndim != 2:
            raise ValueError('Expected a greyscale camera frame')
        if self.background is None:
            self.background = gray.astype(np.float32)
            return False, 0
        self.frame_no += 1
        old_background = cv2.convertScaleAbs(self.background)
        positive_change = cv2.subtract(gray, old_background)
        bright_mask = cv2.inRange(gray, self.brightness, 255)
        change_mask = cv2.inRange(positive_change, 18, 255)
        points = cv2.bitwise_and(bright_mask, change_mask)
        count, _, stats, centroids = cv2.connectedComponentsWithStats(points, connectivity=8)
        blobs = []
        for idx in range(1, count):
            area = int(stats[idx, cv2.CC_STAT_AREA])
            if self.min_area <= area <= self.max_area:
                x, y = centroids[idx]
                blobs.append((float(x), float(y), area))
        # Keep the small object-tracking state bounded even on noisy frames.
        blobs = sorted(blobs, key=lambda x: x[2], reverse=True)[:40]
        prior = self.tracks
        updated = []
        used = set()
        for x, y, area in blobs:
            matched = None
            best_dist_sq = self.max_jump * self.max_jump
            for i, track in enumerate(prior):
                if i in used:
                    continue
                dx, dy = x - track['x'], y - track['y']
                d2 = dx * dx + dy * dy
                if self.min_movement * self.min_movement <= d2 <= best_dist_sq:
                    best_dist_sq = d2
                    matched = i
            if matched is not None:
                used.add(matched)
                count_hits = prior[matched]['hits'] + 1
            else:
                count_hits = 1
            updated.append({'x': x, 'y': y, 'hits': count_hits})
        self.tracks = updated
        cv2.accumulateWeighted(gray, self.background, 0.035)
        confirmed = any(t['hits'] >= self.confirm_frames for t in updated)
        score = sum(area for _, _, area in blobs)
        return confirmed, score
