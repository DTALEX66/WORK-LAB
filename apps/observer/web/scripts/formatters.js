/* WORK-LAB Observer — formatters.js
   Pure formatting helpers. No DOM access. Testable in isolation. */

const WlFormat = (function () {
  "use strict";

  const NULL_DASH = "—";

  function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  /* Integer with thousands separators, or — when null/undefined. */
  function intOrDash(value) {
    if (value === null || value === undefined) return NULL_DASH;
    const n = Number(value);
    if (!Number.isFinite(n)) return NULL_DASH;
    return Math.round(n).toLocaleString("en-US");
  }

  /* Token count with unit. Never fabricate a total token. */
  function tokens(value) {
    const n = intOrDash(value);
    return n === NULL_DASH ? NULL_DASH : n + " tokens";
  }

  /* Compact token count: 64.4K / 26.8K. */
  function tokensCompact(value) {
    if (value === null || value === undefined) return NULL_DASH;
    const n = Number(value);
    if (!Number.isFinite(n)) return NULL_DASH;
    if (n >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
    if (n >= 1e3) return (n / 1e3).toFixed(1).replace(/\.0$/, "") + "K";
    return String(n);
  }

  /* Cost amount with currency; label-driven by status in renderer. */
  function costAmount(cost) {
    if (!cost || cost.amount === null || cost.amount === undefined) return NULL_DASH;
    const amount = Number(cost.amount);
    if (!Number.isFinite(amount)) return NULL_DASH;
    return "$" + amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  /* Duration in seconds -> human readable. */
  function duration(seconds) {
    if (seconds === null || seconds === undefined) return NULL_DASH;
    const s = Number(seconds);
    if (!Number.isFinite(s) || s < 0) return NULL_DASH;
    if (s < 60) return s + "s";
    const m = Math.floor(s / 60);
    if (m < 60) return m + "m";
    const h = Math.floor(m / 60);
    const remM = m % 60;
    if (h < 24) return h + "h " + (remM ? remM + "m" : "");
    const d = Math.floor(h / 24);
    const remH = h % 24;
    return d + "d " + (remH ? remH + "h" : "");
  }

  /* Relative time from an ISO string against `now`. */
  function relativeTime(iso, now) {
    if (!iso) return NULL_DASH;
    const t = new Date(iso).getTime();
    if (!Number.isFinite(t)) return NULL_DASH;
    now = now || Date.now();
    const diff = Math.max(0, now - t);
    const sec = Math.floor(diff / 1000);
    if (sec < 60) return sec + "s";
    const min = Math.floor(sec / 60);
    if (min < 60) return min + "m";
    const hr = Math.floor(min / 60);
    if (hr < 24) return hr + "h";
    const d = Math.floor(hr / 24);
    if (d < 30) return d + "d";
    const mo = Math.floor(d / 30);
    return mo + "mo";
  }

  /* Absolute time with timezone, for detail views. */
  function absoluteTime(iso) {
    if (!iso) return NULL_DASH;
    const t = new Date(iso);
    if (!Number.isFinite(t.getTime())) return NULL_DASH;
    try {
      return t.toLocaleString("zh-CN", {
        year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit", second: "2-digit",
        hour12: false,
      });
    } catch (e) {
      return iso;
    }
  }

  /* Freshness age label. */
  function freshnessAge(ageSeconds) {
    if (ageSeconds === null || ageSeconds === undefined) return NULL_DASH;
    return duration(ageSeconds);
  }

  /* Coverage: "11 / 14". */
  function coverage(sourceCoverage) {
    if (!sourceCoverage) return NULL_DASH;
    return intOrDash(sourceCoverage.numerator) + " / " + intOrDash(sourceCoverage.denominator);
  }

  /* Short SHA: first 7 chars. */
  function shortSha(sha, len) {
    if (!sha) return NULL_DASH;
    const l = len || 7;
    return sha.length > l ? sha.slice(0, l) : sha;
  }

  return {
    NULL_DASH,
    escapeHtml,
    intOrDash,
    tokens,
    tokensCompact,
    costAmount,
    duration,
    relativeTime,
    absoluteTime,
    freshnessAge,
    coverage,
    shortSha,
  };
})();

if (typeof module !== "undefined" && module.exports) {
  module.exports = { WlFormat };
}
