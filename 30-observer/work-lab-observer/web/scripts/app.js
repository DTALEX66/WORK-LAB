/* WORK-LAB Observer — app.js
   Entry point. Bootstraps state from URL params, reads FIXTURE inline,
   fetches GET /api/v1/snapshot (v3) for live data, renders the active view,
   wires theme/view toggles and keyboard nav. Never writes to the server. */

const WlApp = (function () {
  "use strict";

  const APP_ROOT = "wl-app";
  let eventSource = null;
  let eventSourceUrl = null;
  let reconnectTimer = null;
  let reconnectDelayMs = 1000;
  let snapshotRetryTimer = null;
  let snapshotRetryDelayMs = 1000;

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

    // full view — one truthful reading flow; no dead navigation.
    root.className = "wl-shell";
    let content;
    if (isV3Surface(d)) {
      content = WlRenderV3.full(d);
    } else {
      content = `<div class="wl-grid">${WlRender.renderFull(d)}</div>`;
    }
    root.innerHTML =
      WlRender.topbar(d) +
      `<div class="wl-body-full"><main class="wl-content">${content}</main></div>` +
      WlRender.footer(d);
    applyTheme(st.theme);
    wireToggles(root);
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

  }

  function clearSnapshotRetry() {
    if (snapshotRetryTimer !== null) clearTimeout(snapshotRetryTimer);
    snapshotRetryTimer = null;
    snapshotRetryDelayMs = 1000;
  }

  function scheduleSnapshotRetry() {
    if (snapshotRetryTimer !== null) return;
    const delay = snapshotRetryDelayMs;
    snapshotRetryDelayMs = Math.min(snapshotRetryDelayMs * 2, 30000);
    snapshotRetryTimer = setTimeout(async () => {
      snapshotRetryTimer = null;
      await loadData();
      render();
    }, delay);
  }

  function closeEventSource() {
    if (eventSource && typeof eventSource.close === "function") eventSource.close();
    eventSource = null;
    eventSourceUrl = null;
  }

  function stopLiveSubscription() {
    if (reconnectTimer !== null) clearTimeout(reconnectTimer);
    reconnectTimer = null;
    reconnectDelayMs = 1000;
    closeEventSource();
  }

  function scheduleLiveReconnect() {
    if (reconnectTimer !== null) return;
    const delay = reconnectDelayMs;
    reconnectDelayMs = Math.min(reconnectDelayMs * 2, 30000);
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      const st = WlState.get();
      const projection = st.data || st.lastGood;
      if (!projection) return;
      closeEventSource();
      startLiveSubscription(projection);
    }, delay);
  }

  function startLiveSubscription(projection) {
    const url = projection && projection.transport && projection.transport.eventsUrl;
    if (!url) {
      stopLiveSubscription();
      return false;
    }
    if (eventSource && eventSourceUrl === url) return true;
    if (reconnectTimer !== null) clearTimeout(reconnectTimer);
    reconnectTimer = null;
    closeEventSource();
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
        onOpen: async () => {
          if (reconnectTimer !== null) clearTimeout(reconnectTimer);
          reconnectTimer = null;
          reconnectDelayMs = 1000;
          try {
            const result = await WlApi.fetchSnapshot();
            clearSnapshotRetry();
            WlState.accept(result.data, result.mode);
          } catch (err) {
            WlState.markRefreshError(err && err.message ? err.message : "事件流重连后投影刷新失败");
            scheduleSnapshotRetry();
          }
          render();
        },
        onError: () => {
          WlState.markRefreshError("Workflow Sidecar 事件流离线，正在自动重连");
          render();
          scheduleLiveReconnect();
        },
      });
      return true;
    } catch (err) {
      eventSource = null;
      eventSourceUrl = null;
      WlState.markRefreshError(err && err.message ? err.message : "事件流不可用");
      scheduleLiveReconnect();
      return false;
    }
  }

  /* Read the projection source. FIXTURE first; attempt LIVE via GET only. */
  async function loadData() {
    const st = WlState.get();
    if (st.mode === "FIXTURE" || st.mode === "REPLAY") {
      clearSnapshotRetry();
      stopLiveSubscription();
      // FIXTURE: use inline authoritative copy (no network). REPLAY unsupported -> fixture fallback.
      WlState.accept(WlApi.FIXTURE, "FIXTURE");
      return;
    }
    // LIVE: GET /api/v1/snapshot (canonical v3); legacy dashboard retired.
    // P0-7: on failure the UI shows OFFLINE/UNKNOWN — never auto-fallback to a
    // bundled snapshot or FIXTURE. Fixture only loads via an explicit dev entry.
    try {
      const result = await WlApi.fetchSnapshot();
      clearSnapshotRetry();
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
      scheduleSnapshotRetry();
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
