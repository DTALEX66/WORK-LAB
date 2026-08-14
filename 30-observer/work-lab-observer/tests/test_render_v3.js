/* WORK-LAB Observer — test_render_v3.js (WLGM-180/190/200)
   Contract tests for the v3 snapshot render surface: global bar, KPI,
   project table (activity/agent/attention/git), executions, per-project
   detail, compact view, and strict null-vs-unknown rendering. */

"use strict";

const assert = require("assert");
const { loadScripts, loadFixture } = require("./helpers.js");

const { WlApi, WlRenderV3 } = loadScripts();

/* Build a v3 snapshot through the real normalization path (api.js normalizeV3). */
function v3Surface() {
  const snapshot = {
    schemaVersion: "workflow/snapshot/v3",
    revision: 42,
    generatedAt: "2026-08-14T00:00:00Z",
    sourceWatermark: "2026-08-14T00:00:05Z",
    transport: { transportState: "LIVE", freshnessState: "FRESH", coverageNumerator: 3, coverageDenominator: 3, coverageScope: "key-collectors" },
    coverage: { numerator: 3, denominator: 3, scope: "key-collectors" },
    projects: [
      { projectId: "work-lab", displayName: "WORK-LAB", identityState: "RESOLVED", activityState: "ACTIVE", attentionState: "WAITING_APPROVAL_PRESENT", activeExecutionCount: 2, visibility: "FULL", quality: "SOURCE_REPORTED", lastStrongEvidenceAt: "2026-08-14T00:00:04Z", git: { localSha: "a".repeat(40), remoteSha: "a".repeat(40), ciSha: null, matchState: "LOCAL_REMOTE_MATCH" } },
      { projectId: "minigame", displayName: "MINIGAME", identityState: "RESOLVED", activityState: "IDLE", attentionState: "NONE", activeExecutionCount: 0, visibility: "FULL", quality: "SOURCE_REPORTED", lastStrongEvidenceAt: null },
    ],
    executions: [
      { executionId: "exec-1", agent: "hermes", sessionId: "s1", anchorProjectId: "work-lab", state: "RUNNING", stateQuality: "SOURCE_REPORTED", transportState: "LIVE", evidenceLevel: "A", sourceRef: "hermes-run-1" },
      { executionId: "exec-2", agent: "codex", sessionId: "s2", anchorProjectId: "work-lab", state: "WAITING_APPROVAL", stateQuality: "SOURCE_REPORTED", transportState: "LIVE", evidenceLevel: "B", sourceRef: "codex-run-1" },
    ],
    tasks: { PENDING: 1 },
    tokenSummary: { inputTokens: 120000, outputTokens: 45000, totalTokens: 165000, costQuality: "ESTIMATED" },
    git: { localSha: "a".repeat(40), remoteSha: "a".repeat(40), ciSha: null, matchState: "LOCAL_REMOTE_MATCH" },
    ci: [{ runId: "run-1", workflow: "governance.yml", headSha: "a".repeat(40), status: "completed", conclusion: "success", sourceRef: "gh-1" }],
    sourceRefs: ["hermes-run-1", "codex-run-1", "gh-1"],
  };
  return WlApi.normalizeV3(snapshot);
}

let failures = 0;
function t(name, fn) {
  try {
    fn();
    console.log("PASS " + name);
  } catch (err) {
    failures += 1;
    console.log("FAIL " + name + "\n  " + err.message);
  }
}

const d = v3Surface();

t("v3 surface is recognized by renderer", () => {
  assert.strictEqual(d.schemaVersion, "work-lab/observer-projection/v2-rendered");
  assert.strictEqual(d.revision, 42);
});

t("global bar renders transport/coverage/revision/watermark (WLGM-180)", () => {
  const html = WlRenderV3.globalBar(d);
  assert(html.includes("LIVE"), "transport LIVE chip");
  assert(html.includes("FRESH"), "freshness FRESH chip");
  assert(html.includes("3/3"), "coverage numerator/denominator");
  assert(html.includes("#42"), "revision");
  assert(html.includes("2026-08-14T00:00:05Z"), "source watermark");
});

t("KPI counts executions not tasks (WLGM-180)", () => {
  const html = WlRenderV3.kpi(d);
  assert(html.includes("活跃项目"), "active projects card");
  assert(html.includes(">2<"), "2 active executions (exec-1, exec-2)");
  assert(html.includes("等待"), "waiting card");
});

t("project table shows activity/agent/attention/evidence/git (WLGM-180)", () => {
  const html = WlRenderV3.projectTable(d);
  assert(html.includes("WORK-LAB"), "project name");
  assert(html.includes("活跃"), "ACTIVE activity chip");
  assert(html.includes("hermes×1") && html.includes("codex×1"), "agent distribution");
  assert(html.includes("等待批准"), "attention state");
  assert(html.includes("本地=远端"), "git match state");
  assert(html.includes("wl-proj-row"), "clickable rows");
});

t("project table shows working areas (WLGM-180)", () => {
  // workingAreas is aggregated by the backend snapshot projection (single
  // projection, WLGM-150); normalizeV3 passes it through.
  const snap = { schemaVersion: "workflow/snapshot/v3", revision: 1,
    projects: [{ projectId: "p", displayName: "P", activityState: "ACTIVE", workingAreas: ["10-workflow/workflow-assistance"] }],
    executions: [{ executionId: "e1", agent: "hermes", anchorProjectId: "p", state: "RUNNING", workingArea: "10-workflow/workflow-assistance" }],
    tokenSummary: {} };
  const s = WlApi.normalizeV3(snap);
  const html = WlRenderV3.projectTable(s);
  assert(html.includes("10-workflow/workflow-assistance"), "working area chip");
  assert(html.includes("Working areas"), "working areas column header");
});

