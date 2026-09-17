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
  let streamRefreshPromise = null;
  let streamRefreshQueuedEpoch = null;
  let eventSourceGeneration = 0;
  let transportEpoch = 0;
  let eventStreamConnected = false;

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

  /* Redesign: unified v3 surface. The canonical sidecar snapshot is
     workflow/snapshot/v3; legacy v2-rendered projections also render via v3. */
  function isV3Surface(d) {
    if (!d) return false;
    return d.schemaVersion === "workflow/snapshot/v3"
      || d.schemaVersion === "work-lab/observer-projection/v2-rendered";
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
      const inner = isV3Surface(d) ? (typeof WlFusionV3 !== "undefined" && WlFusionV3.renderCompact ? WlFusionV3.renderCompact(d) : WlRenderV3.compact(d)) : WlRender.renderCompact(d);
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
      // Fusion Command Center: signal strip + cross-project matrix + token dash.
      // Single render source — no duplicated matrices (platformStatusMatrix /
      // governanceAndGaps are already inside WlFusionV3.render when relevant).
      content = typeof WlFusionV3 !== "undefined"
        ? WlFusionV3.render(d)
        : WlRenderV3.full(d);
    } else {
      content = `<div class="wl-grid">${WlRender.renderFull(d)}</div>`;
    }
    if (typeof WlFusionV3 !== "undefined" && isV3Surface(d)) {
      root.className = "wl-shell wl-cc";
      root.innerHTML = content;
    } else {
      root.innerHTML =
        WlRender.topbar(d) +
        `<div class="wl-body-full"><main class="wl-content">${content}</main></div>` +
        WlRender.footer(d);
    }
    applyTheme(st.theme);
    wireToggles(root);
    wireObservabilityData(root);
  }

  /* Observability: render WORK-LAB metrics natively from the local Prometheus
     API (no iframe nesting). Deep tools (Grafana/Phoenix/Loki) stay as links. */
  function wireObservabilityData(root) {
    const kpis = root.querySelector("#wl-obskpis");
    if (!kpis) return;
    const defs = [
      { expr: "wlobs_projects", label: "项目", fmt: "int" },
      { expr: "wlobs_executions", label: "执行实例", fmt: "int" },
      { expr: "wlobs_usage_tokens{kind=\"total\"}", label: "Token 总量", fmt: "short" },
      { expr: "wlobs_cost_estimate", label: "成本 (USD)", fmt: "cost" },
      { expr: "wlobs_platform_observations", label: "平台观测", fmt: "int" }
    ];
    function fmt(v, kind) {
      if (kind === "short") return v >= 1e6 ? (v / 1e6).toFixed(2) + "M" : v >= 1e3 ? (v / 1e3).toFixed(1) + "K" : v.toFixed(0);
      if (kind === "cost") return "$" + v.toFixed(2);
      return v.toFixed(0);
    }
    Promise.all(defs.map(function (def) {
      return fetch("http://127.0.0.1:9090/api/v1/query?query=" + encodeURIComponent(def.expr))
        .then(function (res) { return res.json(); })
        .then(function (j) {
          const list = (j.data && j.data.result) || [];
          const total = list.reduce(function (a, item) { return a + (parseFloat(item.value[1]) || 0); }, 0);
          return { def: def, total: total, series: list.length };
        })
        .catch(function () { return null; });
    })).then(function (results) {
      const cards = results.filter(Boolean).map(function (r) {
        return '<div class="wl-obskpi"><span>' + r.def.label + '</span><b>' + fmt(r.total, r.def.fmt) + '</b></div>';
      }).join("");
      kpis.innerHTML = cards || '<span class="wl-empty">指标不可用</span>';
    });
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
    eventSourceGeneration += 1;
    transportEpoch += 1;
    eventStreamConnected = false;
    streamRefreshQueuedEpoch = null;
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

  function refreshFromStream(expectedEpoch) {
    if (!eventStreamConnected || expectedEpoch !== transportEpoch) return Promise.resolve();
    if (streamRefreshPromise) {
      streamRefreshQueuedEpoch = expectedEpoch;
      return streamRefreshPromise;
    }
    streamRefreshPromise = (async () => {
      let refreshEpoch = expectedEpoch;
      while (eventStreamConnected && refreshEpoch === transportEpoch) {
        streamRefreshQueuedEpoch = null;
        let shouldRender = false;
        try {
          const result = await WlApi.fetchSnapshot();
          if (eventStreamConnected && refreshEpoch === transportEpoch) {
            WlState.accept(result.data, result.mode);
            if (WlState.get().lastGood === result.data) {
              clearSnapshotRetry();
              startLiveSubscription(result.data);
            }
            shouldRender = true;
          }
        } catch (err) {
          if (eventStreamConnected && refreshEpoch === transportEpoch) {
            WlState.markRefreshError(err && err.message ? err.message : "实时投影刷新失败");
            scheduleSnapshotRetry();
            shouldRender = true;
          }
        }
        if (shouldRender) render();
        const queuedEpoch = streamRefreshQueuedEpoch;
        if (!eventStreamConnected || queuedEpoch === null || queuedEpoch !== transportEpoch) break;
        refreshEpoch = queuedEpoch;
      }
    })().finally(() => {
      streamRefreshPromise = null;
    });
    return streamRefreshPromise;
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
    const sourceGeneration = eventSourceGeneration;
    try {
      eventSource = WlApi.subscribeEvents(url, {
        onEvent: async (_payload, _lastEventId, eventName) => {
          if (sourceGeneration !== eventSourceGeneration || !eventStreamConnected) return;
          if (eventName === "heartbeat") return;
          await refreshFromStream(transportEpoch);
        },
        onOpen: async () => {
          if (sourceGeneration !== eventSourceGeneration) return;
          if (reconnectTimer !== null) clearTimeout(reconnectTimer);
          reconnectTimer = null;
          reconnectDelayMs = 1000;
          eventStreamConnected = true;
          transportEpoch += 1;
          await refreshFromStream(transportEpoch);
        },
        onError: () => {
          if (sourceGeneration !== eventSourceGeneration) return;
          eventStreamConnected = false;
          transportEpoch += 1;
          WlState.markRefreshError("Workflow Sidecar 事件流离线，正在自动重连", true);
          render();
          scheduleSnapshotRetry();
          // Keep the EventSource instance alive. Browser-native reconnect
          // preserves Last-Event-ID; manual close/recreate would discard it.
        },
        onProtocolError: () => {
          if (sourceGeneration !== eventSourceGeneration) return;
          // Framing is still connected. Fence older GETs but preserve the
          // browser-owned EventSource and Last-Event-ID cursor.
          transportEpoch += 1;
          WlState.markRefreshError("Workflow Sidecar 事件格式无效，正在重新读取快照", true);
          render();
          scheduleSnapshotRetry();
        },
      });
      return true;
    } catch (err) {
      eventSource = null;
      eventSourceUrl = null;
      WlState.markRefreshError(err && err.message ? err.message : "事件流不可用", true);
      scheduleSnapshotRetry();
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
      WlState.accept(result.data, result.mode);
      if (WlState.get().lastGood !== result.data) {
        return; // a delayed lower revision cannot rotate transport identity
      }
      if (result.mode === "LIVE" && eventSource && !eventStreamConnected) {
        startLiveSubscription(result.data);
        WlState.markRefreshError("Workflow Sidecar 事件流尚未重连", true);
        scheduleSnapshotRetry();
        return;
      }
      clearSnapshotRetry();
      startLiveSubscription(result.data);
      WlA11y.announce(result.mode === "LIVE" ? "已加载实时投影数据" : "已加载只读投影数据");
    } catch (err) {
      WlState.markRefreshError(err.message, true);
      if (WlState.get().lastGood) {
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