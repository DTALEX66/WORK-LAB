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
  for (const cue of ['click', 'anomaly', 'result', 'boot', 'release', 'lockdown', 'motor', 'wrong']) {
    assert.equal(audio.play(cue), true);
  }
  assert.deepEqual(played, [
    'audio/click.wav', 'audio/anomaly.wav', 'audio/result.wav', 'audio/boot.wav',
    'audio/release.wav', 'audio/lockdown.wav', 'audio/motor.wav', 'audio/wrong.wav',
  ]);
});

test('mini-game audio can be muted and fails safely without host audio API', () => {
  const audio = createMiniGameAudio({});
  assert.equal(audio.play('click'), false);
  audio.setMuted(true);
  assert.equal(audio.isMuted(), true);
  assert.equal(audio.play('result'), false);
});
