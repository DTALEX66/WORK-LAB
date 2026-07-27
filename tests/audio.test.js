import assert from 'node:assert/strict';
import test from 'node:test';

import {
  AUDIO_LAYERS,
  getAudioLayer,
  isAudioMuted,
  playLayer,
  setAudioMuted,
  toggleAudioMuted,
  setMusicState,
  pauseMusic,
  resumeMusic,
  stopMusic,
} from '../src/audio.js';

test('audio layers separate game feedback categories', () => {
  assert.deepEqual(Object.keys(AUDIO_LAYERS), [
    'button',
    'success',
    'error',
    'anomaly',
    'warning',
    'failure',
    'revive',
    'restart',
  ]);
  assert.equal(getAudioLayer('button').kind, 'beep');
  assert.equal(getAudioLayer('error').kind, 'beep');
  assert.equal(getAudioLayer('anomaly').kind, 'sweep');
  assert.equal(getAudioLayer('failure').kind, 'sweep');
  assert.equal(getAudioLayer('revive').kind, 'sweep');
});

test('audio mute gate prevents layer playback and can be toggled', () => {
  setAudioMuted(false);
  assert.equal(isAudioMuted(), false);
  assert.equal(toggleAudioMuted(), true);
  assert.equal(isAudioMuted(), true);
  assert.equal(playLayer('button'), false);
  assert.equal(setAudioMuted(false), false);
  assert.equal(isAudioMuted(), false);
});

test('H5 music starts after gesture and uses the source BGM loops', async () => {
  const previousAudio = globalThis.Audio;
  const instances = [];
  globalThis.Audio = class {
    constructor(src) { this.src = src; this.loop = false; this.volume = 1; this.paused = true; instances.push(this); }
    play() { this.paused = false; return Promise.resolve(); }
    pause() { this.paused = true; }
  };
  try {
    setAudioMuted(false);
    assert.equal(setMusicState('calm'), true);
    assert.equal(instances.length, 1);
    assert.match(instances[0].src, /bgm-night-shift-loop\.wav$/);
    assert.equal(instances[0].loop, true);
    assert.equal(setMusicState('pressure'), true);
    assert.match(instances[0].src, /bgm-anomaly-pressure-loop\.wav$/);
    pauseMusic();
    assert.equal(resumeMusic(), true);
    stopMusic();
    assert.equal(instances[0].currentTime, 0);
  } finally {
    stopMusic();
    globalThis.Audio = previousAudio;
  }
});

test('unknown audio layer is ignored instead of throwing', () => {
  setAudioMuted(false);
  assert.equal(getAudioLayer('missing'), null);
  assert.equal(playLayer('missing'), false);
});
