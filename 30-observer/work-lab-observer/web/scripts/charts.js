/* WORK-LAB Observer — charts.js
   Native SVG line/area/sparkline only. No pie/donut/3D, no smoothing curves,
   no runtime chart library. Each chart exposes window/unit/timezone/truncation
   notes plus an accessible text summary. Max 5 series. */

const WlCharts = (function () {
  "use strict";

  /* Deterministic palette (blue/green/amber/red/purple from tokens). */
  const PALETTE = ["#0a84ff", "#30d158", "#ff9f0a", "#bf5af2", "#64d2ff"];
  const W = 640;
  const H = 220;
  const PAD = { top: 14, right: 12, bottom: 30, left: 44 };

  /* Build a multi-series straight-line SVG. `series` = [{label, points:[{x,y}], color}] */
  function lineChart(series, opts) {
    opts = opts || {};
    const width = opts.width || W;
    const height = opts.height || H;
    const pad = Object.assign({}, PAD, opts.pad || {});

    // Flatten all points for domain.
    const allX = [];
    const allY = [];
    series.forEach((s) => (s.points || []).forEach((p) => { allX.push(p.x); allY.push(p.y); }));
    const minX = allX.length ? Math.min.apply(null, allX) : 0;
    const maxX = allX.length ? Math.max.apply(null, allX) : 1;
    const rawMinY = allY.length ? Math.min.apply(null, allY) : 0;
    const rawMaxY = allY.length ? Math.max.apply(null, allY) : 1;
    const spanX = maxX - minX || 1;
    const minY = Math.min(0, rawMinY); // baseline at 0 for token area feel
    const maxY = Math.max(rawMaxY, rawMinY + 1);

    function sx(x) { return pad.left + ((x - minX) / spanX) * (width - pad.left - pad.right); }
    function sy(y) {
      const r = maxY - minY || 1;
      return pad.top + (1 - (y - minY) / r) * (height - pad.top - pad.bottom);
    }

    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;

    // horizontal gridlines (5)
    let grid = "";
    for (let i = 0; i <= 4; i++) {
      const gy = pad.top + (plotH / 4) * i;
      const val = maxY - ((maxY - minY) / 4) * i;
      const label = formatAxisVal(val);
      grid += `<line class="wl-gridline" x1="${pad.left}" y1="${gy}" x2="${width - pad.right}" y2="${gy}"/>`;
      grid += `<text x="${pad.left - 6}" y="${gy + 4}" text-anchor="end" class="wl-axis" font-size="10" fill="var(--wl-text-muted)">${label}</text>`;
    }

    // series paths (straight polyline, no smoothing)
    let paths = "";
    let area = "";
    let ptsLabels = "";
    series.forEach((s, si) => {
      if (!s.points || !s.points.length) return;
      const color = s.color || PALETTE[si % PALETTE.length];
      const d = s.points.map((p, i) => (i === 0 ? "M" : "L") + sx(p.x).toFixed(1) + " " + sy(p.y).toFixed(1)).join(" ");
      paths += `<path d="${d}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`;
      if (si === 0 && opts.area) {
        const first = s.points[0];
        const last = s.points[s.points.length - 1];
        area = `<path d="M${sx(first.x)} ${sy(minY)} L${sx(first.x)} ${sy(first.y)} L${sx(last.x)} ${sy(last.y)} L${sx(last.x)} ${sy(minY)} Z" fill="${color}" opacity="0.08"/>`;
      }
    });

    // x labels (first/mid/last)
    let xl = "";
    const xBuckets = opts.buckets || [];
    if (xBuckets.length) {
      [0, Math.floor((xBuckets.length - 1) / 2), xBuckets.length - 1].forEach((idx) => {
        if (idx < 0) return;
        const b = xBuckets[idx];
        const t = typeof b === "number" ? String(b) : String(b);
        xl += `<text x="${pad.left + (plotW / (xBuckets.length - 1 || 1)) * idx}" y="${height - 10}" text-anchor="middle" class="wl-axis" font-size="10" fill="var(--wl-text-muted)">${t}</text>`;
      });
    }

    const legend = series
      .map((s, si) => `<span class="wl-lg"><i style="background:${s.color || PALETTE[si % PALETTE.length]}"></i>${escapeAttr(s.label)}</span>`)
      .join("");

    const summary = series
      .map((s, si) => {
        const vals = (s.points || []).map((p) => p.y);
        const peak = vals.length ? Math.max.apply(null, vals) : 0;
        return s.label + " 峰值 " + formatAxisVal(peak);
      })
      .join("；");

    return {
      svg:
        `<div class="wl-chart">` +
        `<div class="wl-chart-legend">${legend}</div>` +
        `<svg role="img" aria-label="${escapeAttr(opts.ariaLabel || "趋势折线图")}" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" preserveAspectRatio="xMidYMid meet">` +
        `<title>${escapeAttr(opts.ariaLabel || "趋势折线图")}</title>` +
        `<desc>${escapeAttr(opts.ariaDesc || summary + "。" + (opts.notes || ""))}</desc>` +
        grid + area + paths + xl +
        `</svg>` +
        `<div class="wl-chart-notes">` +
        `<span>窗口：${escapeAttr(opts.window || "")}</span>` +
        `<span>单位：${escapeAttr(opts.unit || "tokens")}</span>` +
        `<span>时区：${escapeAttr(opts.timezone || "")}</span>` +
        `<span>截断：${escapeAttr(opts.truncation || "仅最近 N 桶")}</span>` +
        `</div>` +
        `</div>`,
      summary,
    };
  }

  function formatAxisVal(v) {
    if (v >= 1e6) return (v / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
    if (v >= 1e3) return (v / 1e3).toFixed(0) + "k";
    return String(Math.round(v));
  }

  function escapeAttr(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  return { lineChart, PALETTE };
})();

if (typeof module !== "undefined" && module.exports) {
  module.exports = { WlCharts };
}
