/* WORK-LAB Observer — app.js
   Entry point. Bootstraps state from URL params, reads FIXTURE inline,
   optionally fetches GET /api/dashboard for LIVE, renders the active view,
   wires theme/view toggles and keyboard nav. Never writes to the server. */

const WlApp = (function () {
  "use strict";

  const APP_ROOT = "wl-app";

  function readParams() {
    const q = new URLSearchParams(window.location.search);
    const view = WlState.normalizeView(q.get("view"));
    const theme = WlState.normalizeTheme(q.get("theme"));
    const mode = WlState.normalizeMode(q.get("mode"));
    WlState.set({ view, theme, mode });
    return { view, theme, mode };
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    WlState.set({ theme });
    const btn = document.getElementById("themeToggle");
    if (btn) {
      btn.setAttribute("aria-label", theme === "dark" ? "切换到浅色主题" : "切换到深色主题");
      btn.title = theme === "dark" ? "切换到浅色主题" : "切换到深色主题";
      btn.innerHTML = WlRender.icon(theme === "dark" ? "sun" : "moon");
    }
  }

  function render() {
    const st = WlState.get();
    const root = document.getElementById(APP_ROOT);
    const d = st.data || st.lastGood;

    if (!d) {
      root.innerHTML = `<div class="wl-state-note" style="max-width:600px;margin:40px auto">${WlRender.icon("info")}尚无可用投影数据。</div>`;
      return;
    }

    if (st.view === "compact") {
      const inner = WlRender.renderCompact(d);
      root.className = "wl-shell wl-compact";
      root.innerHTML = `<div class="wl-compact">${inner}</div>` + WlRender.footer(d);
      // move tools into a small top row
      const bar = document.createElement("div");
      bar.className = "wl-robar";
      bar.style.padding = "8px 16px";
      bar.innerHTML =
        `<a class="wl-view-link" href="?view=full&theme=${st.theme}&mode=${st.mode}">${WlRender.icon("grid")}完整视图</a>` +
        `<button class="wl-theme-toggle" id="themeToggle" type="button">${WlRender.icon(st.theme === "dark" ? "sun" : "moon")}</button>`;
      root.prepend(bar);
      applyTheme(st.theme);
      wireToggles(root);
      return;
    }

    // full view
    const active = "overview";
    root.className = "wl-shell";
    root.innerHTML =
      WlRender.topbar(d) +
      `<div class="wl-body-full">${WlRender.sidebar(active)}<main class="wl-content"><div class="wl-grid">${WlRender.renderFull(d)}</div></main></div>` +
      WlRender.footer(d);
    applyTheme(st.theme);
    wireToggles(root);
    // sidebar nav
    const side = root.querySelector("nav.wl-sidebar");
    if (side) {
      WlA11y.bindSectionNav(side, active);
    }
  }

  function wireToggles(root) {
    const themeBtn = document.getElementById("themeToggle");
    if (themeBtn) {
      themeBtn.addEventListener("click", () => {
        const next = WlState.get().theme === "dark" ? "light" : "dark";
        applyTheme(next);
        // memory-only; not sent to server. persist in history for shareable link.
        const url = new URL(window.location.href);
        url.searchParams.set("theme", next);
        window.history.replaceState({}, "", url.toString());
        WlA11y.announce("已切换为" + (next === "dark" ? "深色" : "浅色") + "主题");
        render();
      });
    }
    // Appearance settings: background mode + glass opacity (memory-only CSS vars).
    const settingsBtn = document.getElementById("settingsToggle");
    const panel = document.getElementById("wl-settings");
    if (settingsBtn && panel) {
      settingsBtn.addEventListener("click", () => {
        panel.classList.toggle("open");
        if (panel.classList.contains("open")) {
          panel.querySelector("#wl-bg-mode").focus();
        }
      });
      const bg = panel.querySelector("#wl-bg-mode");
      const opacity = panel.querySelector("#wl-opacity");
      const opacityVal = panel.querySelector("#wl-opacity-val");
      const apply = () => {
        document.documentElement.setAttribute("data-bg", bg.value);
        const o = Number(opacity.value) / 100;
        document.documentElement.style.setProperty("--wl-opacity", String(o));
        if (opacityVal) opacityVal.textContent = opacity.value;
      };
      bg.addEventListener("change", apply);
      opacity.addEventListener("input", apply);
    }
  }

  /* Read the projection source. FIXTURE first; attempt LIVE via GET only. */
  async function loadData() {
    const st = WlState.get();
    if (st.mode === "FIXTURE" || st.mode === "REPLAY") {
      // FIXTURE: use inline authoritative copy (no network). REPLAY unsupported -> fixture fallback.
      WlState.accept(WlApi.FIXTURE, "FIXTURE");
      return;
    }
    // LIVE: try GET /api/dashboard; on failure fall back to a bundled REAL snapshot
    // (assets/live-snapshot.json, generated from real observed events), then FIXTURE.
    try {
      const result = await WlApi.fetchDashboard();
      WlState.accept(result.data, "LIVE");
      WlA11y.announce("已加载实时投影数据");
    } catch (err) {
      // Bundled real snapshot (no fabricated agents/projects) — better than FIXTURE.
      try {
        const snapRes = await fetch("assets/live-snapshot.json", { cache: "no-store" });
        if (snapRes.ok) {
          const snap = await snapRes.json();
          WlState.accept(snap, "SNAPSHOT");
          WlA11y.announce("已加载最近真实投影快照（live-snapshot）");
          return;
        }
      } catch (_) { /* fall through */ }
      WlState.markRefreshError(err.message);
      if (WlState.get().lastGood) {
        WlState.set({ mode: "LIVE" });
        WlA11y.announce("实时数据不可用，已保留上次良好投影（last-good）");
      } else {
        WlState.accept(WlApi.FIXTURE, "FIXTURE");
        WlA11y.announce("实时数据不可用，回退到 FIXTURE 数据");
      }
    }
  }

  async function init() {
    readParams();
    await loadData();
    render();
  }

  /* Exposed for tests / debugging. */
  return { init, readParams, applyTheme, render, loadData };
})();

if (typeof window !== "undefined") {
  window.addEventListener("DOMContentLoaded", () => {
    WlApp.init().catch((err) => {
      // eslint-disable-next-line no-console
      console.error("Observer UI boot failed:", err);
      const root = document.getElementById("wl-app");
      if (root) {
        root.innerHTML = `<div class="wl-state-note" style="max-width:600px;margin:40px auto">${WlRender.icon("failed")}界面初始化失败：${WlFormat.escapeHtml(String(err && err.message ? err.message : err))}</div>`;
      }
    });
  });
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { WlApp };
}
