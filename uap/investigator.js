/* UAP Detector v0.9.3 — browser-only multi-view player and paused-frame comparison.
   All three views are processed from the SAME NoIR video. No view isolates infrared.
   Neither video capture nor stored source MP4s are modified. */
'use strict';

document.addEventListener('DOMContentLoaded', () => {
  const root = document.querySelector('[data-investigator]');
  if (!root) return;
  const $ = id => document.getElementById(id);
  const video = $('investigator-video');
  const stage = $('investigator-stage');
  const media = $('investigator-media');
  const seek = $('investigator-seek');
  const play = $('investigator-play');
  const back = $('investigator-back');
  const next = $('investigator-next');
  const speed = $('investigator-speed');
  const time = $('investigator-time');
  const zoomInput = $('investigator-zoom');
  const zoomLabel = $('investigator-zoom-label');
  const brightnessInput = $('investigator-brightness');
  const brightnessLabel = $('investigator-brightness-label');
  const contrastInput = $('investigator-contrast');
  const contrastLabel = $('investigator-contrast-label');
  const reset = $('investigator-reset');
  const fullscreen = $('investigator-fullscreen');
  const snapshot = $('investigator-snapshot');
  const status = $('investigator-status');
  const playbackView = $('investigator-view');
  const compareToggle = $('investigator-compare-toggle');
  const compare = $('investigator-compare');
  const compareUI = $('investigator-compare-ui');
  const compareLeft = $('investigator-compare-left');
  const compareRight = $('investigator-compare-right');
  const compareRightClip = $('investigator-compare-right-clip');
  const compareSlider = $('investigator-compare-slider');
  const compareDivider = $('investigator-compare-divider');
  const viewLeft = $('investigator-view-left');
  const viewRight = $('investigator-view-right');
  const labelLeft = $('investigator-label-left');
  const labelRight = $('investigator-label-right');
  const compareInfo = $('investigator-compare-info');

  // These are browser processing presets, NOT independently recorded spectral channels.
  const views = {
    original: {label:'Original', filter:'none'},
    detection: {label:'Detection (grayscale)', filter:'grayscale(1) contrast(1.25)'},
    enhanced: {label:'Low-light enhanced', filter:'grayscale(1) brightness(1.45) contrast(1.4)'}
  };
  const parsedFps = Number.parseFloat(root.dataset.fps);
  const fps = Number.isFinite(parsedFps) && parsedFps >= 1 && parsedFps <= 240 ? parsedFps : 15;
  let zoom = 1;
  let panX = 0;
  let panY = 0;
  let drag = null;
  let draggingSlider = false;
  let compareRequested = false;

  video.muted = true; // The Camera Module 3 does not record audio.
  video.playsInline = true;

  function say(message) { status.textContent = message; }
  function hasFrame() { return video.readyState >= 2 && video.videoWidth > 0 && video.videoHeight > 0; }
  function canCompare() { return video.paused && hasFrame(); }
  function showingCompare() { return compareRequested && canCompare(); }
  function duration() { return Number.isFinite(video.duration) && video.duration > 0 ? video.duration : 0; }
  function formatTime(seconds) {
    if (!Number.isFinite(seconds)) return '--:--.---';
    const total = Math.round(Math.max(0, seconds) * 1000);
    const minutes = Math.floor(total / 60000);
    const secs = Math.floor((total % 60000) / 1000);
    const millis = total % 1000;
    return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(millis).padStart(3, '0')}`;
  }
  function updateTime() {
    const full = duration();
    time.textContent = `${formatTime(video.currentTime)} / ${full ? formatTime(full) : '--:--.---'}`;
    if (!draggingSlider && full) seek.value = String(Math.round(1000 * video.currentTime / full));
  }
  function updatePlay() { play.textContent = video.paused ? '▶ Play' : '❚❚ Pause'; }
  function clampPan() {
    const maxX = Math.max(0, (zoom - 1) * stage.clientWidth / 2);
    const maxY = Math.max(0, (zoom - 1) * stage.clientHeight / 2);
    panX = Math.max(-maxX, Math.min(maxX, panX));
    panY = Math.max(-maxY, Math.min(maxY, panY));
  }
  function globalFilter() {
    return `brightness(${brightnessInput.value}%) contrast(${contrastInput.value}%)`;
  }
  function updateImage() {
    zoom = Number(zoomInput.value);
    clampPan();
    media.style.transform = `translate(${panX}px, ${panY}px) scale(${zoom})`;
    media.style.filter = globalFilter();
    zoomLabel.textContent = `${zoom.toFixed(2).replace(/\.00$/, '')}×`;
    brightnessLabel.textContent = `${brightnessInput.value}%`;
    contrastLabel.textContent = `${contrastInput.value}%`;
    stage.style.cursor = showingCompare() ? 'ew-resize' : (zoom > 1 ? 'grab' : 'default');
    if (showingCompare()) updateSplit();
  }
  function updatePlaybackView() {
    video.style.filter = views[playbackView.value].filter;
  }
  function updateSplit() {
    const pct = Number(compareSlider.value);
    // Media is zoomed/panned, but divider belongs to untransformed stage.
    // Convert its screen-space x into the local zoomed image coordinates.
    const stageWidth = Math.max(1, stage.clientWidth);
    const local = Math.max(0, Math.min(100, 50 + ((pct - 50) - 100 * panX / stageWidth) / Math.max(1,zoom)));
    compareRightClip.style.clipPath = `inset(0 0 0 ${local}%)`;
    compareDivider.style.left = `${pct}%`;
    compareInfo.textContent = showingCompare()
      ? `${formatTime(video.currentTime)} · Left: ${views[viewLeft.value].label} · Right: ${views[viewRight.value].label}`
      : (video.paused ? 'Choose Compare frame to inspect the current image.' : 'Single-view playback; comparison returns when paused.');
  }
  function updateCompareLabels() {
    labelLeft.textContent = views[viewLeft.value].label;
    labelRight.textContent = views[viewRight.value].label;
    compareLeft.style.filter = views[viewLeft.value].filter;
    compareRight.style.filter = views[viewRight.value].filter;
    updateSplit();
  }
  function capturePausedFrame() {
    if (!showingCompare() || !hasFrame() || video.seeking) return;
    try {
      for (const canvas of [compareLeft, compareRight]) {
        if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
        }
        const ctx = canvas.getContext('2d', {alpha:false});
        if (!ctx) throw new Error('Canvas unavailable');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      }
      updateCompareLabels();
    } catch (_) {
      say('Frame comparison could not render in this browser.');
    }
  }
  function updateCompareVisibility() {
    const visible = showingCompare();
    compare.hidden = !visible;
    compareUI.hidden = !visible;
    video.style.opacity = visible ? '0' : '1';
    stage.classList.toggle('comparing', visible);
    compareToggle.disabled = !canCompare();
    compareToggle.setAttribute('aria-pressed', String(compareRequested));
    compareToggle.textContent = compareRequested ? 'Close comparison' : 'Compare frame';
    updateImage();
    updateSplit();
    if (visible) capturePausedFrame();
  }
  function seekTo(seconds) {
    const full = duration();
    if (!full) { say('Waiting for video metadata.'); return; }
    video.currentTime = Math.max(0, Math.min(Math.max(0, full - 0.001), seconds));
    updateTime();
  }
  function stepFrame(direction) {
    video.pause();
    seekTo(video.currentTime + direction / fps);
    say('Stepped by one nominal frame; browser seeking may not be exact.');
  }

  play.addEventListener('click', async () => {
    if (!video.paused) { video.pause(); return; }
    if (duration() && video.currentTime >= duration() - 0.03) video.currentTime = 0;
    // The play event hides comparison; the pause event restores it automatically.
    try { await video.play(); say('Playing selected view.'); }
    catch (_) { say('Playback failed. Try downloading the original MP4.'); }
  });
  back.addEventListener('click', () => stepFrame(-1));
  next.addEventListener('click', () => stepFrame(1));
  speed.addEventListener('change', () => {
    video.playbackRate = Number(speed.value);
    say(`Playback speed: ${speed.value}×.`);
  });
  seek.addEventListener('input', () => {
    draggingSlider = true;
    if (duration()) time.textContent = `${formatTime(duration() * Number(seek.value) / 1000)} / ${formatTime(duration())}`;
  });
  seek.addEventListener('change', () => {
    draggingSlider = false;
    seekTo(duration() * Number(seek.value) / 1000);
  });
  playbackView.addEventListener('change', () => {
    updatePlaybackView();
    say(`Playback view: ${views[playbackView.value].label}.`);
  });
  compareToggle.addEventListener('click', () => {
    if (!canCompare()) return;
    compareRequested = !compareRequested;
    updateCompareVisibility();
    say(compareRequested ? 'Comparing the current paused frame.' : 'Back to single view.');
  });
  viewLeft.addEventListener('change', () => { updateCompareLabels(); });
  viewRight.addEventListener('change', () => { updateCompareLabels(); });
  compareSlider.addEventListener('input', updateSplit);
  compareSlider.addEventListener('keydown', event => event.stopPropagation());
  compareSlider.addEventListener('pointerdown', event => event.stopPropagation());
  for (const input of [zoomInput, brightnessInput, contrastInput]) {
    input.addEventListener('input', updateImage);
  }
  reset.addEventListener('click', () => {
    zoomInput.value = '1'; brightnessInput.value = '100'; contrastInput.value = '100';
    panX = 0; panY = 0; updateImage();
    say('Image adjustments reset.');
  });
  stage.addEventListener('pointerdown', event => {
    if (event.target.closest('.investigator-fullscreen-controls')) return;
    if (showingCompare() || zoom <= 1 || (event.pointerType === 'mouse' && event.button !== 0)) return;
    drag = {id:event.pointerId, x:event.clientX, y:event.clientY, px:panX, py:panY};
    stage.setPointerCapture(event.pointerId);
    stage.classList.add('dragging');
  });
  stage.addEventListener('pointermove', event => {
    if (!drag || drag.id !== event.pointerId) return;
    panX = drag.px + event.clientX - drag.x;
    panY = drag.py + event.clientY - drag.y;
    updateImage();
  });
  function endDrag(event) {
    if (!drag || drag.id !== event.pointerId) return;
    drag = null; stage.classList.remove('dragging');
  }
  stage.addEventListener('pointerup', endDrag);
  stage.addEventListener('pointercancel', endDrag);
  stage.addEventListener('lostpointercapture', () => { drag = null; stage.classList.remove('dragging'); });
  stage.addEventListener('keydown', event => {
    if (event.target !== stage) return;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault(); stepFrame(event.key === 'ArrowLeft' ? -1 : 1);
    } else if (event.key === ' ' || event.key === 'k') {
      event.preventDefault(); play.click();
    }
  });
  // Fullscreen the actual media stage, never the entire investigation grid.
  // The old grid stretched its controls across the viewport and hid the footage.
  const exitFullscreen = $('investigator-exit-fullscreen');
  const fullscreenPlay = $('investigator-fullscreen-play');
  fullscreen.addEventListener('click', async () => {
    try {
      if (document.fullscreenElement === stage) await document.exitFullscreen();
      else if (stage.requestFullscreen) await stage.requestFullscreen();
      else if (video.webkitEnterFullscreen && playbackView.value === 'original') video.webkitEnterFullscreen();
      else say('Fullscreen is not supported by this browser for the selected view.');
    } catch (_) { say('Fullscreen could not be opened on this device.'); }
  });
  if(exitFullscreen)exitFullscreen.addEventListener('click', async () => {
    if(document.fullscreenElement === stage) await document.exitFullscreen();
  });
  if(fullscreenPlay)fullscreenPlay.addEventListener('click',()=>play.click());
  document.addEventListener('fullscreenchange', () => { clampPan(); updateImage(); });
  window.addEventListener('resize', () => { clampPan(); updateImage(); });

  function downloadCanvas(canvas, name) {
    canvas.toBlob(blob => {
      snapshot.disabled = false;
      if (!blob) { say('Could not export the PNG frame.'); return; }
      // A Save PNG action always downloads; never invoke the platform share dialog.
      // The exported canvas already includes both comparison views and labels.
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url; link.download = name;
      document.body.appendChild(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 30000);
      say('PNG download started. The original video was not changed.');
    }, 'image/png');
  }
  function drawView(ctx, width, height, selected) {
    ctx.filter = `${views[selected].filter === 'none' ? '' : views[selected].filter + ' '}${globalFilter()}`;
    ctx.drawImage(video, 0, 0, width, height);
    ctx.filter = 'none';
  }
  snapshot.addEventListener('click', () => {
    if (!hasFrame()) { say('Wait for the video frame to load before saving a PNG.'); return; }
    video.pause();
    snapshot.disabled = true;
    try {
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d', {alpha:false});
      if (!ctx) throw new Error('Canvas not supported');
      if (showingCompare()) {
        const split = Math.round(canvas.width * Number(compareSlider.value) / 100);
        drawView(ctx, canvas.width, canvas.height, viewLeft.value);
        ctx.save();
        ctx.beginPath(); ctx.rect(split, 0, canvas.width-split, canvas.height); ctx.clip();
        drawView(ctx, canvas.width, canvas.height, viewRight.value);
        ctx.restore();
        ctx.fillStyle = '#d6f6ff'; ctx.fillRect(Math.max(0,split-2),0,Math.max(2,canvas.width/640),canvas.height);
        // Include view labels in exports so comparisons are understandable later.
        const fontSize = Math.max(16, Math.round(canvas.width / 57));
        ctx.font = `bold ${fontSize}px sans-serif`;
        ctx.textBaseline = 'top';
        ctx.lineWidth = Math.max(3, Math.round(fontSize/5));
        ctx.strokeStyle = 'black'; ctx.fillStyle = '#fff';
        ctx.strokeText(views[viewLeft.value].label, 14, 14);
        ctx.fillText(views[viewLeft.value].label, 14, 14);
        const rightText = views[viewRight.value].label;
        const rightX = Math.max(14, canvas.width - ctx.measureText(rightText).width - 14);
        ctx.strokeText(rightText, rightX, 14); ctx.fillText(rightText, rightX, 14);
      } else {
        drawView(ctx, canvas.width, canvas.height, playbackView.value);
      }
      const eid = String(root.dataset.eventId).replace(/[^0-9]/g, '');
      const timestamp = Number(video.currentTime).toFixed(3).replace('.', '-');
      downloadCanvas(canvas, `event-${eid}-${showingCompare()?'compare':playbackView.value}-${timestamp}s.png`);
    } catch (_) { snapshot.disabled = false; say('This browser could not export the current frame.'); }
  });

  video.addEventListener('loadedmetadata', () => { updateTime(); say('Video ready for investigation.'); });
  video.addEventListener('loadeddata', updateCompareVisibility);
  video.addEventListener('timeupdate', updateTime);
  video.addEventListener('seeked', () => { updateTime(); if (showingCompare()) capturePausedFrame(); updateSplit(); });
  video.addEventListener('play', () => { updatePlay(); updateCompareVisibility(); });
  video.addEventListener('pause', () => { updatePlay(); updateCompareVisibility(); });
  video.addEventListener('ended', () => { updatePlay(); updateCompareVisibility(); say('End of recording.'); });
  video.addEventListener('error', () => { say('Video could not be loaded. Try downloading the original MP4.'); });
  updatePlay(); updatePlaybackView(); updateCompareLabels(); updateCompareVisibility(); updateTime();
});
