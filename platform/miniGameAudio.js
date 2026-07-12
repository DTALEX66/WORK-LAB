const SOURCES = Object.freeze({
  click: 'audio/click.wav',
  anomaly: 'audio/anomaly.wav',
  result: 'audio/result.wav',
});

export function createMiniGameAudio(api) {
  const contexts = new Map();
  let muted = false;

  function getContext(cue) {
    if (contexts.has(cue)) return contexts.get(cue);
    if (!api || typeof api.createInnerAudioContext !== 'function') return null;
    const context = api.createInnerAudioContext();
    context.autoplay = false;
    context.loop = false;
    context.volume = cue === 'anomaly' ? 0.28 : 0.22;
    context.src = SOURCES[cue];
    contexts.set(cue, context);
    return context;
  }

  return {
    play(cue) {
      if (muted || !SOURCES[cue]) return false;
      const context = getContext(cue);
      if (!context || typeof context.play !== 'function') return false;
      try {
        context.stop?.();
        context.seek?.(0);
        const result = context.play();
        result?.catch?.(() => {});
        return true;
      } catch {
        return false;
      }
    },
    stopAll() {
      for (const context of contexts.values()) context.stop?.();
    },
    destroy() {
      for (const context of contexts.values()) context.destroy?.();
      contexts.clear();
    },
    setMuted(value) {
      muted = Boolean(value);
      if (muted) this.stopAll();
      return muted;
    },
    isMuted() {
      return muted;
    },
  };
}
