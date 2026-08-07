/* WORK-LAB Observer — state.js
   Holds the current projection, data mode (FIXTURE/LIVE/REPLAY), view
   (full/compact), theme (dark/light), and last-good snapshot.
   Last-good survives failed refreshes: we never clear to zero on error. */

const WlState = (function () {
  "use strict";

  const state = {
    mode: "LIVE",             // FIXTURE | LIVE | REPLAY — default LIVE (real data first)
    view: "full",             // full | compact
    theme: "dark",            // dark | light
    data: null,               // current projection
    lastGood: null,           // last successfully rendered projection
    refreshError: null,
    freshnessState: "fresh",
    sourceCount: 0,
    generatedAt: null,
  };

  /* Mode must be one of the three valid values. Empty/unspecified → LIVE (real data first). */
  function normalizeMode(m) {
    const v = String(m || "").toUpperCase();
    if (v === "LIVE" || v === "REPLAY") return v;
    if (v === "FIXTURE") return "FIXTURE";
    return "LIVE"; // default: real data
  }

  function normalizeView(v) {
    return v === "compact" ? "compact" : "full";
  }

  function normalizeTheme(t) {
    return t === "light" ? "light" : "dark";
  }

  function set(partial) {
    Object.assign(state, partial);
  }

  /* Accept a new projection (FIXTURE or LIVE). Never store a partial/empty as
     last-good if we already have something better. */
  function accept(data, mode) {
    const m = normalizeMode(mode);
    state.mode = m;
    state.data = data;
    state.generatedAt = data && data.generatedAt ? data.generatedAt : null;
    state.freshnessState = data && data.freshness ? data.freshness.state : "unknown";
    state.sourceCount = data && Array.isArray(data.sourceRefs) ? data.sourceRefs.length : 0;
    if (data && data.summary && typeof data.summary.registeredProjects === "number") {
      state.lastGood = data; // a real projection is a valid last-good
    }
    state.refreshError = null;
    return state;
  }

  /* On refresh failure: keep lastGood, mark stale/offline. Do not zero out. */
  function markRefreshError(message) {
    state.refreshError = message;
    if (state.mode === "LIVE" && state.lastGood) {
      state.freshnessState = "stale";
    }
    return state;
  }

  function get() {
    return state;
  }

  return { get, set, accept, markRefreshError, normalizeMode, normalizeView, normalizeTheme };
})();

if (typeof module !== "undefined" && module.exports) {
  module.exports = { WlState };
}