t("governance drift view: known data renders, unknown never fabricates (WLGM-180 §7)", () => {
  const snap = { schemaVersion: "workflow/snapshot/v3", revision: 1, projects: [], executions: [],
    governance: { state: "DRIFT", families: {
      rules: { state: "DRIFT", current: 12, drift: 1 },
      skills: { state: "CLEAN", current: 13, drift: 0 },
      memory: { state: "UNKNOWN", current: null, drift: null },
      adapters: { state: "CLEAN", current: 4, drift: 0 },
    } },
    tokenSummary: {} };
  const s = WlApi.normalizeV3(snap);
  const html = WlRenderV3.governanceDrift(s);
  assert(html.includes("Rules"), "rules family");
  assert(html.includes("漂移"), "DRIFT chip");
  assert(html.includes("当前 12 / 漂移 1"), "rules counts");
  assert(html.includes("一致"), "CLEAN chip");
  const unknown = WlRenderV3.governanceDrift(WlApi.normalizeV3({ schemaVersion: "workflow/snapshot/v3", revision: 1, projects: [], executions: [], tokenSummary: {} }));
  assert(unknown.includes("UNKNOWN"), "unknown governance");
  assert(!unknown.includes("当前 0"), "no fabricated zero counts");
});

t("executions table shows state/quality/transport/evidence level (WLGM-180)", () => {
  const html = WlRenderV3.executionsTable(d);
  assert(html.includes("exec-1"), "execution id");
  assert(html.includes("hermes"), "agent");
  assert(html.includes("L"), "evidence level chip");
  assert(html.includes("SOURCE_REPORTED"), "state quality");
});

t("token/CI section: unknown tokens are never padded to zero (WLGM-180)", () => {
  const d2 = WlApi.normalizeV3({
    schemaVersion: "workflow/snapshot/v3", revision: 1, projects: [], executions: [],
    tokenSummary: { inputTokens: null, outputTokens: null, totalTokens: null, costQuality: "UNKNOWN" },
  });
  const html = WlRenderV3.tokenCi(d2);
  assert(html.includes("未知"), "null tokens shown as 未知, not 0");
  const htmlFull = WlRenderV3.tokenCi(d);
  assert(htmlFull.includes("120000"), "real tokens shown");
  assert(htmlFull.includes("通过"), "CI success chip");
});

t("per-project detail (WLGM-190)", () => {
  const html = WlRenderV3.projectDetail(d, "work-lab");
  assert(html.includes("项目详情"), "detail title");
  assert(html.includes("等待批准"), "attention in detail");
  assert(html.includes("exec-1"), "execution in detail");
  assert(html.includes("hermes-run-1"), "source ref in detail");
  assert(html.includes("RESOLVED"), "identity state");
});

t("per-project detail shows visited/timeline/lost/conflict (WLGM-190)", () => {
  const snap = { schemaVersion: "workflow/snapshot/v3", revision: 1,
    projects: [{ projectId: "p", displayName: "P", activityState: "ACTIVE" }],
    executions: [{
      executionId: "e1", agent: "codex", anchorProjectId: "p", state: "LOST", evidenceLevel: "D",
      visitedRepositories: [{ repositoryId: "other-repo" }],
      timeline: [{ state: "RUNNING", at: "t0" }, { state: "LOST", at: "t1" }],
      lostReason: "heartbeat expired 60s",
      conflicts: ["weak-evidence-running:src-x"],
    }],
    tokenSummary: {} };
  const s = WlApi.normalizeV3(snap);
  const html = WlRenderV3.projectDetail(s, "p");
  assert(html.includes("other-repo"), "visited repository");
  assert(html.includes("RUNNING"), "timeline state");
  assert(html.includes("heartbeat expired 60s"), "LOST reason");
  assert(html.includes("证据冲突"), "conflict marker");
  assert(html.includes("失联"), "LOST chip");
});

t("compact view (WLGM-200)", () => {
  const html = WlRenderV3.compact(d);
  assert(html.includes("传输"), "transport in compact");
  assert(html.includes("覆盖"), "coverage in compact");
  assert(html.includes("WORK-LAB"), "project in compact");
  assert(html.includes("等待"), "waiting counts");
  assert(html.includes("最近强证据"), "last strong evidence");
});

t("unknown surface never claims LIVE", () => {
  const empty = WlApi.normalizeV3({ schemaVersion: "workflow/snapshot/v3", revision: 0, projects: [], executions: [], tokenSummary: {} });
  const html = WlRenderV3.projectTable(empty);
  assert(html.includes("暂无已批准项目"), "no fabricated projects");
  const bar = WlRenderV3.globalBar(empty);
  assert(!bar.includes("wl-chip running"), "transport not LIVE when unknown");
});

/* run() contract for tests/run_all_tests.js */
let ran = 0;
const _t = t;
t = function (name, fn) { ran += 1; _t(name, fn); };

function run() {
  return { pass: ran - failures, fail: failures };
}

if (require.main === module) {
  console.log("\n==== WORK-LAB Observer v3 render contract tests ====");
  console.log("TOTAL: " + (ran - failures) + " passed, " + failures + " failed");
  process.exit(failures ? 1 : 0);
}

module.exports = { run };
