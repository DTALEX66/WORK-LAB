/* WORK-LAB Observer — truthful v3 render contract tests.
   The production surface only renders facts that have a real canonical source.
   Empty execution/CI/governance/collector-health projections must not become
   permanent cards or fabricated zero/UNKNOWN KPIs. */

"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { loadScripts, WEB } = require("./helpers.js");

const { WlApi, WlState, WlRenderV3 } = loadScripts();

function snapshot(overrides) {
  return WlApi.normalizeV3(Object.assign({
    schemaVersion: "workflow/snapshot/v3",
    revision: 0,
    generatedAt: "2026-08-14T15:00:00Z",
    sourceWatermark: "2026-08-14T14:59:30Z",
    transport: {
      transportState: "DELAYED",
      freshnessState: "UNKNOWN",
      eventsUrl: "http://127.0.0.1:54245/api/v1/events",
    },
    projects: [{
      projectId: "work-lab",
      displayName: "WORK-LAB",
      identityState: "RESOLVED",
      activityState: "REGISTERED",
      git: {
        localSha: "769345d21fb9df9d0acafe13f953e41597658b80",
        branch: "main",
        dirtyCount: 10,
        observedAt: "2026-08-14T14:59:30Z",
        quality: "EXACT_SOURCE",
        freshness: "STALE",
        sourceRef: "git-rev-parse",
      },
    }],
    tasks: {},
    executions: [],
    tokenSummary: {
      inputTokens: null,
      outputTokens: null,
      totalTokens: null,
      costQuality: "UNKNOWN",
    },
    ci: [],
    workspace: {
      plan: {
        taskpackId: "WORK-LAB-FINAL-MASTER-CONTROL-PLANE",
        status: "DELIVERED_PENDING_REMAINING_APPROVALS",
        counts: { total: 28, verifiedLocal: 24, blocked: 1, reconcileRequired: 3 },
        tasks: [
          { taskId: "WL3-600", status: "VERIFIED_LOCAL", evidence: "真实 SSE" },
          { taskId: "WL3-620", status: "BLOCKED", evidence: "便携构建边界" },
        ],
      },
      governance: {
        modules: [{ id: "workflow-assistance" }, { id: "work-lab-observer" }],
        contracts: 30,
        skills: 13,
        singleWriter: true,
        unverifiedCapabilities: ["commercial_release", "real_device_validation"],
      },
      history: {
        totalErrors: 60,
        byClassification: { contract_drift: 27, feature_gap: 4 },
        recentErrors: [{ errorId: "ERR-060", title: "Observer fail-closed contract", statusAfter: "PASS" }],
      },
      sources: [
        { path: "taskpacks/current/WORK-LAB-MASTER-2.0-APPROVAL-PACKAGE.md", evidenceKind: "PLAN" },
        { path: ".project/governance/generated/CURRENT_STATE.json", evidenceKind: "STATIC_BASELINE" },
        { path: "taskpacks/current/error-ledger.json", evidenceKind: "HISTORY" },
      ],
    },
  }, overrides || {}));
}

let failures = 0;
let ran = 0;
function t(name, fn) {
  ran += 1;
  try {
    fn();
    console.log("PASS " + name);
  } catch (err) {
    failures += 1;
    console.log("FAIL " + name + "\n  " + err.message);
  }
}

t("connection strip reports the real sidecar/event state without 0/0 coverage", () => {
  const html = WlRenderV3.connectionStrip(snapshot());
  assert(html.includes("Sidecar 已连接"), "successful snapshot fetch is shown as connected");
  assert(html.includes("事件流延迟"), "backend DELAYED verdict remains visible");
  assert(html.includes("2026-08-14T14:59:30Z"), "real source watermark is rendered");
  assert(!html.includes("0/0"), "missing collector_health is not rendered as coverage");
  assert(!html.includes("collector_health"), "internal table name is not exposed");
  assert(!html.includes("#0"), "meaningless zero revision is hidden");
});

t("last-good becomes visibly OFFLINE when the EventSource transport fails", () => {
  WlState.accept(snapshot(), "LIVE");
  WlState.markRefreshError("event stream offline", true);
  const state = WlState.get();
  assert.strictEqual(state.mode, "OFFLINE");
  assert.strictEqual(state.data.transport.transportState, "OFFLINE");
  assert.strictEqual(state.data.transport.eventStreamConnected, false);
  const html = WlRenderV3.connectionStrip(state.data);
  assert(html.includes("Sidecar 离线"), "stale last-good must not claim sidecar connectivity");
  assert(html.includes("事件流离线"), "EventSource failure is visible");
  assert(!html.includes("Sidecar 已连接"), "old transport evidence cannot override local failure");
});

