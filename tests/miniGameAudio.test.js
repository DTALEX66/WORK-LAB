import assert from 'node:assert/strict';
import test from 'node:test';

import { createMiniGameAudio } from '../platform/miniGameAudio.js';

test('mini-game audio maps semantic cues to bundled local files', () => {
  const played = [];
  const api = {
    createInnerAudioContext() {
      return {
        set src(value) { this._src = value; },
        get src() { return this._src; },
        play() { played.push(this.src); },
        stop() {},
        destroy() {},
      };
    },
  };
  const audio = createMiniGameAudio(api);
  assert.equal(audio.play('click'), true);
  assert.equal(audio.play('anomaly'), true);
  assert.equal(audio.play('result'), true);
  assert.deepEqual(played, ['audio/click.wav', 'audio/anomaly.wav', 'audio/result.wav']);
});

test('mini-game audio can be muted and fails safely without host audio API', () => {
  const audio = createMiniGameAudio({});
  assert.equal(audio.play('click'), false);
  audio.setMuted(true);
  assert.equal(audio.isMuted(), true);
  assert.equal(audio.play('result'), false);
});
