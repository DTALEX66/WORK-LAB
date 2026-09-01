/* WORK-LAB Observer — state.js
   Holds the current projection, data mode (LIVE/SNAPSHOT/OFFLINE/UNKNOWN/FIXTURE/REPLAY), view
   (full/compact), theme (dark/light), and last-good snapshot.
   Last-good survives failed refreshes: we never clear to zero on error. */

const WlState = (function () {
  "use strict";

  const state = {
    mode: "UNKNOWN",          // LIVE | SNAPSHOT | OFFLINE | UNKNOWN | FIXTURE | REPLAY
    view: "full",             // full | compact
    theme: "dark",            // dark | light
    data: null,               // current projection
    lastGood: null,           // last successfully rendered projection
    refreshError: null,
    freshnessState: "fresh",
    sourceCount: 0,
    generatedAt: null,
  };

  /* Empty/unspecified → UNKNOWN. A successful GET never implies LIVE. */
  function normalizeMode(m) {
    const v = String(m || "").toUpperCase();
    if (v === "LIVE" || v === "SNAPSHOT" || v === "OFFLINE" || v === "UNKNOWN" || v === "REPLAY") return v;
    if (v === "FIXTURE") return "FIXTURE";
    return "UNKNOWN";
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

  function staleCopy(data, freshnessState, transportOffline) {
    if (!data || typeof data !== "object") return data;
    const copy = JSON.parse(JSON.stringify(data));
    const timestamp = Date.parse(copy.generatedAt || (copy.freshness && copy.freshness.lastGoodAt) || "");
    const ageSeconds = Number.isFinite(timestamp) ? Math.max(0, Math.floor((Date.now() - timestamp) / 1000)) : null;
    copy.mode = state.mode;
    copy.freshness = Object.assign({}, copy.freshness || {}, {
      state: freshnessState,
      ageSeconds,
      lastGoodAt: (copy.freshness && copy.freshness.lastGoodAt) || copy.generatedAt || null,
    });
    if (copy.quality && typeof copy.quality === "object") copy.quality.freshness = freshnessState;
    if (transportOffline) {
      copy.transport = Object.assign({}, copy.transport || {}, {
        transportState: "OFFLINE",
        freshnessState: String(freshnessState || "offline").toUpperCase(),
        eventStreamConnected: false,
      });
    }
    if (Array.isArray(copy.projects)) {
      copy.projects.forEach((project) => {
        if (project.quality && typeof project.quality === "object") project.quality.freshness = freshnessState;
      });
    }
    return copy;
  }

  /* Accept a new projection (FIXTURE or LIVE). Never store a partial/empty as
     last-good if we already have something better. */
  function accept(data, mode) {
    const incomingRevision = data && Number.isInteger(data.revision) ? data.revision : null;
    const currentRevision = state.lastGood && Number.isInteger(state.lastGood.revision)
      ? state.lastGood.revision
      : null;
    if (incomingRevision !== null && currentRevision !== null && incomingRevision < currentRevision) {
      return state;
    }
    const m = normalizeMode(mode);
    state.mode = m;
    state.data = m === "SNAPSHOT" ? staleCopy(data, "stale") : data;
    state.generatedAt = data && data.generatedAt ? data.generatedAt : null;
    state.freshnessState = state.data && state.data.freshness ? state.data.freshness.state : "unknown";
    state.sourceCount = data && Array.isArray(data.sourceRefs) ? data.sourceRefs.length : 0;
    // v3 is authoritative even when it has zero approved projects.  The old
    // check required a rendered v2 summary and silently discarded valid v3
    // snapshots, which made the UI appear frozen or permanently offline.
    const validProjection = data && typeof data === "object"
      && Array.isArray(data.projects)
      && (data.schemaVersion === "workflow/snapshot/v3"
        || data.schemaVersion === "work-lab/observer-projection/v2-rendered"
        || (data.summary && typeof data.summary.registeredProjects === "number"));
    if (validProjection) {
      state.lastGood = data; // retain the unmodified last-good source projection
    }
    state.refreshError = null;
    return state;
  }

  /* On refresh failure: keep lastGood, mark stale/offline. Do not zero out. */
  function markRefreshError(message, transportOffline) {
    state.refreshError = message;
    if (transportOffline) state.mode = "OFFLINE";
    const nextFreshness = state.lastGood ? "stale" : "offline";
    state.freshnessState = nextFreshness;
    state.data = state.lastGood ? staleCopy(state.lastGood, nextFreshness, Boolean(transportOffline)) : null;
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
