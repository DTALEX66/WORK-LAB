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
        { path: "50-taskpacks/WORK-LAB-MASTER-2.0-APPROVAL-PACKAGE.md", evidenceKind: "PLAN" },
        { path: "00-governance/generated/CURRENT_STATE.json", evidenceKind: "STATIC_BASELINE" },
        { path: "50-taskpacks/error-ledger.json", evidenceKind: "HISTORY" },
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
  ["执行实例", "CI / GitHub", "治理漂移", "Collector 覆盖", "Token 用量"].forEach((label) => {
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

t("full view keeps blueprint taskpack governance history and explicit gaps", () => {
  const html = WlRenderV3.full(snapshot());
  assert(html.includes("项目蓝图"), "plan is a first-class product section");
  assert(html.includes("28"), "TaskPack total is visible");
  assert(html.includes("WL3-620"), "task rows are visible");
  assert(html.includes("历史与恢复"), "historical ledger is visible");
  assert(html.includes("ERR-060"), "recent error evidence is visible");
  assert(html.includes("明确未验证"), "gaps are visible instead of hidden or fabricated");
  assert(html.includes("50-taskpacks/WORK-LAB-MASTER-2.0-APPROVAL-PACKAGE.md"), "source path is traceable");
  assert(!html.includes("<span>实时完成率</span>"), "static plan counts are not labeled as realtime telemetry");
});

t("production v3 entry calls only the truthful full/compact surfaces", () => {
  const app = fs.readFileSync(path.join(WEB, "scripts", "app.js"), "utf-8");
  assert(/WlRenderV3\.full\(/.test(app), "full surface entry is wired");
  assert(/WlRenderV3\.compact\(/.test(app), "compact surface entry is wired");
  ["governanceDrift", "executionsTable", "tokenCi", "kpi"].forEach((name) => {
    assert(!new RegExp("WlRenderV3\\." + name + "\\(").test(app), "retired module not called: " + name);
  });
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