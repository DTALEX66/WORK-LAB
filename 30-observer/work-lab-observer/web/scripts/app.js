/* WORK-LAB Observer — app.js
   Entry point. Bootstraps state from URL params, reads FIXTURE inline,
   optionally fetches GET /api/dashboard for LIVE, renders the active view,
   wires theme/view toggles and keyboard nav. Never writes to the server. */

const WlApp = (function () {
  "use strict";

  const APP_ROOT = "wl-app";
  let eventSource = null;
  let eventSourceUrl = null;

  function readParams() {
    const q = new URLSearchParams(window.location.search);
    const view = WlState.normalizeView(q.get("view"));
    const theme = WlState.normalizeTheme(q.get("theme"));
    const mode = WlState.normalizeMode(q.get("mode"));
    WlState.set({ view, theme, mode });
    return { view, theme, mode };
  }

  function retainedApiParam() {
    const api = new URLSearchParams(window.location.search).get("api");
    return api ? "&api=" + encodeURIComponent(api) : "";
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

  function isV3Surface(d) {
    return d && d.schemaVersion === "work-lab/observer-projection/v2-rendered";
  }

  function render() {
    const st = WlState.get();
    const root = document.getElementById(APP_ROOT);
    const d = st.data || st.lastGood;

    if (!d) {
      root.innerHTML = `<div class="wl-state-note" style="max-width:600px;margin:40px auto">${WlRender.icon("info")}${st.mode === "OFFLINE" ? "数据源离线（OFFLINE，不加载假数据）" : "尚无可用投影数据。"}</div>`;
      return;
    }

    if (st.view === "compact") {
      const inner = isV3Surface(d) ? WlRenderV3.compact(d) : WlRender.renderCompact(d);
      root.className = "wl-shell wl-compact";
      root.innerHTML = `<div class="wl-compact">${inner}</div>` + (isV3Surface(d) ? "" : WlRender.footer(d));
      // move tools into a small top row
      const bar = document.createElement("div");
      bar.className = "wl-robar";
      bar.style.padding = "8px 16px";
      bar.innerHTML =
        `<a class="wl-view-link" href="?view=full&theme=${st.theme}&mode=${st.mode}${retainedApiParam()}">${WlRender.icon("grid")}完整视图</a>` +
        `<button class="wl-theme-toggle" id="themeToggle" type="button">${WlRender.icon(st.theme === "dark" ? "sun" : "moon")}</button>`;
      root.prepend(bar);
      applyTheme(st.theme);
      wireToggles(root);
      return;
    }

    // full view
    const active = "overview";
    root.className = "wl-shell";
    let content;
    if (isV3Surface(d)) {
      content =
        WlRenderV3.globalBar(d) +
        WlRenderV3.kpi(d) +
        WlRenderV3.projectTable(d) +
        WlRenderV3.executionsTable(d) +
        WlRenderV3.tokenCi(d);
    } else {
      content = `<div class="wl-grid">${WlRender.renderFull(d)}</div>`;
    }
    root.innerHTML =
      WlRender.topbar(d) +
      `<div class="wl-body-full">${WlRender.sidebar(active)}<main class="wl-content"><div class="wl-grid">${content}</div></main></div>` +
      WlRender.footer(d);
    applyTheme(st.theme);
    wireToggles(root);
    // v3: project row click -> detail (WLGM-190)
    if (isV3Surface(d)) {
      const rows = root.querySelectorAll(".wl-proj-row");
      rows.forEach((row) => {
        row.addEventListener("click", () => {
          const pid = row.getAttribute("data-project");
          const detailBox = document.getElementById("wl-v3-detail");
          if (detailBox) {
            const already = detailBox.querySelector(`[data-project-detail="${pid}"]`);
            if (already) { already.remove(); return; }
            detailBox.innerHTML = WlRenderV3.projectDetail(d, pid);
            const box = detailBox.querySelector(`[data-project-detail="${pid}"]`);
            if (box) box.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }
        });
        row.addEventListener("keydown", (ev) => {
          if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); row.click(); }
        });
      });
    }
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

  function stopLiveSubscription() {
    if (eventSource && typeof eventSource.close === "function") eventSource.close();
    eventSource = null;
    eventSourceUrl = null;
  }

  function startLiveSubscription(projection) {
    const url = projection && projection.transport && projection.transport.eventsUrl;
    if (!url) {
      stopLiveSubscription();
      return false;
    }
    if (eventSource && eventSourceUrl === url) return true;
    stopLiveSubscription();
    eventSourceUrl = url;
    try {
      eventSource = WlApi.subscribeEvents(url, {
        onEvent: async () => {
          try {
            const result = await WlApi.fetchSnapshot();
            WlState.accept(result.data, result.mode);
          } catch (err) {
            WlState.markRefreshError(err && err.message ? err.message : "实时投影刷新失败");
          }
          render();
        },
        onError: () => {
          WlState.markRefreshError("Workflow Sidecar 事件流离线，正在自动重连");
          render();
        },
      });
      return true;
    } catch (err) {
      eventSource = null;
      eventSourceUrl = null;
      WlState.markRefreshError(err && err.message ? err.message : "事件流不可用");
      return false;
    }
  }

  /* Read the projection source. FIXTURE first; attempt LIVE via GET only. */
  async function loadData() {
    const st = WlState.get();
    if (st.mode === "FIXTURE" || st.mode === "REPLAY") {
      stopLiveSubscription();
      // FIXTURE: use inline authoritative copy (no network). REPLAY unsupported -> fixture fallback.
      WlState.accept(WlApi.FIXTURE, "FIXTURE");
      return;
    }
    // LIVE: GET /api/v1/snapshot (canonical v3), legacy /api/dashboard tolerated.
    // P0-7: on failure the UI shows OFFLINE/UNKNOWN — never auto-fallback to a
    // bundled snapshot or FIXTURE. Fixture only loads via an explicit dev entry.
    try {
      const result = await WlApi.fetchSnapshot();
      WlState.accept(result.data, result.mode);
      startLiveSubscription(result.data);
      WlA11y.announce(result.mode === "LIVE" ? "已加载实时投影数据" : "已加载只读投影数据");
    } catch (err) {
      stopLiveSubscription();
      WlState.markRefreshError(err.message);
      if (WlState.get().lastGood) {
        WlState.set({ mode: "OFFLINE" });
        WlA11y.announce("实时数据不可用，已保留上次良好投影（last-good，标记为 STALE）");
      } else {
        WlState.accept(null, "OFFLINE");
        WlA11y.announce("实时数据不可用，界面显示 OFFLINE（不加载假数据）");
      }
    }
  }

  async function init() {
    readParams();
    await loadData();
    render();
  }

  /* Exposed for tests / debugging. */
  return { init, readParams, applyTheme, render, loadData, startLiveSubscription, stopLiveSubscription };
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
