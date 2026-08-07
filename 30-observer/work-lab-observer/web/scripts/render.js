/* WORK-LAB Observer — render.js
   Pure render functions: produce HTML strings from a projection for the
   full and compact views. Components receive data; they never fetch.
   All status is conveyed by icon + text + color (never color alone). */

const WlRender = (function () {
  "use strict";

  const F = WlFormat;

  /* Same-document icon reference (sprite inlined in index.html; works over
     file:// and http:// without CORS issues on the sprite itself). */
  function icon(name) {
    return `<svg class="wl-icon" aria-hidden="true" focusable="false"><use href="#i-${name}"/></svg>`;
  }

  /* Map a projection state string to chip class + icon + zh label. */
  function statusMeta(state) {
    switch (state) {
      case "blocked": return { cls: "blocked", ic: "blocked", text: "阻塞" };
      case "waiting_external": return { cls: "waiting", ic: "waiting", text: "等待外部" };
      case "queued": return { cls: "waiting", ic: "waiting", text: "排队" };
      case "running": return { cls: "running", ic: "running", text: "运行" };
      case "failed": return { cls: "failed", ic: "failed", text: "失败" };
      case "completed": return { cls: "completed", ic: "completed", text: "完成" };
      case "idle": return { cls: "idle", ic: "clock", text: "空闲" };
      default: return { cls: "unknown", ic: "unknown", text: "未知" };
    }
  }

  function chipFor(state) {
    const m = statusMeta(state);
    return `<span class="wl-chip ${m.cls}">${icon(m.ic)}${m.text}</span>`;
  }

  function qdot(dataQuality) {
    const cls = String(dataQuality || "unknown").toLowerCase();
    return `<span class="wl-quality"><span class="wl-qdot ${cls}"></span>${F.escapeHtml(dataQuality || "unknown")}</span>`;
  }

  /* ===================== FULL VIEW ===================== */

  function renderKpi(d) {
    const s = d.summary || {};
    const fresh = d.freshness || {};
    // Derive task counts from the actual project list so KPI never disagrees
    // with the project table (no phantom tasks). summary.tasks may be stale/overcount.
    const projects = d.projects || [];
    const stCount = { running: 0, waiting: 0, blocked: 0, completed: 0, idle: 0, failed: 0, queued: 0, unknown: 0 };
    projects.forEach((p) => {
      const key = (stCount[p.state] !== undefined) ? p.state : "unknown";
      stCount[key] += 1;
    });
    const running = stCount.running + stCount.queued;
    const waiting = stCount.waiting;
    const blocked = stCount.blocked;
    const active = (s.activeProjects != null) ? s.activeProjects : (running + waiting + blocked);
    const freshnessText = fresh.state === "fresh" ? "新鲜" : (fresh.state === "delayed" ? "延迟" : (fresh.state === "stale" ? "陈旧" : "未知"));
    const freshCls = fresh.state === "fresh" ? "fresh" : (fresh.state === "stale" ? "stale" : "delayed");

    const cards = [
      { label: "活跃项目", value: active, note: "最近有活动", ic: "projects" },
      { label: "运行任务", value: running, note: "进行中", ic: "running" },
      { label: "等待", value: waiting, note: "等待外部/排队", ic: "waiting" },
      { label: "阻塞", value: blocked, note: "最高优先级 blocker", ic: "blocked" },
      { label: "数据新鲜度", value: freshnessText, note: "age " + (F.freshnessAge(fresh.ageSeconds) !== "—" ? F.freshnessAge(fresh.ageSeconds) : "未知"), ic: "fresh", cls: freshCls, small: true },
    ];

    let out = '<div class="wl-grid wl-kpi">';
    cards.forEach((c) => {
      const valCls = c.small ? " style=\"font-size:20px\"" : "";
      out += `<div class="wl-card wl-metric"><div class="wl-metric-label">${icon(c.ic)}${c.label}</div>` +
        `<div class="wl-metric-value${c.cls ? " wl-chip " + c.cls : ""}"${valCls}>${F.escapeHtml(String(c.value))}</div>` +
        `<div class="wl-metric-note">${F.escapeHtml(c.note)}</div></div>`;
    });
    out += "</div>";
    return out;
  }

  /* Project row sort: blocked → waiting_external → failed → running → completed/idle → unknown */
  const SORT_ORDER = { blocked: 0, waiting_external: 1, queued: 1, failed: 2, running: 3, completed: 4, idle: 4, unknown: 5 };

  function renderProjectTable(d) {
    const projects = (d.projects || []).slice();
    projects.sort((a, b) => {
      const ao = SORT_ORDER[a.state] !== undefined ? SORT_ORDER[a.state] : 5;
      const bo = SORT_ORDER[b.state] !== undefined ? SORT_ORDER[b.state] : 5;
      return ao - bo;
    });

    if (!projects.length) {
      return `<div class="wl-state-note">${icon("info")}尚无已验证项目事件。</div>`;
    }

    // Converged columns: main project + status only. Drop branch/task/stage/duration detail.
    const head = `
      <tr><th>项目</th><th>Agent</th><th>状态</th><th>Blocker / CI</th></tr>`;

    const rows = projects.map((p) => {
      const ciState = p.ciState ? `<span class="wl-chip ${ciCls(p.ciState)}">${F.escapeHtml(String(p.ciState))}</span>` : "—";
      return `<tr>
        <td><div class="wl-project-cell"><span class="wl-project-name">${F.escapeHtml(p.displayName || p.projectId)}</span></div></td>
        <td>${F.escapeHtml(p.agentPlatform || "—")}</td>
        <td>${chipFor(p.state)}</td>
        <td>${ciState}</td>
      </tr>`;
    }).join("");

    return `<div class="wl-table-wrap"><table class="wl-table"><thead>${head}</thead><tbody>${rows}</tbody></table></div>`;
  }

  function ciCls(s) {
    const v = String(s || "").toUpperCase();
    if (v.indexOf("FAIL") !== -1) return "failed";
    if (v.indexOf("BLOCK") !== -1) return "blocked";
    if (v.indexOf("PASS") !== -1) return "completed";
    if (v.indexOf("RUN") !== -1) return "running";
    if (v.indexOf("QUEUED") !== -1) return "waiting";
    return "unknown";
  }

  function renderBlocker(d) {
    const b = d.primaryBlocker;
    if (!b) return `<div class="wl-state-note">${icon("check")}当前无阻塞。</div>`;
    const q = b.quality || {};
    return `<div class="wl-blocker">
      <div class="wl-blocker-head">${icon("blocked")}<div class="wl-blocker-title">${F.escapeHtml(b.title)}</div></div>
      <div class="wl-kv">
        <span class="k">项目</span><span class="v wl-strong">${F.escapeHtml(b.projectId)}</span>
        <span class="k">状态</span><span class="v">${chipFor("blocked")} ${F.escapeHtml(String(b.state))}</span>
        <span class="k">持续时间</span><span class="v">${F.duration(b.durationSeconds)}</span>
        <span class="k">最新观察</span><span class="v">${F.relativeTime(b.lastObservedAt)}（${F.absoluteTime(b.lastObservedAt)}）</span>
        <span class="k">来源质量</span><span class="v">${qdot(q.dataQuality)} · ${F.escapeHtml(q.evidenceCompleteness || "unknown")} · ${F.escapeHtml(q.freshness || "unknown")}</span>
        <span class="k">影响范围</span><span class="v">${F.escapeHtml(b.impact || "—")}</span>
        <span class="k">Next</span><span class="v">${F.escapeHtml(b.nextCondition || "—")}</span>
      </div>
      <div class="wl-impact">${icon("info")} 证据卡 · 只读观察，不提供重试操作。</div>
    </div>`;
  }

  function renderUsage(d) {
    const u = d.usage || {};
    const cost = u.cost || {};
    const sub = u.subscriptionUsage;
    const costLabel = cost.status === "estimated" ? "API 估算 / " + (cost.currency || "USD") :
      (cost.status === "actual" ? "API 实际 / " + (cost.currency || "USD") :
      (cost.status === "subscription" ? "订阅" : "未知计费"));
    const cells = [
      { label: "输入 Token", value: F.tokensCompact(u.inputTokens), full: F.tokens(u.inputTokens), ic: "token" },
      { label: "输出 Token", value: F.tokensCompact(u.outputTokens), full: F.tokens(u.outputTokens), ic: "token" },
      { label: "Reasoning Token", value: u.reasoningTokens == null ? "未知" : F.tokensCompact(u.reasoningTokens), full: u.reasoningTokens == null ? "unknown" : F.tokens(u.reasoningTokens), ic: "token" },
      { label: "缓存读取", value: F.tokensCompact(u.cacheReadTokens), full: F.tokens(u.cacheReadTokens), ic: "cache" },
      { label: "缓存写入", value: u.cacheWriteTokens == null ? "未知" : F.tokensCompact(u.cacheWriteTokens), full: u.cacheWriteTokens == null ? "unknown" : F.tokens(u.cacheWriteTokens), ic: "cache" },
      { label: costLabel, value: F.costAmount(cost), full: "估算，非实际账单", ic: "coin" },
      { label: "订阅未计量", value: sub === "not-metered" ? "未计量" : F.escapeHtml(String(sub || "未知")), full: sub === "not-metered" ? "订阅未计量" : "—", ic: "sub" },
      { label: "Unknown", value: "—", full: "无独立 unknown 字段", ic: "unknown" },
    ];
    let out = '<div class="wl-usage-grid">';
    cells.forEach((c) => {
      out += `<div class="wl-usage-cell"><div class="wl-u-label">${icon(c.ic)}${c.label}</div>` +
        `<div class="wl-u-value">${F.escapeHtml(String(c.value))}</div><div class="wl-u-sub">${F.escapeHtml(String(c.full))}</div></div>`;
    });
    out += "</div>";
    return out;
  }

  function renderTrend(d) {
    const u = d.usage || {};
    const win = d.window || {};
    const series = (u.series || []).slice(0, 5).map((s) => {
      const name = (d.projects || []).find((p) => p.projectId === s.projectId);
      return {
        label: name ? name.displayName : s.projectId,
        points: (s.points || []).map((p) => ({ x: new Date(p.bucket).getTime(), y: p.inputTokens || 0 })),
      };
    });
    const buckets = (u.series && u.series[0] && u.series[0].points || []).map((p) => {
      const t = new Date(p.bucket);
      return t.getMonth() + 1 + "/" + t.getDate();
    });
    if (!series.length) {
      return `<div class="wl-state-note">${icon("info")}暂无趋势数据。</div>`;
    }
    const chart = WlCharts.lineChart(series, {
      area: true,
      buckets,
      ariaLabel: "跨项目 7 日输入 Token 趋势",
      ariaDesc: "最多 5 条项目序列的输入 Token 折线，单位为 tokens。",
      window: `${win.from || ""} → ${win.to || ""}`,
      unit: "tokens（输入）",
      timezone: win.timezone || "未知",
      truncation: "仅最近 7 个桶；超过 5 序列已截断",
    });
    return chart.svg + `<p class="sr-only">${F.escapeHtml(chart.summary)}</p>`;
  }

  function renderCi(d) {
    const ci = d.ci || {};
    const items = [
      { k: "exact-SHA 绑定", v: F.intOrDash(ci.exactShaBound) + " / " + F.intOrDash(ci.exactShaRequired), ic: "sha" },
      { k: "Queued no job", v: F.intOrDash(ci.queuedNoJob), ic: "waiting" },
      { k: "Running", v: F.intOrDash(ci.running), ic: "running" },
      { k: "Passed", v: F.intOrDash(ci.passed), ic: "completed" },
      { k: "Failed", v: F.intOrDash(ci.failed), ic: "failed" },
      { k: "Unknown", v: F.intOrDash(ci.unknown), ic: "unknown" },
    ];
    let out = '<div class="wl-ci-grid">';
    items.forEach((it) => {
      out += `<div class="wl-ci-item"><div class="wl-ci-k">${it.k}</div><div class="wl-ci-v">${icon(it.ic)}${it.v}</div></div>`;
    });
    out += "</div>";

    // per-project branch/sha/gate/evidence freshness
    const rows = (d.projects || []).map((p) => `
      <tr><td class="wl-strong">${F.escapeHtml(p.displayName || p.projectId)}</td>
      <td>${F.escapeHtml(p.branch || "—")}</td>
      <td class="mono break-word">${F.shortSha(p.headSha)}</td>
      <td>${p.ciState ? `<span class="wl-chip ${ciCls(p.ciState)}">${F.escapeHtml(String(p.ciState))}</span>` : "—"}</td>
      <td>${F.relativeTime(p.lastEventAt)}</td></tr>`).join("");
    out += `<div class="wl-table-wrap"><table class="wl-table"><thead><tr><th>项目</th><th>Branch</th><th>HEAD / SHA</th><th>门禁</th><th>证据新鲜度</th></tr></thead><tbody>${rows}</tbody></table></div>`;
    return out;
  }

  function renderGovernance(d) {
    const g = d.governance || {};
    const dims = [
      { label: "Rules", data: g.rules },
      { label: "Skills", data: g.skills },
      { label: "Adapters", data: g.adapters },
      { label: "Memory / Context", data: g.memoryContext },
    ];
    const rows = dims.map((dim) => {
      const v = dim.data || {};
      return `<tr><td>${F.escapeHtml(dim.label)}</td>
        <td class="wl-gov-num">${F.intOrDash(v.current)}</td>
        <td class="wl-gov-num wl-gov-drift">${F.intOrDash(v.drift)}</td>
        <td class="wl-gov-num wl-gov-quar">${F.intOrDash(v.quarantined)}</td>
        <td class="wl-gov-num wl-gov-conf">${F.intOrDash(v.conflicts)}</td>
        <td class="wl-gov-num wl-gov-stale">${F.intOrDash(v.stale)}</td></tr>`;
    }).join("");
    return `<table class="wl-gov"><thead><tr><th>维度</th><th>Current</th><th>Drift</th><th>Quarantined</th><th>Conflicts</th><th>Stale</th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  function renderQuality(d) {
    const q = d.quality || {};
    const cov = q.sourceCoverage || {};
    const pct = cov.denominator ? Math.round((cov.numerator / cov.denominator) * 100) : 0;
    const items = [
      { k: "Evidence", v: F.escapeHtml(q.evidenceCompleteness || "unknown") },
      { k: "Freshness", v: F.escapeHtml(q.freshness || "unknown") },
      { k: "Unknown", v: F.intOrDash(q.unknown) },
      { k: "Malformed", v: F.intOrDash(q.malformed) },
      { k: "Dropped", v: F.intOrDash(q.dropped) },
      { k: "Duplicate", v: F.intOrDash(q.duplicate) },
      { k: "Projection lag", v: q.projectionLagMs == null ? "—" : F.intOrDash(q.projectionLagMs) + " ms" },
      { k: "Last good", v: F.relativeTime(q.lastGoodAt) },
    ];
    let out = `<div class="wl-dq">
      <div class="wl-dq-coverage"><div class="wl-dq-k">Source coverage · ${F.escapeHtml(cov.scope || "")}</div>
        <div class="wl-dq-v">${F.intOrDash(cov.numerator)} / ${F.intOrDash(cov.denominator)} <span style="font-size:12px;color:var(--wl-text-muted)">(${pct}%)</span></div>
        <div class="wl-dq-bar"><span style="width:${pct}%"></span></div></div>`;
    items.forEach((it) => {
      out += `<div class="wl-dq-item"><div class="wl-dq-k">${it.k}</div><div class="wl-dq-v">${it.v}</div></div>`;
    });
    out += "</div>";
    return out;
  }

  /* Compact health summary — folds CI / governance / quality into one compact strip
     so the full view stays component-like and not crowded. */
  function renderHealthStrip(d) {
    const ci = d.ci || {};
    const g = d.governance || {};
    const q = d.quality || {};
    const cov = q.sourceCoverage || {};
    const pills = [];
    pills.push(`<div class="wl-health-item"><span class="wl-h-label">exact-SHA</span><span class="wl-h-value">${F.intOrDash(ci.exactShaBound)}/${F.intOrDash(ci.exactShaRequired)}</span></div>`);
    pills.push(`<div class="wl-health-item"><span class="wl-h-label">CI 排队无job</span><span class="wl-h-value">${F.intOrDash(ci.queuedNoJob)}</span></div>`);
    pills.push(`<div class="wl-health-item"><span class="wl-h-label">来源覆盖</span><span class="wl-h-value">${F.intOrDash(cov.numerator)}/${F.intOrDash(cov.denominator)}</span></div>`);
    pills.push(`<div class="wl-health-item"><span class="wl-h-label">治理漂移</span><span class="wl-h-value">${F.intOrDash((g.rules||{}).drift)}</span></div>`);
    const fresh = (q.freshness === "fresh") ? "新鲜" : (q.freshness === "stale" ? "陈旧" : (q.freshness || "未知"));
    pills.push(`<div class="wl-health-item"><span class="wl-h-label">新鲜度</span><span class="wl-h-value">${F.escapeHtml(fresh)}</span></div>`);
    pills.push(`<div class="wl-health-item"><span class="wl-h-label">未知项</span><span class="wl-h-value">${F.intOrDash(q.unknown)}</span></div>`);
    return `<div class="wl-health-strip">${pills.join("")}</div>`;
  }

  /* Full view sections — CONVERGED: only core blocks, component-like, roomy.
     CI/Governance/Quality are folded into a single compact "health" strip to
     avoid the crowded 8-card dashboard. */
  function fullSections(d) {
    return [
      { id: "overview", title: "总览", sub: "KPI", html: renderKpi(d), noCard: true },
      { id: "projects", title: "项目运行全景", sub: "Projects", html: renderProjectTable(d), full: true },
      { id: "blocker", title: "关键阻塞", sub: "Blocker", html: renderBlocker(d) },
      { id: "usage", title: "用量与趋势", sub: "Usage · Trend", html: renderUsage(d) + renderTrend(d), full: true },
      { id: "governance", title: "治理健康", sub: "Rules · Skills · Adapters · Memory", html: renderGovernance(d), full: true },
      { id: "health", title: "CI / 数据质量", sub: "CI · Quality", html: renderHealthStrip(d) + renderQuality(d), full: true },
    ];
  }

  function renderFull(d, now) {
    const sections = fullSections(d);
    const span = {
      overview: "wl-col-12", projects: "wl-col-9", blocker: "wl-col-3",
      usage: "wl-col-12", governance: "wl-col-12", health: "wl-col-12",
    };
    let out = "";
    sections.forEach((s) => {
      if (s.noCard) {
        out += `<section id="${s.id}" class="wl-col-12" aria-label="${F.escapeHtml(s.title)}">${s.html}</section>`;
        return;
      }
      const col = span[s.id] || "wl-col-12";
      out += `<section id="${s.id}" class="${col} wl-card"><h3>${icon("info")}${F.escapeHtml(s.title)}<span style="margin-left:auto;font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--wl-text-muted)">${F.escapeHtml(s.sub)}</span></h3>${s.html}</section>`;
    });
    return out;
  }

  /* ===================== COMPACT VIEW ===================== */

  function compactHeader(d) {
    const fresh = d.freshness || {};
    const freshText = fresh.state === "fresh" ? "新鲜" : (fresh.state === "delayed" ? "延迟" : (fresh.state === "stale" ? "陈旧" : "未知"));
    return `<div class="wl-compact-header wl-shell" data-tauri-drag-region>
      <span class="wl-mark">${icon("grid")}</span>
      <span class="wl-compact-title" data-tauri-drag-region>WORK-LAB</span>
      <span class="wl-badge wl-badge-ro">${icon("eye")}只读</span>
      <span class="wl-badge wl-badge-cross">${icon("projects")}跨项目</span>
      <span class="wl-badge wl-badge-fixture">${icon("info")}FIXTURE</span>
      <span class="wl-badge ${fresh.state === 'fresh' ? 'wl-badge-fresh' : 'wl-badge-delayed'}">${icon("fresh")}${F.escapeHtml(freshText)}</span>
    </div>`;
  }

  function compactGlobal(d) {
    const s = d.summary || {};
    const t = s.tasks || {};
    const cells = [
      { label: "登记项目", v: s.registeredProjects, ic: "projects" },
      { label: "运行", v: t.running, ic: "running" },
      { label: "等待", v: t.waiting, ic: "waiting" },
      { label: "阻塞", v: t.blocked, ic: "blocked" },
      { label: "完成", v: t.completed, ic: "completed" },
    ];
    let out = '<div class="wl-usage-grid">';
    cells.forEach((c) => {
      out += `<div class="wl-usage-cell"><div class="wl-u-label">${icon(c.ic)}${c.label}</div><div class="wl-u-value">${F.intOrDash(c.v)}</div></div>`;
    });
    out += "</div>";
    return out;
  }

  function compactActive(d) {
    const projects = (d.projects || []).slice().filter((p) => ["running", "blocked", "waiting_external", "queued"].includes(p.state));
    const sortIdx = (p) => SORT_ORDER[p.state] !== undefined ? SORT_ORDER[p.state] : 5;
    projects.sort((a, b) => sortIdx(a) - sortIdx(b));
    const shown = projects.slice(0, 2);
    const others = Math.max(0, projects.length - shown.length);
    let out = '<div class="wl-usage-grid">';
    shown.forEach((p) => {
      const m = statusMeta(p.state);
      out += `<div class="wl-usage-cell"><div class="wl-u-label">${icon(m.ic)}${m.text}</div>` +
        `<div class="wl-u-value" style="font-size:15px">${F.escapeHtml(p.displayName || p.projectId)}</div>` +
        `<div class="wl-u-sub">${F.escapeHtml(p.task || p.stage || "—")}</div></div>`;
    });
    out += "</div>";
    if (others > 0) {
      out += `<p class="wl-metric-note" style="margin-top:8px">另有 ${others} 个活动项目（只读展开或进入完整视图查看全部）。</p>`;
    }
    return out;
  }

  function compactUsage(d) {
    const u = d.usage || {};
    const cost = u.cost || {};
    const costLabel = cost.status === "estimated" ? "API 估算 / " + (cost.currency || "USD") : (cost.currency || "USD");
    const cells = [
      { label: "输入 Token", value: F.tokensCompact(u.inputTokens), sub: F.tokens(u.inputTokens), ic: "token" },
      { label: costLabel, value: F.costAmount(cost), sub: "估算，非实际账单", ic: "coin" },
      { label: "订阅未计量", value: u.subscriptionUsage === "not-metered" ? "未计量" : "—", sub: "not-metered", ic: "sub" },
      { label: "缓存读取", value: F.tokensCompact(u.cacheReadTokens), sub: F.tokens(u.cacheReadTokens), ic: "cache" },
    ];
    let out = '<div class="wl-usage-grid">';
    cells.forEach((c) => {
      out += `<div class="wl-usage-cell"><div class="wl-u-label">${icon(c.ic)}${c.label}</div>` +
        `<div class="wl-u-value">${F.escapeHtml(String(c.value))}</div><div class="wl-u-sub">${F.escapeHtml(String(c.sub))}</div></div>`;
    });
    out += "</div>";
    return out;
  }

  function compactEvidenceHealth(d) {
    const ci = d.ci || {};
    const gov = d.governance || {};
    const q = d.quality || {};
    const cov = q.sourceCoverage || {};
    const driftTotal = (Object.keys(gov).reduce((sum, k) => sum + ((gov[k] && gov[k].drift) || 0), 0));
    const items = [
      { label: "Exact-SHA", value: F.intOrDash(ci.exactShaBound) + " / " + F.intOrDash(ci.exactShaRequired), ic: "sha" },
      { label: "治理漂移", value: F.intOrDash(driftTotal), ic: "governance" },
      { label: "来源覆盖", value: F.intOrDash(cov.numerator) + " / " + F.intOrDash(cov.denominator), ic: "layer" },
      { label: "未知项", value: F.intOrDash(q.unknown), ic: "unknown" },
      { label: "新鲜度", value: F.escapeHtml(q.freshness || "unknown"), ic: "fresh" },
    ];
    let out = '<div class="wl-ci-grid">';
    items.forEach((it) => {
      out += `<div class="wl-ci-item"><div class="wl-ci-k">${it.label}</div><div class="wl-ci-v">${icon(it.ic)}${it.v}</div></div>`;
    });
    out += "</div>";
    return out;
  }

  function renderCompact(d, now) {
    const sections = [
      { title: "全局状态", sub: "Global", html: compactGlobal(d) },
      { title: "正在执行", sub: "Active", html: compactActive(d) },
      { title: "关键阻塞", sub: "Blocker", html: renderBlocker(d) },
      { title: "今日用量", sub: "Usage", html: compactUsage(d) },
      { title: "证据与健康", sub: "Evidence & Health", html: compactEvidenceHealth(d) },
    ];
    let out = compactHeader(d);
    out += '<div class="wl-compact-stack">';
    sections.forEach((s) => {
      out += `<section class="wl-card"><h3>${icon("info")}${F.escapeHtml(s.title)}<span style="margin-left:auto;font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--wl-text-muted)">${F.escapeHtml(s.sub)}</span></h3>${s.html}</section>`;
    });
    out += "</div>";
    return out;
  }

  /* ===================== NAV / shell ===================== */

  function sidebar(active) {
    const items = [
      { id: "overview", label: "总览", ic: "grid" },
      { id: "projects", label: "项目与任务", ic: "projects" },
      { id: "usage", label: "用量", ic: "usage" },
      { id: "ci", label: "CI / GitHub", ic: "ci" },
      { id: "governance", label: "治理健康", ic: "governance" },
      { id: "quality", label: "数据质量", ic: "quality" },
    ];
    let out = '<nav class="wl-sidebar wl-card" aria-label="主导航">';
    items.forEach((it) => {
      const cls = it.id === active ? "active" : "";
      out += `<a class="wl-nav-item ${cls}" href="#${it.id}">${icon(it.ic)}<span>${F.escapeHtml(it.label)}</span></a>`;
    });
    out += "</nav>";
    return out;
  }

  function topbar(d, now) {
    const fresh = d.freshness || {};
    const freshText = fresh.state === "fresh" ? "新鲜" : (fresh.state === "delayed" ? "延迟" : (fresh.state === "stale" ? "陈旧" : "未知"));
    const registered = d.summary ? d.summary.registeredProjects : 0;
    const mode = WlState.get().mode;
    const badgeCls = mode === "LIVE" ? "wl-badge-live" : (mode === "REPLAY" ? "wl-badge-replay" : "wl-badge-fixture");
    return `<div class="wl-topbar" data-tauri-drag-region>
      <div class="wl-brand" data-tauri-drag-region><span class="wl-drag-handle" data-tauri-drag-region><span></span><span></span><span></span></span><span class="wl-mark">${icon("grid")}</span>WORK-LAB Observer</div>
      <div class="wl-topbar-tools">
        <span class="wl-badge wl-badge-ro">${icon("eye")}只读</span>
        <span class="wl-badge wl-badge-cross">${icon("projects")}跨项目</span>
        <span class="wl-badge ${badgeCls}">${icon("info")}${F.escapeHtml(mode)}</span>
        <span class="wl-badge">${icon("projects")}登记 ${F.intOrDash(registered)}</span>
        <span class="wl-badge ${fresh.state === 'fresh' ? 'wl-badge-fresh' : 'wl-badge-stale'}">${icon("fresh")}${F.escapeHtml(freshText)} · ${F.freshnessAge(fresh.ageSeconds)}</span>
        <button type="button" class="wl-theme-toggle" id="settingsToggle" aria-label="外观设置" title="外观设置">${icon("layer")}</button>
      </div>
    </div>`;
  }

  function footer(d) {
    return `<footer class="wl-footer">
      <span>多源权威采集 · 统一只读投影 · Observer 零写入 · 无模型参与</span>
      <span class="mono">schema ${F.escapeHtml(d.schemaVersion || "—")} · ${F.escapeHtml(d.generatedAt || "")}</span>
    </footer>`;
  }

  return { icon, statusMeta, chipFor, renderBlocker, renderFull, renderCompact, sidebar, topbar, footer, fullSections, SORT_ORDER };
})();

if (typeof module !== "undefined" && module.exports) {
  module.exports = { WlRender };
}
