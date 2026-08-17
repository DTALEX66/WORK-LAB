/* WORK-LAB Observer - Command Center 2.0 Composer (WL-OBS-UI-DSH-20260816).
   Single unified information architecture:
   01 Global Command / 02 Projects / 03 Activity / 04 Telemetry /
   05 Delivery / 06 Governance + Data Trust.
   TRUTH-FIRST: every number must have a canonical source;
   UNKNOWN/null never become decorative KPIs. */
"use strict";

const WlFusionV3 = (function () {
  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function integer(value) {
    if (value === null || value === undefined || value === "") return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }
  function fmtShort(n) {
    if (n == null || !Number.isFinite(n)) return "-";
    return n >= 1000000 ? (n / 1000000).toFixed(1) + "M"
      : n >= 1000 ? (n / 1000).toFixed(0) + "K"
      : String(n);
  }

  /* Unified status meta (single source of truth for status colors). */
  function statusMeta(state) {
    const s = String(state || "UNKNOWN").toUpperCase();
    if (s === "LIVE" || s === "RUNNING" || s === "ACTIVE" || s === "EXECUTING" || s === "PASS" || s === "PASSING") return { key: "success", label: s === "LIVE" ? "LIVE" : s === "PASS" || s === "PASSING" ? "PASS" : "运行中", cls: "ok" };
    if (s.includes("BLOCK") || s === "FAILED" || s === "FAIL" || s === "CRITICAL") return { key: "critical", label: s === "FAILED" || s === "FAIL" ? "FAILED" : "阻塞", cls: "bad" };
    if (s === "WARNING" || s === "WAIT" || s === "WAITING" || s === "QUEUED" || s === "STALE") return { key: "warning", label: s === "WAIT" || s === "WAITING" ? "等待" : s === "STALE" ? "STALE" : s === "QUEUED" ? "QUEUED" : "警告", cls: "warn" };
    if (s === "REGISTERED" || s === "IDLE" || s === "STOPPED" || s === "OFFLINE") return { key: "muted", label: s === "OFFLINE" ? "OFFLINE" : s === "IDLE" ? "空闲" : "已注册", cls: "muted" };
    return { key: "unknown", label: s === "UNKNOWN" ? "UNKNOWN" : esc(s.toLowerCase()), cls: "muted" };
  }

  function renderGlobalCommand(d) {
    const transport = d.transport || {};
    const state = statusMeta(transport.transportState || "UNKNOWN");
    const projects = Array.isArray(d.projects) ? d.projects : [];
    const active = projects.filter((p) => {
      const s = String(p.activityState || "").toUpperCase();
      return s.includes("RUN") || s.includes("ACT") || s === "EXECUTING";
    }).length;
    const blocked = projects.filter((p) => String(p.activityState || "").toUpperCase().includes("BLOCK")).length;
    const coverage = d.coverage || {};
    const covPct = integer(coverage.denominator) > 0 && integer(coverage.numerator) != null ? Math.round((coverage.numerator / coverage.denominator) * 100) : null;
    const kpis = [
      { label: "项目", value: String(projects.length) },
      { label: "运行中", value: String(active), cls: active ? "ok" : "muted" },
      { label: "阻塞", value: String(blocked), cls: blocked ? "bad" : "muted" },
      { label: "覆盖", value: covPct === null ? "-" : covPct + "%", cls: covPct !== null && covPct >= 80 ? "ok" : "muted" },
    ];
    const tokUsage = (d.tokenSummary || {}).totalTokens;
    if (integer(tokUsage) != null) kpis.push({ label: "Token", value: fmtShort(integer(tokUsage)), cls: "primary" });
    return '<section class="wl-cmd-global" aria-label="全局状态">' +
      '<div class="wl-cmd-badge"><span class="wl-cmd-dot ' + state.cls + '"></span><b class="' + state.cls + '">' + state.label + '</b><em>READ ONLY</em></div>' +
      '<div class="wl-cmd-kpis">' + kpis.map((k) => '<div class="wl-cmd-kpi"><span>' + esc(k.label) + '</span><b class="' + (k.cls || "") + '">' + esc(k.value) + '</b></div>').join("") + '</div>' +
      '</section>';
  }

  function renderProjectGrid(d) {
    const projects = Array.isArray(d.projects) ? d.projects : [];
    if (!projects.length) return '<section class="wl-proj-section"><header class="wl-sec-head"><h2>项目</h2></header><div class="wl-empty">尚无已批准项目</div></section>';
    const cards = projects.map((p) => {
      const git = p.git || {};
      const st = statusMeta(p.activityState);
      const dirty = integer(git.dirtyCount);
      const dirtyTxt = dirty === 0 ? "Clean" : dirty != null ? dirty + " changes" : "—";
      const dirtyCls = dirty === 0 ? "ok" : dirty != null ? "warn" : "muted";
      const platform = p.agentPlatform ? esc(String(p.agentPlatform).toUpperCase()) : "—";
      const activeExec = integer(p.activeExecutionCount);
      const attention = p.attentionState ? statusMeta(p.attentionState) : null;
      return '<article class="wl-proj-card">' +
        '<header class="wl-proj-head"><div class="wl-proj-title"><span class="wl-proj-dot ' + st.cls + '"></span><b>' + esc(p.displayName || p.projectId) + '</b></div><span class="wl-proj-status ' + st.cls + '">' + st.label + '</span></header>' +
        '<div class="wl-proj-sub">' + esc(p.projectId || "") + '</div>' +
        '<div class="wl-proj-facts">' +
          '<div><span>Agent</span><b class="wl-proj-platform">' + platform + '</b></div>' +
          '<div><span>分支</span><b class="mono">' + esc(git.branch || "—") + '</b></div>' +
          '<div><span>HEAD</span><b class="mono">' + (git.localSha ? esc(String(git.localSha).slice(0, 7)) : "—") + '</b></div>' +
        '</div>' +
        '<div class="wl-proj-facts">' +
          '<div><span>工作树</span><b class="' + dirtyCls + '">' + esc(dirtyTxt) + '</b></div>' +
          '<div><span>执行</span><b>' + (activeExec != null ? esc(activeExec) : "—") + '</b></div>' +
          (attention ? '<div><span>注意</span><b class="' + attention.cls + '">' + attention.label + '</b></div>' : "") +
        '</div>' +
        (git.observedAt ? '<div class="wl-proj-evidence"><span>证据</span><time class="mono">' + esc(String(git.observedAt).slice(0, 19)) + '</time></div>' : "") +
      '</article>';
    }).join("");
    return '<section class="wl-proj-section" id="projects"><header class="wl-sec-head"><h2>项目</h2><span>' + projects.length + ' 个</span></header><div class="wl-proj-grid">' + cards + '</div></section>';
  }

  function renderActivity(d) {
    const executions = Array.isArray(d.executions) ? d.executions : [];
    if (!executions.length) return "";
    const rows = executions.slice(0, 8).map((e) => {
      const st = statusMeta(e.state);
      const proj = e.anchorProjectId || e.projectId || "—";
      return '<div class="wl-act-row"><span class="wl-proj-dot ' + st.cls + '"></span><b>' + esc(proj) + '</b><span class="wl-act-task">' + esc(e.taskTitle || e.title || "") + '</span><span class="wl-act-state ' + st.cls + '">' + st.label + '</span></div>';
    }).join("");
    return '<section class="wl-act-section" id="activity"><header class="wl-sec-head"><h2>Agent 活动</h2><span>' + executions.length + ' 个执行</span></header><div class="wl-act-list">' + rows + '</div></section>';
  }

  /* Agent Fleet (报告 Module09): 按 Agent 聚合的执行实例（runtime/status/项目）。 */
  function renderAgentFleet(d) {
    const execs = Array.isArray(d.executions) ? d.executions : [];
    if (!execs.length) return "";
    const byAgent = {};
    execs.forEach(function (e) {
      const agent = e.agent || "unknown";
      if (!byAgent[agent]) byAgent[agent] = { agent: agent, runs: 0, active: 0, projects: {} };
      byAgent[agent].runs += 1;
      const st = String(e.state || "").toUpperCase();
      if (st === "RUNNING" || st === "ACTIVE" || st === "EXECUTING") byAgent[agent].active += 1;
      const proj = e.anchorProjectId || e.projectId || "—";
      byAgent[agent].projects[proj] = (byAgent[agent].projects[proj] || 0) + 1;
    });
    const rows = Object.keys(byAgent).map(function (k) {
      const a = byAgent[k];
      const active = a.active > 0;
      const projects = Object.keys(a.projects).map(function (p) { return p + "×" + a.projects[p]; }).join(" · ");
      return '<div class="wl-act-row"><span class="wl-proj-dot ' + (active ? "ok" : "muted") + '"></span>' +
        '<b>' + esc(a.agent) + '</b>' +
        '<span class="wl-act-task">' + esc(projects || "—") + '</span>' +
        '<span class="wl-act-state ' + (active ? "ok" : "muted") + '">' + (active ? "活跃 " + a.active : a.runs + " 次") + '</span></div>';
    }).join("");
    return '<section class="wl-act-section" id="fleet"><header class="wl-sec-head"><h2>Agent Fleet</h2><span>' + Object.keys(byAgent).length + ' 个 Agent（Runtime Control）</span></header><div class="wl-act-list">' + rows + '</div></section>';
  }

  /* Execution Timeline (报告 Module09): 时间线视图（执行实例生命周期 + 项目注册）。 */
  function renderTimeline(d) {
    const execs = Array.isArray(d.executions) ? d.executions : [];
    const projects = Array.isArray(d.projects) ? d.projects : [];
    const events = [];
    projects.forEach(function (p) {
      events.push({ at: p.registeredAt || null, cls: "muted", text: esc(p.displayName || p.projectId) + " 注册" });
    });
    execs.forEach(function (e) {
      const st = statusMeta(e.state);
      events.push({ at: e.startedAt || e.lastHeartbeatAt || null, cls: st.cls, text: esc(e.agent || "agent") + " · " + esc(e.anchorProjectId || "—") + " → " + st.label });
    });
    events.sort(function (a, b) { return (a.at || "").localeCompare(b.at || ""); });
    const items = events.slice(-10).reverse().map(function (e) {
      const time = e.at ? String(e.at).slice(5, 19).replace("T", " ") : "—";
      return '<div class="wl-tl-row"><span class="wl-tl-time mono">' + esc(time) + '</span><span class="wl-tl-dot ' + e.cls + '"></span><span class="wl-tl-text">' + e.text + '</span></div>';
    }).join("");
    return '<section class="wl-act-section" id="timeline"><header class="wl-sec-head"><h2>Execution Timeline</h2><span>最近事件</span></header><div class="wl-tl-list">' + (items || '<span class="wl-empty-inline">无事件</span>') + '</div></section>';
  }

  function renderTelemetry(d) {
    const t = d.tokenSummary || {};
    const total = integer(t.totalTokens);
    if (total == null) return '<section class="wl-tel-section" id="telemetry"><header class="wl-sec-head"><h2>AI Telemetry</h2></header><div class="wl-empty-state"><b>No token samples yet</b><span>Waiting for a collector-reported usage sample.</span><em>SOURCE · Explicit usage ledger</em></div></section>';
    const hit = integer(t.cacheHitTokens);
    const miss = integer(t.cacheMissTokens);
    const hitRate = hit != null && miss != null && (hit + miss) > 0 ? Math.round((hit / (hit + miss)) * 100) : null;
    const cells = [
      { label: "Token", value: fmtShort(total), big: true },
      { label: "输入", value: fmtShort(integer(t.inputTokens)) },
      { label: "输出", value: fmtShort(integer(t.outputTokens)) },
      { label: "缓存命中", value: fmtShort(hit) },
      { label: "未命中", value: fmtShort(miss) },
    ];
    if (hitRate != null) cells.push({ label: "命中率", value: hitRate + "%", cls: "ok" });
    return '<section class="wl-tel-section" id="telemetry"><header class="wl-sec-head"><h2>AI Telemetry</h2><span>真实用量</span></header><div class="wl-tel-cells">' + cells.map((c) => '<div class="wl-tel-cell ' + (c.big ? "wl-tel-big" : "") + '"><span>' + esc(c.label) + '</span><b class="' + (c.cls || "") + '">' + esc(c.value) + '</b></div>').join("") + '</div></section>';
  }

  function renderDelivery(d) {
    const projects = Array.isArray(d.projects) ? d.projects : [];
    if (!projects.length) return "";
    const rows = projects.map((p) => {
      const git = p.git || {};
      const dirty = integer(git.dirtyCount);
      const ci = (p.ci && p.ci.length) ? statusMeta(p.ci[0].conclusion || p.ci[0].status) : null;
      return '<div class="wl-del-row">' +
        '<b>' + esc(p.displayName || p.projectId) + '</b>' +
        '<code class="mono">' + esc(git.branch || "—") + '</code>' +
        '<code class="mono">' + (git.localSha ? esc(String(git.localSha).slice(0, 7)) : "—") + '</code>' +
        '<span class="wl-del-ci ' + (ci ? ci.cls : "muted") + '">' + (ci ? ci.label : "—") + '</span>' +
        '<span class="wl-del-dirty ' + (dirty === 0 ? "ok" : dirty == null ? "muted" : "warn") + '">' + (dirty === 0 ? "Clean" : dirty == null ? "—" : dirty + " 变更") + '</span>' +
      '</div>';
    }).join("");
    return '<section class="wl-del-section" id="delivery"><header class="wl-sec-head"><h2>Delivery / CI</h2></header><div class="wl-del-table">' + rows + '</div></section>';
  }

  function renderGovernance(d) {
    const g = (d.governance || {}).families || {};
    const entries = Object.entries(g);
    const chips = entries.map(([k, v]) => {
      const st = statusMeta((v && v.state) || "unknown");
      return '<span class="wl-gov-chip ' + st.cls + '">' + esc(k) + ' · ' + esc(st.label.toLowerCase()) + '</span>';
    }).join("");
    return '<section class="wl-gov-section" id="governance"><header class="wl-sec-head"><h2>治理健康</h2></header><div class="wl-gov-chips">' + (chips || '<span class="wl-empty-inline">无治理基线</span>') + '</div></section>';
  }

  function renderDataTrust(d) {
    const transport = d.transport || {};
    const st = statusMeta(transport.transportState || "UNKNOWN");
    const coverage = d.coverage || {};
    const numerator = integer(coverage.numerator);
    const denominator = integer(coverage.denominator);
    const cov = denominator > 0 && numerator != null ? (numerator + " / " + denominator) : "—";
    const quality = d.quality || {};
    const facts = [
      { label: "Transport", value: st.label, cls: st.cls },
      { label: "Source coverage", value: cov },
      { label: "Freshness", value: d.sourceWatermark ? String(d.sourceWatermark).slice(0, 19) : "—" },
      { label: "Revision", value: integer(d.revision) != null ? "#" + integer(d.revision) : "—" },
      { label: "Malformed", value: quality.malformed == null ? "—" : String(quality.malformed) },
      { label: "Dropped", value: quality.dropped == null ? "—" : String(quality.dropped) },
    ];
    return '<section class="wl-trust-section" id="trust"><header class="wl-sec-head"><h2>Data Trust</h2><span>这些状态有多可信</span></header><div class="wl-trust-grid">' + facts.map((f) => '<div><span>' + esc(f.label) + '</span><b class="' + (f.cls || "") + '">' + esc(f.value) + '</b></div>').join("") + '</div></section>';
  }

  function renderSidebar(d) {
    const nav = [
      { id: "projects", label: "项目", icon: "i-projects" },
      { id: "activity", label: "活动", icon: "i-ci" },
      { id: "telemetry", label: "遥测", icon: "i-usage" },
      { id: "delivery", label: "交付", icon: "i-branch" },
      { id: "governance", label: "治理", icon: "i-layer" },
      { id: "trust", label: "信任", icon: "i-sha" },
    ];
    const links = nav.map((n) => '<a href="#' + n.id + '" class="wl-nav-link" title="' + n.label + '"><svg class="wl-nav-svg" aria-hidden="true"><use href="#' + n.icon + '"></use></svg><span>' + esc(n.label) + '</span></a>').join("");
    return '<nav class="wl-sidebar" aria-label="主导航"><div class="wl-sidebar-brand"><svg class="wl-brand-svg" aria-hidden="true"><use href="#i-sha"></use></svg></div><div class="wl-nav-list">' + links + '</div><div class="wl-sidebar-foot"><span class="wl-ro-badge">RO</span></div></nav>';
  }

  function renderTopbar(d) {
    const st = statusMeta((d.transport || {}).transportState || "UNKNOWN");
    return '<header class="wl-topbar"><div class="wl-topbar-title"><b>WORK-LAB</b><span>Observer</span><em>Command Center</em></div><div class="wl-topbar-right"><span class="wl-topbar-state ' + st.cls + '">' + st.label + '</span><span class="wl-topbar-ro">READ ONLY</span></div></header>';
  }

  function renderObservability() {
    // Native metrics panel (filled by app.js from Prometheus API) + tool links.
    // No iframe nesting: deep tools (Grafana/Phoenix/Loki) open in their own
    // window; the OB surface renders Prometheus facts natively.
    const links = [
      { label: "Grafana 总台", url: "http://127.0.0.1:3000" },
      { label: "Phoenix Trace", url: "http://127.0.0.1:6006" },
      { label: "Loki 日志", url: "http://127.0.0.1:3000/explore?schemaVersion=1&panes=%7B%22default%22%3A%7B%22datasource%22%3A%7B%22type%22%3A%22loki%22%2C%22uid%22%3A%22P8E80F9AEF21F6940%22%7D%2C%22queries%22%3A%5B%7B%22refId%22%3A%22A%22%2C%22expr%22%3A%22%7B%7D%22%2C%22queryType%22%3A%22range%22%7D%5D%2C%22range%22%3A%7B%22from%22%3A%22now-1h%22%2C%22to%22%3A%22now%22%7D%7D%7D" }
    ];
    const chips = links.map((l) => '<a class="wl-gov-chip" href="' + l.url + '" target="_blank" rel="noopener">' + esc(l.label) + '</a>').join("");
    return '<section class="wl-gov-section" id="observability"><header class="wl-sec-head"><h2>Observability</h2><span>实时指标（Prometheus 原生渲染）</span></header><div id="wl-obskpis" class="wl-obskpis"><span class="wl-empty">加载中…</span></div><div class="wl-gov-chips" style="margin-top:10px">' + chips + '</div></section>';
  }

  function renderShell(d) {
    return '<div class="wl-cc-shell">' + renderSidebar(d) + '<main class="wl-cc-main">' +
      renderTopbar(d) + renderGlobalCommand(d) + renderProjectGrid(d) + renderActivity(d) +
      '<div class="wl-cc-cols">' + renderAgentFleet(d) + renderTimeline(d) + '</div>' +
      '<div class="wl-cc-cols">' + renderTelemetry(d) + renderDataTrust(d) + '</div>' +
      renderDelivery(d) + renderGovernance(d) + renderObservability() +
      '</main></div>';
  }


  /* Compact: a real tiny monitoring window (not a shrunk full view). */
  function renderCompact(d) {
    const st = statusMeta((d.transport || {}).transportState || "UNKNOWN");
    const projects = Array.isArray(d.projects) ? d.projects : [];
    const active = projects.filter((p) => {
      const state = String(p.activityState || "").toUpperCase();
      return state.includes("RUN") || state.includes("ACT") || state === "EXECUTING";
    }).length;
    const blocked = projects.filter((p) => String(p.activityState || "").toUpperCase().includes("BLOCK")).length;
    const tokVal = (d.tokenSummary || {}).totalTokens;
    const coverage = d.coverage || {};
    const covPct = integer(coverage.denominator) > 0 && integer(coverage.numerator) != null ? Math.round((coverage.numerator / coverage.denominator) * 100) : null;
    const rows = projects.map((p) => {
      const ps = statusMeta(p.activityState);
      const git = p.git || {};
      return '<div class="wl-cp-row"><span class="wl-proj-dot ' + ps.cls + '"></span><b>' + esc(p.displayName || p.projectId) + '</b><code class="mono">' + esc(git.branch || "-") + '</code><span class="wl-cp-state ' + ps.cls + '">' + ps.label + '</span></div>';
    }).join("");
    return '<div class="wl-cp" role="status" aria-live="polite">' +
      '<div class="wl-cp-head"><b>WORK-LAB</b><span class="wl-cp-live ' + st.cls + '">' + st.label + '</span></div>' +
      '<div class="wl-cp-sum"><span>' + projects.length + ' 项目</span><span>' + active + ' 活跃</span><span class="' + (blocked ? "bad" : "muted") + '">' + blocked + " 阻塞" + '</span></div>' +
      '<div class="wl-cp-list">' + (rows || '<span class="wl-empty">无项目</span>') + '</div>' +
      '<div class="wl-cp-foot">' +
        (integer(tokVal) != null ? '<span class="mono">' + fmtShort(integer(tokVal)) + ' tok</span>' : '') +
        '<span>覆盖 ' + (covPct === null ? "-" : covPct + "%") + '</span>' +
        (d.sourceWatermark ? '<span class="mono">' + esc(String(d.sourceWatermark).slice(11, 19)) + '</span>' : '') +
      '</div></div>';
  }

  function render(d) { return renderShell(d); }

  return { render, renderCompact, esc, fmtShort, statusMeta, renderShell, renderSidebar, renderTopbar, renderGlobalCommand, renderProjectGrid, renderActivity, renderAgentFleet, renderTimeline, renderTelemetry, renderDelivery, renderGovernance, renderDataTrust, renderObservability };
})();

if (typeof module !== "undefined" && module.exports) {
  module.exports = { WlFusionV3 };
}