t("project surface keeps canonical registry and local Git facts", () => {
  const html = WlRenderV3.projectOverview(snapshot());
  assert(html.includes("WORK-LAB"), "canonical project name");
  assert(html.includes("已登记"), "REGISTERED has truthful user-facing semantics");
  assert(html.includes("main"), "local branch");
  assert(html.includes("769345d2"), "short local HEAD");
  assert(html.includes("10 项变更"), "real dirty file count");
  assert(html.includes("2026-08-14T14:59:30Z"), "Git observation time");
});

t("unsupported execution/CI/governance fields never become cards", () => {
  const html = WlRenderV3.full(snapshot());
  ["执行实例", "CI / GitHub", "治理漂移", "Collector 覆盖"].forEach((label) => {
    assert(!html.includes(label), "unsupported or empty module hidden: " + label);
  });
  assert(!html.includes("UNKNOWN"), "no permanent UNKNOWN filler");
});

t("task and usage sections appear only when canonical samples exist", () => {
  const empty = WlRenderV3.optionalFacts(snapshot());
  assert.strictEqual(empty, "", "no empty optional cards");

  const populated = snapshot({
    tasks: { PENDING: 2, COMPLETED_LOCAL: 5 },
    tokenSummary: {
      inputTokens: 1200,
      outputTokens: 300,
      totalTokens: 1500,
      costQuality: "EXACT_SOURCE",
    },
  });
  const html = WlRenderV3.optionalFacts(populated);
  assert(html.includes("任务账本"), "real canonical task counts shown");
  assert(html.includes("PENDING") && html.includes("2"), "task status preserved");
  assert(html.includes("用量样本"), "real usage sample shown");
  assert(html.includes("1500"), "real total tokens shown");
});

t("full view: connection + token dash + status matrix + governance only", () => {
  const html = WlRenderV3.full(snapshot());
  assert(html.includes("跨项目运行状态"), "cross-project runtime matrix present");
  assert(html.includes("TOKEN 仪表盘"), "token dashboard present");
  assert(html.includes("Sidecar"), "connection strip present");
  assert(html.includes("治理"), "governance present");
  // Per-project internal task matrices are NOT rendered.
  assert(!html.includes("项目蓝图"), "no workspace hero/taskpack");
  assert(!html.includes("TaskPack 任务"), "no internal taskpack matrix");
  assert(!html.includes("历史与恢复"), "no history ledger");
  assert(!html.includes("证据来源"), "no evidence sources");
});

