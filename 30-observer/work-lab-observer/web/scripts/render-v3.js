/* WORK-LAB Observer — truthful workflow/snapshot/v3 renderer.

   Production policy:
   - canonical registry and local Git facts are the primary surface;
   - task/usage sections render only when canonical samples exist;
   - execution, CI/GitHub, governance drift and collector coverage are omitted
     until a production writer/collector supplies real observations;
   - null/UNKNOWN values never become decorative KPI cards. */

"use strict";

const WlRenderV3 = (function () {
  const F = WlFormat;

  function esc(value) {
    return F.escapeHtml(value == null ? "" : String(value));
  }

  function integer(value) {
    return Number.isInteger(value) && value >= 0 ? value : null;
  }

  function transportMeta(state) {
    const key = String(state || "UNKNOWN").toUpperCase();
    const map = {
      LIVE: { label: "事件流实时", cls: "truth-ok" },
      CONNECTING: { label: "事件流连接中", cls: "truth-warn" },
      DELAYED: { label: "事件流延迟", cls: "truth-warn" },
      OFFLINE: { label: "事件流离线", cls: "truth-bad" },
      UNKNOWN: { label: "事件流未确认", cls: "truth-muted" },
    };
    return map[key] || { label: "事件流 " + key, cls: "truth-muted" };
  }

  function projectStatus(state) {
    const key = String(state || "UNKNOWN").toUpperCase();
    const map = {
      REGISTERED: { label: "已登记", cls: "truth-ok" },
      ACTIVE: { label: "活跃", cls: "truth-ok" },
      IDLE: { label: "空闲", cls: "truth-muted" },
      UNAVAILABLE: { label: "不可用", cls: "truth-bad" },
    };
    return map[key] || { label: "已接入", cls: "truth-muted" };
  }

  function sourceTime(d, git) {
    return (git && git.observedAt) || d.sourceWatermark || null;
  }

  function connectionStrip(d) {
    const transport = transportMeta(d.transport && d.transport.transportState);
    const watermark = d.sourceWatermark;
    const revision = integer(d.revision);
    let meta = "";
    if (watermark) {
      meta += `<span class="wl-truth-meta"><span>最近采集</span><time class="mono">${esc(watermark)}</time></span>`;
    }
    if (revision && revision > 0) {
      meta += `<span class="wl-truth-meta"><span>事件版本</span><b class="mono">#${revision}</b></span>`;
    }
    return `<section class="wl-truth-strip wl-card" aria-label="只读数据链状态">
      <div class="wl-truth-source"><span class="wl-truth-dot truth-ok"></span><b>Sidecar 已连接</b><span>只读 Snapshot API</span></div>
      <div class="wl-truth-source"><span class="wl-truth-dot ${transport.cls}"></span><b>${esc(transport.label)}</b></div>
      ${meta}
    </section>`;
  }

  function gitFacts(d, project) {
    const git = project.git || {};
    if (!git.localSha) {
      return `<div class="wl-truth-empty-inline">尚无本地 Git 采集样本</div>`;
    }
    const dirty = integer(git.dirtyCount);
    const dirtyText = dirty === 0 ? "工作区干净" : (dirty == null ? null : `${dirty} 项变更`);
    const observed = sourceTime(d, git);
    return `<div class="wl-git-facts">
      <div class="wl-fact"><span>分支</span><b class="mono">${esc(git.branch || "detached")}</b></div>
      <div class="wl-fact"><span>本地 HEAD</span><b class="mono">${esc(String(git.localSha).slice(0, 8))}</b></div>
      ${dirtyText ? `<div class="wl-fact"><span>工作树</span><b>${esc(dirtyText)}</b></div>` : ""}
      ${observed ? `<div class="wl-fact wl-fact-wide"><span>采集时间</span><time class="mono">${esc(observed)}</time></div>` : ""}
    </div>`;
  }

  function projectOverview(d) {
    const projects = Array.isArray(d.projects) ? d.projects : [];
    if (!projects.length) {
      return `<section class="wl-truth-panel wl-card"><div class="wl-truth-empty"><b>尚无已批准项目</b><span>Observer 不会自动扫描或展示未批准目录。</span></div></section>`;
    }
    const cards = projects.map((project) => {
      const status = projectStatus(project.activityState);
      return `<article class="wl-project-truth-card">
        <header class="wl-project-truth-head">
          <div>
            <span class="wl-eyebrow">本地项目</span>
            <h2>${esc(project.displayName || project.projectId)}</h2>
          </div>
          <span class="wl-truth-chip ${status.cls}">${esc(status.label)}</span>
        </header>
        <div class="wl-source-labels" aria-label="真实数据来源">
          <span>项目登记</span>
          ${project.git && project.git.localSha ? "<span>本地 Git</span>" : ""}
        </div>
        ${gitFacts(d, project)}
      </article>`;
    }).join("");
    return `<section class="wl-truth-panel" id="projects">
      <div class="wl-truth-heading">
        <div><span class="wl-eyebrow">已接入工作区</span><h1>当前可观测项目</h1></div>
        <p>仅显示通过批准边界并已进入本地观测库的项目与 Git 事实。</p>
      </div>
      <div class="wl-project-truth-grid">${cards}</div>
    </section>`;
  }

  function taskFacts(d) {
    const entries = Object.entries(d.tasks || {}).filter(([, count]) => integer(count) !== null);
    if (!entries.length) return "";
    return `<section class="wl-optional-card wl-card">
      <div class="wl-optional-head"><div><span class="wl-eyebrow">Canonical store</span><h2>任务账本</h2></div><span>仅计已落库任务</span></div>
      <div class="wl-stat-list">${entries.map(([state, count]) => `<div><span class="mono">${esc(state)}</span><b>${count}</b></div>`).join("")}</div>
    </section>`;
  }

  function usageFacts(d) {
    const usageSample = d.tokenSummary || d.usage || {};
    const total = integer(usageSample.totalTokens);
    const input = integer(usageSample.inputTokens);
    const output = integer(usageSample.outputTokens);
    if (total === null && input === null && output === null) return "";
    return `<section class="wl-optional-card wl-card">
      <div class="wl-optional-head"><div><span class="wl-eyebrow">Explicit usage ledger</span><h2>用量样本</h2></div><span>${esc(usageSample.costQuality || "SOURCE_REPORTED")}</span></div>
      <div class="wl-stat-list">
        ${input !== null ? `<div><span>输入</span><b>${input}</b></div>` : ""}
        ${output !== null ? `<div><span>输出</span><b>${output}</b></div>` : ""}
        ${total !== null ? `<div><span>总量</span><b>${total}</b></div>` : ""}
      </div>
    </section>`;
  }

  function optionalFacts(d) {
    const cards = taskFacts(d) + usageFacts(d);
    return cards ? `<section class="wl-optional-grid" aria-label="有样本时显示的可选数据">${cards}</section>` : "";
  }

  function planState(status) {
    const value = String(status || "");
    if (value.includes("PENDING") || value.includes("APPROVAL")) return { label: "待完成剩余批准", cls: "truth-warn" };
    if (value.includes("BLOCKED")) return { label: "存在阻塞", cls: "truth-bad" };
    if (value.includes("VERIFIED") || value.includes("DELIVERED")) return { label: "已有本地交付证据", cls: "truth-ok" };
    return { label: "规划基线", cls: "truth-muted" };
  }

  function taskState(status) {
    const value = String(status || "").toUpperCase();
    if (value.includes("COMPLETED")) return { label: "已完成", cls: "truth-ok" };
    if (value.includes("PARTIAL")) return { label: "部分完成 / 需核对", cls: "truth-warn" };
    if (value.includes("BLOCKED")) return { label: "阻塞", cls: "truth-bad" };
    if (value.includes("NOT_EXECUTED")) return { label: "未执行", cls: "truth-bad" };
    if (value.includes("DEFERRED")) return { label: "延期", cls: "truth-warn" };
    if (value.includes("VERIFIED")) return { label: "本地已验证", cls: "truth-ok" };
    if (value.includes("READY")) return { label: "待批准", cls: "truth-warn" };
    return { label: value || "未分类", cls: "truth-muted" };
  }

  function workspaceHero(d) {
    const workspace = d.workspace || {};
    const plan = workspace.plan || {};
    const governance = workspace.governance || {};
    if (!plan.status && !governance.stage) return "";
    const state = planState(plan.status);
    const counts = plan.counts || {};
    const total = integer(counts.total);
    const verified = integer(counts.verifiedLocal);
    const blocked = integer(counts.blocked);
    const modules = Array.isArray(governance.modules) ? governance.modules.length : null;
    return `<section class="wl-workspace-hero wl-card" aria-label="项目蓝图与交付状态">
      <div class="wl-workspace-hero-main">
        <span class="wl-eyebrow">版本化规划与交付基线</span>
        <h1>WORK-LAB 项目蓝图</h1>
        <p>TaskPack、治理基线与历史账本是权威仓库事实；它们不是实时遥测，也不会被伪装成实时完成率。</p>
      </div>
      <span class="wl-truth-chip ${state.cls}">${esc(state.label)}</span>
      <div class="wl-baseline-stats">
        ${total !== null ? `<div><span>TaskPack 任务</span><b>${total}</b><small>规划口径</small></div>` : ""}
        ${verified !== null ? `<div><span>本地验证声明</span><b>${verified}</b><small>批准包记录</small></div>` : ""}
        ${blocked !== null ? `<div><span>记录阻塞</span><b>${blocked}</b><small>批准包记录</small></div>` : ""}
        ${modules !== null ? `<div><span>活跃模块</span><b>${modules}</b><small>静态治理基线</small></div>` : ""}
      </div>
    </section>`;
  }

  function taskpackSection(d) {
    const plan = (d.workspace || {}).plan || {};
    const tasks = Array.isArray(plan.tasks) ? plan.tasks : [];
    const approvals = Array.isArray(plan.approvals) ? plan.approvals : [];
    if (!tasks.length && !approvals.length) return "";
    const taskRows = tasks.map((task) => {
      const state = taskState(task.status);
      return `<div class="wl-taskpack-row">
        <b class="mono">${esc(task.taskId)}</b>
        <span class="wl-truth-chip ${state.cls}">${esc(state.label)}</span>
        <span>${esc(task.evidence || "无证据摘要")}</span>
      </div>`;
    }).join("");
    const approvalRows = approvals.map((item) => {
      const state = taskState(item.state);
      return `<div class="wl-approval-row"><span><b>${esc(item.label)}</b><small>${esc(item.detail)}</small></span><span class="wl-truth-chip ${state.cls}">${esc(state.label)}</span></div>`;
    }).join("");
    return `<section class="wl-plan-grid" id="taskpack">
      <article class="wl-card wl-plan-card">
        <header class="wl-section-head"><div><span class="wl-eyebrow">TaskPack 工作包</span><h2>阶段、任务与证据</h2></div><span>规划 / 本地验证</span></header>
        <div class="wl-taskpack-list">${taskRows}</div>
      </article>
      ${approvalRows ? `<article class="wl-card wl-approval-card"><header class="wl-section-head"><div><span class="wl-eyebrow">交付边界</span><h2>批准与未执行项</h2></div><span>批准包记录</span></header><div class="wl-approval-list">${approvalRows}</div></article>` : ""}
    </section>`;
  }

  function governanceAndGaps(d) {
    const governance = (d.workspace || {}).governance || {};
    if (!Object.keys(governance).length) return "";
    const modules = Array.isArray(governance.modules) ? governance.modules : [];
    const gaps = Array.isArray(governance.unverifiedCapabilities) ? governance.unverifiedCapabilities : [];
    const gapLabels = {
      hermes_live_apply: "Hermes 全局配置实际应用",
      paid_provider_smoke: "付费 Provider 真实冒烟",
      transferred_visual_calibration: "转移范围视觉校准",
      real_device_validation: "真实设备验证",
      commercial_release: "正式生产发布",
    };
    return `<section class="wl-governance-grid">
      <article class="wl-card wl-governance-card">
        <header class="wl-section-head"><div><span class="wl-eyebrow">CURRENT_STATE 静态基线</span><h2>治理与模块边界</h2></div><span>${esc(governance.generatedAt || "未标时间")}</span></header>
        <div class="wl-governance-facts">
          <div><span>合同</span><b>${esc(governance.contracts == null ? "—" : governance.contracts)}</b></div>
          <div><span>仓库技能</span><b>${esc(governance.skills == null ? "—" : governance.skills)}</b></div>
          <div><span>单写者</span><b>${governance.singleWriter === true ? "是" : "未确认"}</b></div>
        </div>
        <div class="wl-module-list">${modules.map((item) => `<div><b>${esc(item.id)}</b><span>${esc(item.role || item.path || "活跃模块")}</span></div>`).join("")}</div>
      </article>
      <article class="wl-card wl-gap-card">
        <header class="wl-section-head"><div><span class="wl-eyebrow">真实性边界</span><h2>明确未验证</h2></div><span>不冒充已完成</span></header>
        <div class="wl-gap-list">${gaps.map((gap) => `<div><span class="wl-truth-dot truth-warn"></span><b>${esc(gapLabels[gap] || String(gap).replaceAll("_", " "))}</b></div>`).join("") || '<div class="wl-truth-empty-inline">当前基线未列出未验证能力</div>'}</div>
      </article>
    </section>`;
  }

  function historySection(d) {
    const history = (d.workspace || {}).history || {};
    const recent = Array.isArray(history.recentErrors) ? history.recentErrors : [];
    if (history.totalErrors == null && !recent.length) return "";
    const classes = Object.entries(history.byClassification || {}).sort((a, b) => b[1] - a[1]).slice(0, 6);
    return `<section class="wl-history-grid" id="history">
      <article class="wl-card wl-history-card">
        <header class="wl-section-head"><div><span class="wl-eyebrow">错误账本 · 历史事实</span><h2>历史与恢复</h2></div><span>${esc(history.generatedAt || "版本化记录")}</span></header>
        <div class="wl-history-total"><b>${esc(history.totalErrors)}</b><span>条已记录错误与修复经验</span></div>
        <div class="wl-history-classes">${classes.map(([name, count]) => `<div><span>${esc(name.replaceAll("_", " "))}</span><b>${esc(count)}</b></div>`).join("")}</div>
      </article>
      <article class="wl-card wl-recent-card">
        <header class="wl-section-head"><div><span class="wl-eyebrow">最近记录</span><h2>根因与剩余边界</h2></div><span>历史，不是实时告警</span></header>
        <div class="wl-recent-list">${recent.map((item) => `<div><span class="mono">${esc(item.errorId)}</span><p><b>${esc(item.title || item.classification || "已记录问题")}</b>${item.remainingBoundary ? `<small>${esc(item.remainingBoundary)}</small>` : ""}</p><span class="wl-truth-chip ${item.statusAfter === "PASS" ? "truth-ok" : "truth-warn"}">${esc(item.statusAfter || "RECORDED")}</span></div>`).join("")}</div>
      </article>
    </section>`;
  }

  function sourceEvidence(d) {
    const sources = Array.isArray((d.workspace || {}).sources) ? d.workspace.sources : [];
    if (!sources.length) return "";
    return `<section class="wl-card wl-evidence-card"><header class="wl-section-head"><div><span class="wl-eyebrow">来源可追踪</span><h2>证据来源</h2></div><span>Sidecar 启动时只读加载</span></header><div class="wl-evidence-list">${sources.map((source) => `<div><span class="wl-truth-chip truth-muted">${esc(source.evidenceKind)}</span><code>${esc(source.path)}</code><time>${esc(source.generatedAt || source.loadedAt || "")}</time></div>`).join("")}</div></section>`;
  }

  function full(d) {
    return connectionStrip(d) + workspaceHero(d) + taskpackSection(d) + governanceAndGaps(d) + projectOverview(d) + optionalFacts(d) + historySection(d) + sourceEvidence(d);
  }

  function compact(d) {
    const projects = Array.isArray(d.projects) ? d.projects : [];
    const transport = transportMeta(d.transport && d.transport.transportState);
    const rows = projects.map((project) => {
      const git = project.git || {};
      const status = projectStatus(project.activityState);
      return `<div class="wl-compact-truth-row"><div><b>${esc(project.displayName || project.projectId)}</b><span class="mono">${esc(git.branch || "—")} · ${esc(git.localSha ? String(git.localSha).slice(0, 8) : "无 Git 样本")}</span></div><span class="wl-truth-chip ${status.cls}">${esc(status.label)}</span></div>`;
    }).join("");
    return `<section class="wl-compact-truth wl-card"><header><div><span class="wl-eyebrow">WORK-LAB Observer</span><h1>只读项目事实</h1></div><span class="wl-truth-chip ${transport.cls}">${esc(transport.label)}</span></header>${rows || '<div class="wl-truth-empty-inline">尚无已批准项目</div>'}</section>`;
  }

  return { connectionStrip, projectOverview, optionalFacts, workspaceHero, taskpackSection, governanceAndGaps, historySection, sourceEvidence, full, compact };
})();

if (typeof module !== "undefined" && module.exports) {
  module.exports = { WlRenderV3 };
}