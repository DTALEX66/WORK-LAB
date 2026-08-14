/* WORK-LAB Observer — render-v3.js (WLGM-180/190/200)
   Renders the canonical v3 snapshot surface (normalized by api.js normalizeV3):
     - global transport/freshness/coverage/revision bar
     - KPI: active projects / executions / waiting / blocked
     - product project table with activityState, agent distribution, attention,
       activeExecutionCount, last strong evidence, visibility/quality, git match
     - executions list with evidence level + transport state
     - token/cost + CI summaries
     - per-project detail (WLGM-190): identity, bindings, executions, git/CI
     - compact view (WLGM-200): transport/freshness + active + waiting/blocked +
       primary blocker + token coverage + last strong evidence
   Read-only: pure render, no fetch, no writes. Status is icon + text + color. */

const WlRenderV3 = (function () {
  "use strict";

  const F = WlFormat;

  function icon(name) {
    return `<svg class="wl-icon" aria-hidden="true" focusable="false"><use href="#i-${name}"/></svg>`;
  }

  function esc(v) {
    return F.escapeHtml(v == null ? "—" : String(v));
  }

  /* Map v3 transport/freshness to chip. */
  function transportMeta(transport) {
    const st = String((transport && transport.transportState) || "UNKNOWN").toUpperCase();
    const fs = String((transport && transport.freshnessState) || "UNKNOWN").toUpperCase();
    const tmap = { LIVE: { cls: "running", ic: "running", text: "LIVE" }, DELAYED: { cls: "waiting", ic: "waiting", text: "DELAYED" }, OFFLINE: { cls: "blocked", ic: "blocked", text: "OFFLINE" }, CONNECTING: { cls: "waiting", ic: "waiting", text: "CONNECTING" } };
    const fmap = { FRESH: { cls: "fresh", ic: "fresh", text: "FRESH" }, STALE: { cls: "stale", ic: "clock", text: "STALE" }, EXPIRED: { cls: "blocked", ic: "alert", text: "EXPIRED" } };
    const t = tmap[st] || { cls: "unknown", ic: "unknown", text: st };
    const f = fmap[fs] || { cls: "unknown", ic: "unknown", text: fs };
    return `<span class="wl-chip ${t.cls}">${icon(t.ic)}传输 ${t.text}</span> <span class="wl-chip ${f.cls}">${icon(f.ic)}新鲜度 ${f.text}</span>`;
  }

  function attentionMeta(attention) {
    switch (attention) {
      case "WAITING_APPROVAL_PRESENT": return { cls: "waiting", ic: "waiting", text: "等待批准" };
      case "WAITING_USER_PRESENT": return { cls: "waiting", ic: "waiting", text: "等待用户" };
      case "BLOCKED_PRESENT": return { cls: "blocked", ic: "blocked", text: "阻塞" };
      default: return { cls: "idle", ic: "clock", text: "无" };
    }
  }

  function activityMeta(state) {
    switch (String(state || "UNKNOWN").toUpperCase()) {
      case "ACTIVE": return { cls: "running", ic: "running", text: "活跃" };
      case "IDLE": return { cls: "idle", ic: "clock", text: "空闲" };
      case "NO_ACTIVE_EXECUTION": return { cls: "idle", ic: "clock", text: "无执行" };
      case "PARTIAL_VISIBILITY": return { cls: "waiting", ic: "waiting", text: "部分可见" };
      case "UNRESOLVED": return { cls: "unknown", ic: "unknown", text: "未解析" };
      default: return { cls: "unknown", ic: "unknown", text: "未知" };
    }
  }

  function execMeta(state) {
    switch (String(state || "UNKNOWN").toUpperCase()) {
      case "RUNNING": case "STARTING": return { cls: "running", ic: "running", text: "运行" };
      case "WAITING_USER": return { cls: "waiting", ic: "waiting", text: "等待用户" };
      case "WAITING_APPROVAL": return { cls: "waiting", ic: "waiting", text: "等待批准" };
      case "BLOCKED": return { cls: "blocked", ic: "blocked", text: "阻塞" };
      case "COMPLETED": return { cls: "completed", ic: "completed", text: "完成" };
      case "FAILED": return { cls: "failed", ic: "failed", text: "失败" };
      case "CANCELLED": return { cls: "idle", ic: "clock", text: "取消" };
      case "LOST": return { cls: "blocked", ic: "alert", text: "失联" };
      case "DISCOVERED": return { cls: "waiting", ic: "waiting", text: "发现" };
      default: return { cls: "unknown", ic: "unknown", text: "未知" };
    }
  }

  function gitMatchMeta(match) {
    switch (String(match || "NO_LOCAL_CLAIM")) {
      case "MATCH": return { cls: "completed", text: "三端一致" };
      case "LOCAL_REMOTE_MATCH": return { cls: "running", text: "本地=远端" };
      case "LOCAL_CI_MATCH": return { cls: "waiting", text: "本地=CI" };
      case "MISMATCH": return { cls: "blocked", text: "不一致" };
      default: return { cls: "unknown", text: String(match || "无本地声明") };
    }
  }

  /* Agent distribution across executions per project. */
  function agentCounts(d, projectId) {
    const counts = {};
    (d.executions || []).forEach((e) => {
      if (e.anchorProjectId === projectId && e.agent) {
        counts[e.agent] = (counts[e.agent] || 0) + 1;
      }
    });
    return counts;
  }

  /* ---------- WLGM-180: global transport/freshness/coverage bar ---------- */
  function globalBar(d) {
    const cov = d.coverage || {};
    const covText = (cov.numerator == null || cov.denominator == null)
      ? "未知"
      : `${cov.numerator}/${cov.denominator}${cov.scope ? " · " + esc(cov.scope) : ""}`;
    const covCls = (cov.numerator != null && cov.denominator != null && cov.numerator >= cov.denominator) ? "fresh" : "stale";
    return `
      <div class="wl-card wl-global-bar">
        <div class="wl-global-bar-row">
          <span class="wl-kv"><span class="wl-kv-label">${icon("fresh")}传输/新鲜度</span>${transportMeta(d.transport)}</span>
          <span class="wl-kv"><span class="wl-kv-label">${icon("quality")}Collector 覆盖</span><span class="wl-chip ${covCls}">${covText}</span></span>
          <span class="wl-kv"><span class="wl-kv-label">${icon("sha")}投影 revision</span><span class="wl-chip">#${esc(d.revision)}</span></span>
          <span class="wl-kv"><span class="wl-kv-label">${icon("clock")}水印</span><span class="wl-mono">${esc(d.sourceWatermark)}</span></span>
        </div>
      </div>`;
  }

  /* ---------- WLGM-180: KPI ---------- */
  function kpi(d) {
    const projects = d.projects || [];
    const executions = d.executions || [];
    const activeProjects = projects.filter((p) => String(p.state || "").toLowerCase() === "active").length;
    const activeExecs = executions.filter((e) => ["RUNNING", "STARTING", "WAITING_USER", "WAITING_APPROVAL", "BLOCKED"].includes(String(e.state || "").toUpperCase())).length;
    const waiting = executions.filter((e) => ["WAITING_USER", "WAITING_APPROVAL"].includes(String(e.state || "").toUpperCase())).length;
    const blocked = executions.filter((e) => String(e.state || "").toUpperCase() === "BLOCKED").length;
    const cards = [
      { label: "活跃项目", value: activeProjects, note: "activityState=ACTIVE", ic: "projects" },
      { label: "执行中", value: activeExecs, note: "running/starting", ic: "running" },
      { label: "等待", value: waiting, note: "用户/批准", ic: "waiting" },
      { label: "阻塞", value: blocked, note: "需关注", ic: "blocked" },
    ];
    let out = '<div class="wl-grid wl-kpi">';
    cards.forEach((c) => {
      out += `<div class="wl-card wl-metric"><div class="wl-metric-label">${icon(c.ic)}${c.label}</div>` +
        `<div class="wl-metric-value">${c.value}</div><div class="wl-metric-note">${c.note}</div></div>`;
    });
    out += "</div>";
    return out;
  }

  /* ---------- WLGM-180: project table ---------- */
  function projectTable(d) {
    const projects = (d.projects || []).slice();
    const sortRank = { blocked: 0, waiting: 1, active: 2, idle: 3, unknown: 4 };
    projects.sort((a, b) => (sortRank[a.state] != null ? sortRank[a.state] : 9) - (sortRank[b.state] != null ? sortRank[b.state] : 9));
    if (!projects.length) {
      return `<div class="wl-state-note">${icon("info")}暂无已批准项目（候选需先批准）。</div>`;
    }
    const rows = projects.map((p) => {
      const am = activityMeta(p.state);
      const attn = attentionMeta(p.attentionState);
      const agents = agentCounts(d, p.projectId);
      const agentText = Object.keys(agents).length
        ? Object.entries(agents).map(([k, v]) => `${esc(k)}×${v}`).join(" ")
        : (p.agentPlatform ? esc(p.agentPlatform) : "—");
      const gm = gitMatchMeta(p.git && p.git.matchState);
      const evidence = p.lastStrongEvidenceAt ? `<span class="wl-mono">${esc(p.lastStrongEvidenceAt)}</span>` : "—";
      return `
        <tr data-project="${esc(p.projectId)}" class="wl-proj-row" tabindex="0" aria-label="项目 ${esc(p.displayName || p.projectId)}">
          <td><div class="wl-proj-name">${esc(p.displayName || p.projectId)}<span class="wl-proj-id">${esc(p.projectId)}</span></div></td>
          <td><span class="wl-chip ${am.cls}">${icon(am.ic)}${am.text}</span></td>
          <td>${esc(p.activeExecutionCount)}</td>
          <td>${agentText}</td>
          <td><span class="wl-chip ${attn.cls}">${icon(attn.ic)}${attn.text}</span></td>
          <td>${evidence}</td>
          <td><span class="wl-quality"><span class="wl-qdot ${String(p.visibility || "UNKNOWN").toLowerCase()}"></span>${esc(p.visibility)}</span> <span class="wl-quality">${esc(p.quality)}</span></td>
          <td><span class="wl-chip ${gm.cls}">${gm.text}</span></td>
        </tr>`;
    });
    return `
      <div class="wl-card">
        <h3 class="wl-section-title">${icon("projects")}主体项目（${projects.length}）</h3>
        <div class="wl-table-wrap"><table class="wl-table">
          <thead><tr><th>项目</th><th>活动状态</th><th>执行数</th><th>Agent 分布</th><th>关注</th><th>最近强证据</th><th>可见性/质量</th><th>Git</th></tr></thead>
          <tbody>${rows.join("")}</tbody>
        </table></div>
        <div id="wl-v3-detail"></div>
      </div>`;
  }

  /* ---------- WLGM-180: executions list ---------- */
  function executionsTable(d) {
    const executions = d.executions || [];
    if (!executions.length) {
      return `<div class="wl-card"><h3 class="wl-section-title">${icon("running")}Executions</h3><div class="wl-state-note">${icon("info")}无 execution 证据（未接入 Agent 时显示 unsupported/unknown，不显示 0 个任务）。</div></div>`;
    }
    const rows = executions.map((e) => {
      const em = execMeta(e.state);
      const tm = transportMeta({ transportState: e.transportState || "UNKNOWN" });
      const lvl = e.evidenceLevel ? `<span class="wl-chip">L${esc(e.evidenceLevel)}</span>` : "";
      return `<tr>
        <td><span class="wl-mono">${esc(e.executionId)}</span></td>
        <td>${esc(e.agent)}</td>
        <td>${esc(e.anchorProjectId)}</td>
        <td><span class="wl-chip ${em.cls}">${icon(em.ic)}${em.text}</span></td>
        <td>${esc(e.stateQuality)}</td>
        <td>${tm}</td>
        <td>${lvl}${e.sourceRef ? `<span class="wl-mono wl-src">${esc(e.sourceRef)}</span>` : ""}</td>
      </tr>`;
    });
    return `
      <div class="wl-card"><h3 class="wl-section-title">${icon("running")}当前 Executions（${executions.length}）</h3>
      <div class="wl-table-wrap"><table class="wl-table">
        <thead><tr><th>execution</th><th>Agent</th><th>项目</th><th>状态</th><th>状态质量</th><th>传输</th><th>证据</th></tr></thead>
        <tbody>${rows.join("")}</tbody>
      </table></div></div>`;
  }

  /* ---------- WLGM-180: token + CI ---------- */
  function tokenCi(d) {
    const u = d.usage || {};
    const tokenText = (u.inputTokens == null && u.outputTokens == null)
      ? "未知（未补零）"
      : `in ${esc(u.inputTokens)} / out ${esc(u.outputTokens)} / 总 ${esc(u.totalTokens)}`;
    const cost = u.costQuality ? `（${esc(u.costQuality)}）` : "";
    const ciRows = (d.ci || []).map((r) => {
      const c = String(r.conclusion || "").toLowerCase() === "success" ? { cls: "completed", text: "通过" }
        : String(r.conclusion || "").toLowerCase() === "failure" ? { cls: "failed", text: "失败" }
        : { cls: "waiting", text: String(r.status || "进行中") };
      return `<tr><td><span class="wl-mono">${esc(r.workflow)}</span></td><td><span class="wl-mono">${esc(r.headSha)}</span></td><td><span class="wl-chip ${c.cls}">${c.text}</span></td></tr>`;
    }).join("");
    return `
      <div class="wl-grid wl-cols-2">
        <div class="wl-card"><h3 class="wl-section-title">${icon("token")}Token / 费用</h3>
          <div class="wl-kv"><span class="wl-kv-label">用量</span><span class="wl-mono">${tokenText}</span></div>
          <div class="wl-kv"><span class="wl-kv-label">费用质量</span><span class="wl-chip">${esc(cost || "UNKNOWN")}</span></div>
        </div>
        <div class="wl-card"><h3 class="wl-section-title">${icon("ci")}CI（exact-SHA）</h3>
          ${d.ci && d.ci.length ? `<div class="wl-table-wrap"><table class="wl-table"><thead><tr><th>workflow</th><th>head SHA</th><th>结论</th></tr></thead><tbody>${ciRows}</tbody></table></div>` : `<div class="wl-state-note">${icon("info")}${esc(d.git && d.git.ciSha ? "无 CI run" : "exact-SHA CI UNVERIFIED")}</div>`}
        </div>
      </div>`;
  }

  /* ---------- WLGM-190: per-project detail ---------- */
  function projectDetail(d, projectId) {
    const p = (d.projects || []).find((x) => x.projectId === projectId);
    if (!p) return "";
    const execs = (d.executions || []).filter((e) => e.anchorProjectId === projectId);
    const execRows = execs.map((e) => {
      const em = execMeta(e.state);
      return `<li><span class="wl-chip ${em.cls}">${em.text}</span> <span class="wl-mono">${esc(e.executionId)}</span> · ${esc(e.agent)} · ${esc(e.sessionId || "无 session")} · L${esc(e.evidenceLevel || "?")}${e.sourceRef ? ` · src ${esc(e.sourceRef)}` : ""}</li>`;
    }).join("") || `<li>无 execution 证据</li>`;
    const git = p.git || {};
    const gm = gitMatchMeta(git.matchState);
    const tok = p.token || {};
    return `
      <div class="wl-card wl-detail" data-project-detail="${esc(projectId)}">
        <h3 class="wl-section-title">${icon("info")}项目详情 · ${esc(p.displayName || p.projectId)}</h3>
        <div class="wl-kv"><span class="wl-kv-label">活动状态</span>${activityMeta(p.state).text} / 关注 ${attentionMeta(p.attentionState).text}</div>
        <div class="wl-kv"><span class="wl-kv-label">身份</span>${esc(p.identityState || "UNRESOLVED")} · 可见性 ${esc(p.visibility)} · 质量 ${esc(p.quality)}</div>
        <div class="wl-kv"><span class="wl-kv-label">Git</span>${gm.text} · <span class="wl-mono">${esc(git.localSha)}</span></div>
        <div class="wl-kv"><span class="wl-kv-label">Token</span>in ${esc(tok.inputTokens == null ? "未知" : tok.inputTokens)} / out ${esc(tok.outputTokens == null ? "未知" : tok.outputTokens)} (${esc(tok.costQuality || "UNKNOWN")})</div>
        <div class="wl-kv"><span class="wl-kv-label">最近强证据</span><span class="wl-mono">${esc(p.lastStrongEvidenceAt || "—")}</span></div>
        <h4>Executions</h4><ul class="wl-detail-list">${execRows}</ul>
        ${p.sourceRefs && p.sourceRefs.length ? `<h4>Source refs</h4><ul class="wl-detail-list">${p.sourceRefs.map((s) => `<li><span class="wl-mono">${esc(s)}</span></li>`).join("")}</ul>` : ""}
      </div>`;
  }

  /* ---------- WLGM-200: compact ---------- */
  function compact(d) {
    const projects = d.projects || [];
    const executions = d.executions || [];
    const activeExecs = executions.filter((e) => ["RUNNING", "STARTING", "WAITING_USER", "WAITING_APPROVAL", "BLOCKED"].includes(String(e.state || "").toUpperCase()));
    const waiting = executions.filter((e) => ["WAITING_USER", "WAITING_APPROVAL"].includes(String(e.state || "").toUpperCase()));
    const blocked = executions.filter((e) => String(e.state || "").toUpperCase() === "BLOCKED");
    const primaryBlocker = blocked[0] || waiting[0] || null;
    const cov = d.coverage || {};
    const lastStrong = projects.map((p) => p.lastStrongEvidenceAt).filter(Boolean).sort().slice(-1)[0] || "—";
    const rows = projects.map((p) => {
      const am = activityMeta(p.state);
      const attn = attentionMeta(p.attentionState);
      return `<li class="wl-compact-row"><span class="wl-chip ${am.cls}">${am.text}</span> ${esc(p.displayName || p.projectId)} ${p.activeExecutionCount > 0 ? `<b>${p.activeExecutionCount}</b>` : ""} <span class="wl-chip ${attn.cls}">${attn.text}</span></li>`;
    }).join("") || `<li>无已批准项目</li>`;
    return `
      <div class="wl-card wl-compact-bar">${transportMeta(d.transport)} <span class="wl-chip">覆盖 ${esc(cov.numerator == null ? "未知" : cov.numerator + "/" + cov.denominator)}</span></div>
      <ul class="wl-compact-list">${rows}</ul>
      <div class="wl-kv"><span class="wl-kv-label">执行中</span><b>${activeExecs.length}</b> · 等待 <b>${waiting.length}</b> · 阻塞 <b>${blocked.length}</b></div>
      <div class="wl-kv"><span class="wl-kv-label">主关注</span>${primaryBlocker ? esc(primaryBlocker.agent + " · " + primaryBlocker.anchorProjectId + " · " + primaryBlocker.state) : "无"}</div>
      <div class="wl-kv"><span class="wl-kv-label">最近强证据</span><span class="wl-mono">${esc(lastStrong)}</span></div>`;
  }

  return {
    globalBar,
    kpi,
    projectTable,
    executionsTable,
    tokenCi,
    projectDetail,
    compact,
    activityMeta,
    attentionMeta,
    execMeta,
  };
})();

if (typeof module !== "undefined" && module.exports) {
  module.exports = { WlRenderV3 };
}