t("production v3 entry calls fusion + truthful surfaces", () => {
  const app = fs.readFileSync(path.join(WEB, "scripts", "app.js"), "utf-8");
  assert(/WlFusionV3\.render\(/.test(app), "fusion render is wired for full view");
  assert(/WlRenderV3\.compact\(/.test(app), "compact surface entry is wired");
  ["governanceDrift", "executionsTable", "tokenCi", "kpi"].forEach((name) => {
    assert(!new RegExp("WlRenderV3\\." + name + "\\(").test(app), "retired module not called: " + name);
  });
});


t("metric cards render real data only", () => {
  const d = snapshot();
  d.projects = [d.projects[0]];
  d.tasks = { completed: 3, running: 1 };
  d.tokenSummary = { totalTokens: 1500000, inputTokens: 500000, outputTokens: 1000000 };
  d.coverage = { numerator: 6, denominator: 6 };
  const html = WlRenderV3.metricCards(d);
  assert(html.includes("已接入项目"), "projects metric present");
  assert(html.includes("1"), "projects count rendered");
  assert(html.includes("任务"), "tasks metric present");
  assert(html.includes("4"), "task total rendered");
  assert(html.includes("Token 用量"), "usage metric present");
  assert(html.includes("1.5M"), "usage formatted as M");
  assert(html.includes("采集覆盖"), "coverage metric present");
  assert(html.includes("100%"), "coverage pct rendered");
});

t("metric cards never fabricate from UNKNOWN/zero", () => {
  const d = snapshot();
  d.projects = [];
  d.tasks = {};
  d.tokenSummary = { totalTokens: null, inputTokens: null, outputTokens: null };
  d.coverage = null;
  const html = WlRenderV3.metricCards(d);
  assert(html === "", "no metrics when no canonical data");
});

t("full view has no per-project task matrix", () => {
  const d = snapshot();
  d.tasks = { completed: 3 };
  const html = WlRenderV3.full(d);
  assert(!html.includes("wl-taskpack"), "no taskpack section in full view");
  assert(!html.includes("wl-project-truth-card"), "no per-project task cards");
});


t("platform status matrix shows project/platform/activity", () => {
  const d = snapshot();
  d.projects = [Object.assign({}, d.projects[0], {
    agentPlatform: "dsh", activityState: "RUNNING",
  })];
  d.tokenSummary = { totalTokens: 2500000, inputTokens: 1000000, outputTokens: 1500000, cacheHitTokens: 800000, cacheMissTokens: 200000 };
  const html = WlRenderV3.platformStatusMatrix(d);
  assert(html.includes("跨项目运行状态"), "matrix heading present");
  assert(html.includes("DSH"), "platform label shown");
  assert(html.includes("运行中"), "activity badge shown");
  assert(html.includes("main"), "branch shown");
  assert(!html.includes("wl-project-truth-card"), "no per-project task card");
});

t("token dashboard renders real tokens only", () => {
  const d = snapshot();
  d.tokenSummary = { totalTokens: 2500000, inputTokens: 1000000, outputTokens: 1500000, cacheHitTokens: 800000, cacheMissTokens: 200000 };
  const html = WlRenderV3.tokenDashboard(d);
  assert(html.includes("TOKEN 仪表盘"), "token dash heading");
  assert(html.includes("2.5M"), "total formatted");
  assert(html.includes("80%"), "hit rate computed");
  assert(html.includes("缓存命中"), "hit cell");
});

t("token dashboard empty when no sample", () => {
  const d = snapshot();
  d.tokenSummary = { totalTokens: null, inputTokens: null, outputTokens: null };
  const html = WlRenderV3.tokenDashboard(d);
  assert(html.includes("尚无真实 token 样本"), "empty state, no fabricated KPI");
});

t("full view prefers runtime matrix over task matrix", () => {
  const d = snapshot();
  const html = WlRenderV3.full(d);
  const statusIdx = html.indexOf("wl-status-panel");
  const taskIdx = html.indexOf("wl-taskpack");
  assert(statusIdx !== -1, "runtime status matrix in full view");
  assert(!html.includes("项目运行全景"), "legacy project table gone");
});

t("CC2: single unified project grid (no duplicated surfaces)", () => {
  const d = snapshot();
  const html = WlFusionV3.render(d);
  // Global Command + one Projects grid
  assert(html.includes("wl-cmd-global"), "global command present");
  assert(html.includes("wl-proj-grid"), "single project grid");
  // No duplicated project surfaces
  assert(!html.includes("wl-signal-strip"), "no old signal strip");
  assert(!html.includes("wl-matrix-row"), "no old runtime matrix");
  assert(!html.includes("wl-hp-card"), "no old homepage card");
});

t("CC2: truth - token telemetry empty state when no sample", () => {
  const d = snapshot();
  d.tokenSummary = { totalTokens: null, inputTokens: null, outputTokens: null };
  const html = WlFusionV3.render(d);
  assert(html.includes("No token samples yet"), "empty state, no fake zero");
  assert(!html.includes("0 Token"), "no fabricated zero KPI");
});

t("CC2: telemetry renders real tokens", () => {
  const d = snapshot();
  d.tokenSummary = { totalTokens: 2500000, inputTokens: 1000000, outputTokens: 1500000, cacheHitTokens: 800000, cacheMissTokens: 200000 };
  const html = WlFusionV3.render(d);
  assert(html.includes("AI Telemetry"), "telemetry section");
  assert(html.includes("2.5M"), "total");
  assert(html.includes("80%"), "hit rate");
});

t("CC2: project card shows platform/git/status", () => {
  const d = snapshot();
  d.projects = [Object.assign({}, d.projects[0], { agentPlatform: "DSH" })];
  const html = WlFusionV3.render(d);
  assert(html.includes("WORK-LAB"), "project name");
  assert(html.includes("DSH"), "platform");
  assert(html.includes("wl-proj-card"), "project card");
  assert(html.includes("main"), "branch");
  assert(html.includes("wl-proj-dot"), "status dot");
});

t("app.js wires fusion render", () => {
  const app = fs.readFileSync(path.join(WEB, "scripts", "app.js"), "utf-8");
  assert(app.includes("WlFusionV3.render"), "fusion render wired");
});

function run() {
  return { pass: ran - failures, fail: failures };
}

if (require.main === module) {
  console.log("\n==== WORK-LAB Observer truthful v3 render tests ====");
  console.log("TOTAL: " + (ran - failures) + " passed, " + failures + " failed");
  process.exit(failures ? 1 : 0);
}

module.exports = { run };