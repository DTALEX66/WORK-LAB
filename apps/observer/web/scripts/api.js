/* WORK-LAB Observer — api.js
   Data acquisition. Modes:
     - SNAPSHOT (bundled fallback): uses assets/live-snapshot.json only after
       the live GET endpoint is unavailable.
     - FIXTURE (explicit static/open): uses the inline copy of
       fixtures/cross-project-active-mixed.json. High-visibility amber tag,
       never disguised as LIVE.
     - LIVE (discovered): GET-only fetch from a validated loopback
       /api/v1/snapshot endpoint (v3). The frontend NEVER writes.
   Non-GET methods are rejected client-side as a negative control.
   Unknown fields are ignored (forward compatible) — we only read known keys. */

const WlApi = (function () {
  "use strict";

  /* Inline copy of fixtures/cross-project-active-mixed.json (authoritative fixture).
     Values: inputTokens 64391 / outputTokens 26821 / cacheReadTokens 39960 must be
     kept semantically separate; $4.29 is an API estimate; subscriptionUsage is
     not-metered. */
  const FIXTURE = {
    schemaVersion: "work-lab/observer-projection/v2",
    mode: "FIXTURE",
    generatedAt: "2026-08-07T14:30:00+08:00",
    window: { from: "2026-08-01T00:00:00+08:00", to: "2026-08-07T14:30:00+08:00", timezone: "Asia/Shanghai" },
    freshness: { state: "fresh", ageSeconds: 12, lastGoodAt: "2026-08-07T14:29:48+08:00" },
    summary: {
      registeredProjects: 4, activeProjects: 3,
      tasks: { running: 7, waiting: 3, blocked: 2, failed: 0, completed: 28, unknown: 0 },
    },
    projects: [
      {
        projectId: "cognitive-loop-os", displayName: "Cognitive-Loop-OS",
        repository: "cognitive-loop-os/core", agentPlatform: "HERMES",
        task: "Kernel audit / Gate C", state: "waiting_external", stage: "等待 CI",
        durationSeconds: 14880, blockerSummary: "exact-SHA CI 已排队，暂无 job",
        branch: "main", headSha: "a1b2c3d", ciState: "QUEUED_NO_JOB",
        lastEventAt: "2026-08-07T14:29:48+08:00",
        quality: { evidenceCompleteness: "complete", dataQuality: "exact", freshness: "fresh", sourceRef: "github-actions-cognitive-loop-os" },
      },
      {
        projectId: "work-lab", displayName: "WORK-LAB",
        repository: "DTALEX66/WORK-LAB", agentPlatform: "CODEX",
        task: "Observer projection", state: "running", stage: "本地 Gate",
        durationSeconds: 1080, blockerSummary: null,
        branch: "main", headSha: "d4e5f6a", ciState: "LOCAL_RUNNING",
        lastEventAt: "2026-08-07T14:29:52+08:00",
        quality: { evidenceCompleteness: "complete", dataQuality: "exact", freshness: "fresh", sourceRef: "task-ledger-work-lab" },
      },
      {
        projectId: "automation-sandbox", displayName: "Automation Sandbox",
        repository: "sandbox/ui-runtime", agentPlatform: "Cursor",
        task: "UI runtime integration", state: "blocked", stage: "证据不足",
        durationSeconds: 2520, blockerSummary: "缺少视觉回归证据",
        branch: "feature/ui", headSha: "b7c8d9e", ciState: "BLOCKED_LOCAL",
        lastEventAt: "2026-08-07T14:29:38+08:00",
        quality: { evidenceCompleteness: "partial", dataQuality: "deduplicated", freshness: "fresh", sourceRef: "sandbox-runtime" },
      },
      {
        projectId: "client-project-a", displayName: "Client Project A",
        repository: "client-a/app", agentPlatform: "WorkBuddy",
        task: null, state: "idle", stage: "空闲",
        durationSeconds: null, blockerSummary: null,
        branch: "main", headSha: "c3d4e5f", ciState: "PASSED",
        lastEventAt: "2026-08-07T12:30:00+08:00",
        quality: { evidenceCompleteness: "partial", dataQuality: "stale", freshness: "delayed", sourceRef: "client-project-a-export" },
      },
    ],
    primaryBlocker: {
      projectId: "cognitive-loop-os",
      title: "exact-SHA CI 已排队，暂无 job",
      state: "QUEUED_NO_JOB", durationSeconds: 14880,
      lastObservedAt: "2026-08-07T14:29:48+08:00",
      impact: "阻塞 Kernel audit / Gate C 的远端证据，不阻塞无关本地任务",
      nextCondition: "GitHub 分配 job 或 watcher 到达下一检查时间",
      quality: { evidenceCompleteness: "complete", dataQuality: "exact", freshness: "fresh", sourceRef: "github-actions-cognitive-loop-os" },
    },
    usage: {
      inputTokens: 64391, outputTokens: 26821, reasoningTokens: null,
      cacheReadTokens: 39960, cacheWriteTokens: null,
      cost: { amount: 4.29, currency: "USD", status: "estimated", billingType: "mixed", sourceRef: "pricing-catalog-fixture" },
      subscriptionUsage: "not-metered",
      series: [
        { projectId: "work-lab", points: [
          { bucket: "2026-08-01T00:00:00+08:00", inputTokens: 23000, outputTokens: 9200 },
          { bucket: "2026-08-02T00:00:00+08:00", inputTokens: 28000, outputTokens: 11000 },
          { bucket: "2026-08-03T00:00:00+08:00", inputTokens: 32000, outputTokens: 12800 },
          { bucket: "2026-08-04T00:00:00+08:00", inputTokens: 26000, outputTokens: 10300 },
          { bucket: "2026-08-05T00:00:00+08:00", inputTokens: 22000, outputTokens: 8800 },
          { bucket: "2026-08-06T00:00:00+08:00", inputTokens: 28000, outputTokens: 11200 },
          { bucket: "2026-08-07T00:00:00+08:00", inputTokens: 37000, outputTokens: 14800 },
        ]},
        { projectId: "cognitive-loop-os", points: [
          { bucket: "2026-08-01T00:00:00+08:00", inputTokens: 14000, outputTokens: 5900 },
          { bucket: "2026-08-02T00:00:00+08:00", inputTokens: 18000, outputTokens: 7200 },
          { bucket: "2026-08-03T00:00:00+08:00", inputTokens: 22000, outputTokens: 8800 },
          { bucket: "2026-08-04T00:00:00+08:00", inputTokens: 15000, outputTokens: 6100 },
          { bucket: "2026-08-05T00:00:00+08:00", inputTokens: 17000, outputTokens: 6800 },
          { bucket: "2026-08-06T00:00:00+08:00", inputTokens: 18000, outputTokens: 7200 },
          { bucket: "2026-08-07T00:00:00+08:00", inputTokens: 27000, outputTokens: 10800 },
        ]},
        { projectId: "automation-sandbox", points: [
          { bucket: "2026-08-01T00:00:00+08:00", inputTokens: 6000, outputTokens: 2400 },
          { bucket: "2026-08-02T00:00:00+08:00", inputTokens: 9000, outputTokens: 3600 },
          { bucket: "2026-08-03T00:00:00+08:00", inputTokens: 13000, outputTokens: 5200 },
          { bucket: "2026-08-04T00:00:00+08:00", inputTokens: 8000, outputTokens: 3200 },
          { bucket: "2026-08-05T00:00:00+08:00", inputTokens: 6000, outputTokens: 2400 },
          { bucket: "2026-08-06T00:00:00+08:00", inputTokens: 5000, outputTokens: 2000 },
          { bucket: "2026-08-07T00:00:00+08:00", inputTokens: 14000, outputTokens: 5600 },
        ]},
        { projectId: "client-project-a", points: [
          { bucket: "2026-08-01T00:00:00+08:00", inputTokens: 1000, outputTokens: 400 },
          { bucket: "2026-08-02T00:00:00+08:00", inputTokens: 1500, outputTokens: 600 },
          { bucket: "2026-08-03T00:00:00+08:00", inputTokens: 2500, outputTokens: 1000 },
          { bucket: "2026-08-04T00:00:00+08:00", inputTokens: 1200, outputTokens: 480 },
          { bucket: "2026-08-05T00:00:00+08:00", inputTokens: 900, outputTokens: 360 },
          { bucket: "2026-08-06T00:00:00+08:00", inputTokens: 1200, outputTokens: 480 },
          { bucket: "2026-08-07T00:00:00+08:00", inputTokens: 2500, outputTokens: 1000 },
        ]},
      ],
      quality: { evidenceCompleteness: "partial", dataQuality: "deduplicated", freshness: "fresh", sourceRef: "usage-projection-fixture" },
    },
    ci: {
      exactShaBound: 3, exactShaRequired: 4, queuedNoJob: 1, running: 1, passed: 1, failed: 0, unknown: 1,
      quality: { evidenceCompleteness: "partial", dataQuality: "exact", freshness: "fresh", sourceRef: "ci-projection-fixture" },
    },
    governance: {
      rules: { current: 12, drift: 1, quarantined: 0, conflicts: 0, stale: 0 },
      skills: { current: 13, drift: 1, quarantined: 1, conflicts: 0, stale: 0 },
      adapters: { current: 4, drift: 0, quarantined: 1, conflicts: 1, stale: 0 },
      memoryContext: { current: 8, drift: 0, quarantined: 2, conflicts: 0, stale: 1 },
    },
    quality: {
      sourceCoverage: { numerator: 11, denominator: 14, scope: "registered-project-required-sources" },
      evidenceCompleteness: "partial", freshness: "fresh",
      unknown: 2, malformed: 0, dropped: 0, duplicate: 3,
      projectionLagMs: 180, lastGoodAt: "2026-08-07T14:29:48+08:00",
    },
    sourceRefs: [
      { id: "task-ledger-work-lab", kind: "task-ledger", authority: "runtime", observedAt: "2026-08-07T14:29:52+08:00" },
      { id: "github-actions-cognitive-loop-os", kind: "github-actions", authority: "official", observedAt: "2026-08-07T14:29:48+08:00" },
      { id: "usage-projection-fixture", kind: "fixture", authority: "derived", observedAt: "2026-08-07T14:29:48+08:00" },
    ],
  };

  /* WLGM-150: the ONLY canonical projection endpoint is GET /api/v1/snapshot
     (schema workflow/snapshot/v3). Loopback, GET, no-store, strict origin. */
  function snapshotV3Endpoint() {
    if (typeof window === "undefined") return "/api/v1/snapshot";
    const raw = new URLSearchParams(window.location.search).get("api");
    if (raw) {
      const parsed = new URL(raw);
      const authorityStart = raw.indexOf("//") + 2;
      const authorityEnd = raw.indexOf("/", authorityStart);
      const hasUserInfo = authorityStart > 1 && raw.slice(authorityStart, authorityEnd < 0 ? raw.length : authorityEnd).includes("@");
      const loopback = parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1" || parsed.hostname === "::1" || parsed.hostname === "[::1]";
      if (parsed.protocol !== "http:" || !loopback || hasUserInfo || parsed.pathname !== "/api/v1/snapshot" || parsed.search || parsed.hash) {
        throw new Error("Snapshot endpoint is outside the declared loopback read-only boundary");
      }
      return parsed.toString();
    }
    // Control Tower default: the local WORK-LAB sidecar projection API
    // (loopback, GET-only). Same boundary as an explicit ?api= loopback URL.
    return "http://127.0.0.1:61867/api/v1/snapshot";
  }

  /* WLGM-150: single projection mapping (v3 snapshot -> render surface).
     Implemented once, here, in the client. Strict null-vs-zero: unknown token
     values stay null; observed counters stay 0/positive. */
  function normalizeV3(snapshot) {
    const projects = Array.isArray(snapshot.projects) ? snapshot.projects : [];
    const executions = Array.isArray(snapshot.executions && snapshot.executions[0])
      ? snapshot.executions[0]
      : (Array.isArray(snapshot.executions) ? snapshot.executions : []);
    const activeProjects = projects.filter((p) => p.activityState === "ACTIVE").length;
    const perProject = new Map();
    projects.forEach((p) => {
      perProject.set(p.projectId, {
        projectId: p.projectId,
        displayName: p.displayName || p.projectId,
        agentPlatform: p.agentPlatform || null,
        activityState: p.activityState || "UNKNOWN",
        state: String(p.activityState || "UNKNOWN").toLowerCase(),
        attentionState: p.attentionState || "NONE",
        identityState: p.identityState || "UNRESOLVED",
        activeExecutionCount: p.activeExecutionCount == null ? null : p.activeExecutionCount,
        workingAreas: Array.isArray(p.workingAreas) ? p.workingAreas : [],
        visibility: p.visibility || "UNKNOWN",
        quality: p.quality || "UNKNOWN",
        lastStrongEvidenceAt: p.lastStrongEvidenceAt || null,
        git: p.git || null,
        token: p.token || null,
        executionIds: p.executionIds || [],
        sourceRefs: p.sourceRefs || [],
      });
    });
    executions.forEach((e) => {
      const entry = perProject.get(e.anchorProjectId);
      // Project state is the PROJECT activityState; execution state is separate.
      // Only backfill the agent platform (agent distribution is aggregated from
      // executions by the v3 renderer).
      if (entry && !entry.agentPlatform) {
        entry.agentPlatform = String(e.agent || "UNKNOWN").toUpperCase();
      }
    });
    const usageSummary = snapshot.tokenSummary || {};
    // P0-4: LIVE only when the backend evidence declares transportState=LIVE
    // (live_gate.py full-condition verdict). STALE/DELAYED/unknown must never
    // render as LIVE.
    const transport = snapshot.transport || { transportState: "UNKNOWN", freshnessState: "UNKNOWN" };
    // v3 has one authority for online state: the backend live-gate transport
    // verdict. Ignore any extra top-level mode field so it cannot override an
    // OFFLINE/DELAYED transport with a fabricated LIVE claim.
    const declared = String(transport.transportState || "UNKNOWN").toUpperCase();
    const mode = declared === "LIVE" ? "LIVE"
      : ["SNAPSHOT", "FIXTURE", "OFFLINE", "UNKNOWN"].includes(declared) ? declared
      : "UNKNOWN";
    const tokenSummary = {
      inputTokens: usageSummary.inputTokens == null ? null : usageSummary.inputTokens,
      outputTokens: usageSummary.outputTokens == null ? null : usageSummary.outputTokens,
      totalTokens: usageSummary.totalTokens == null ? null : usageSummary.totalTokens,
      costQuality: usageSummary.costQuality || "UNKNOWN",
    };
    return {
      schemaVersion: "work-lab/observer-projection/v2-rendered",
      mode,
      generatedAt: snapshot.generatedAt,
      revision: snapshot.revision,
      sourceWatermark: snapshot.sourceWatermark,
      transport,
      coverage: snapshot.coverage || null,
      governance: snapshot.governance || null,
      summary: {
        registeredProjects: projects.length,
        activeProjects,
        executions: executions.length,
      },
      projects: Array.from(perProject.values()),
      executions,
      // Keep both names during the v2-rendered compatibility window.  The
      // canonical v3 field is tokenSummary; the renderer must not lose real
      // usage merely because the adapter renamed it to usage.
      tokenSummary,
      usage: tokenSummary,
      quality: snapshot.quality || null,
      git: snapshot.git || { localSha: null, remoteSha: null, ciSha: null, matchState: "NO_LOCAL_CLAIM" },
      ci: snapshot.ci || [],
      tasks: snapshot.tasks || {},
      workspace: snapshot.workspace || {},
      sourceRefs: snapshot.sourceRefs || [],
    };
  }

  function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }

  function isValidTimestamp(value) {
    return typeof value === "string" && value.length > 0 && Number.isFinite(Date.parse(value));
  }

  function isLoopbackEventsUrl(url) {
    try {
      const raw = String(url || "");
      const parsed = new URL(raw, typeof window !== "undefined" ? window.location.href : "http://127.0.0.1/");
      const authorityStart = raw.indexOf("//") + 2;
      const authorityEnd = raw.indexOf("/", authorityStart);
      const hasUserInfo = authorityStart > 1 && raw.slice(authorityStart, authorityEnd < 0 ? raw.length : authorityEnd).includes("@");
      const loopback = parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1" || parsed.hostname === "[::1]" || parsed.hostname === "::1";
      return parsed.protocol === "http:"
        && loopback
        && !hasUserInfo
        && parsed.pathname === "/api/v1/events"
        && !parsed.search
        && !parsed.hash;
    } catch (_) {
      return false;
    }
  }

  function validateSnapshotV3(snapshot) {
    if (!isRecord(snapshot) || snapshot.schemaVersion !== "workflow/snapshot/v3") return false;
    if (!Number.isInteger(snapshot.revision) || snapshot.revision < 0) return false;
    if (!isValidTimestamp(snapshot.generatedAt)) return false;
    if (!Array.isArray(snapshot.projects) || !Array.isArray(snapshot.executions) || !Array.isArray(snapshot.ci)) return false;
    if (!isRecord(snapshot.tasks) || !isRecord(snapshot.tokenSummary) || !isRecord(snapshot.transport) || !isRecord(snapshot.coverage)) return false;
    const transportState = String(snapshot.transport.transportState || "").toUpperCase();
    if (!["LIVE", "DELAYED", "OFFLINE", "UNKNOWN", "CONNECTING"].includes(transportState)) return false;
    if (transportState === "LIVE") {
      const numerator = snapshot.coverage.numerator;
      const denominator = snapshot.coverage.denominator;
      if (snapshot.transport.eventStreamConnected !== true) return false;
      if (!Number.isInteger(numerator) || !Number.isInteger(denominator) || denominator <= 0 || numerator !== denominator) return false;
      if (!isValidTimestamp(snapshot.transport.connectedSince)) return false;
      if (!isValidTimestamp(snapshot.transport.lastHeartbeatAt)) return false;
      if (!isValidTimestamp(snapshot.transport.writerWatermarkAt)) return false;
      if (!isLoopbackEventsUrl(snapshot.transport.eventsUrl)) return false;
    }
    return true;
  }

  /* GET /api/v1/snapshot (canonical v3); anything else -> throw -> OFFLINE
     (no fixture fallback). */
  async function fetchSnapshot(timeoutMs) {
    const timeout = timeoutMs || 5000;
    const endpoints = [snapshotV3Endpoint()];
    let lastError = null;
    for (const endpoint of endpoints) {
      const ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
      const timer = ctrl ? setTimeout(() => ctrl.abort(), timeout) : null;
      try {
        const res = await fetch(endpoint, {
          method: "GET",
          cache: "no-store",
          headers: { Accept: "application/json" },
          signal: ctrl ? ctrl.signal : undefined,
        });
        if (!res.ok) {
          throw new Error("GET " + endpoint + " -> " + res.status);
        }
        const data = await res.json();
        if (validateSnapshotV3(data)) {
          const normalized = normalizeV3(data);
          // P0-4: eventsUrl fallback — derive from the endpoint origin when the
          // backend transport does not advertise it.
          if (normalized.transport && !normalized.transport.eventsUrl) {
            const base = new URL(endpoint, typeof window !== "undefined" ? window.location.href : "http://127.0.0.1/");
            normalized.transport.eventsUrl = base.origin + "/api/v1/events";
          }
          return { ok: true, mode: normalized.mode, data: normalized, source: endpoint };
        }
        throw new Error("GET " + endpoint + " returned an invalid or retired snapshot contract");
      } catch (err) {
        lastError = err && err.name === "AbortError"
          ? new Error("GET " + endpoint + " timed out")
          : err;
      } finally {
        if (timer) clearTimeout(timer);
      }
    }
    throw lastError || new Error("No Observer snapshot endpoint available");
  }

  function fetchDashboard() {
    // Retired (R2 third batch): legacy callers must fail closed instead of
    // silently receiving a v3 response through an unvalidated path.
    throw new Error("Legacy dashboard endpoint retired; use fetchSnapshot");
  }

  /* Client-side non-GET negative control. Returns a rejected promise for any
     method other than GET. (No server write is ever attempted.) */
  function rejectNonGet(method) {
    const m = String(method || "").toUpperCase();
    if (m !== "GET") {
      return Promise.reject(new Error("405 Method Not Allowed (client read-only): " + m));
    }
    return Promise.resolve();
  }

  /* Subscribe to the Workflow-owned loopback SSE endpoint advertised by the
     read-only v3 snapshot projection. EventSource owns reconnect and forwards
     Last-Event-ID automatically; Observer only reacts by re-reading projection. */
  function subscribeEvents(url, handlers) {
    if (typeof EventSource === "undefined") {
      throw new Error("EventSource is unavailable");
    }
    const raw = String(url);
    if (!isLoopbackEventsUrl(raw)) {
      throw new Error("SSE endpoint is outside the declared loopback read-only boundary");
    }
    const parsed = new URL(raw, typeof window !== "undefined" ? window.location.href : "http://127.0.0.1/");
    const source = new EventSource(parsed.toString());
    // P0-4: the backend sends NAMED events (event: observed / heartbeat /
    // resync_required); named events must be bound with addEventListener.
    // onmessage only receives anonymous frames — keep it as a fallback.
    const dispatch = (event, eventName) => {
      let payload = null;
      try {
        payload = JSON.parse(event.data);
      } catch (error) {
        if (handlers && typeof handlers.onProtocolError === "function") {
          handlers.onProtocolError(error, eventName, event.lastEventId || null);
        }
        return;
      }
      if (handlers && typeof handlers.onEvent === "function") {
        handlers.onEvent(payload, event.lastEventId || null, eventName);
      }
    };
    ["snapshot", "observed", "heartbeat", "resync_required"].forEach((name) => {
      source.addEventListener(name, (event) => dispatch(event, name));
    });
    source.addEventListener("message", (event) => dispatch(event, "message"));
    source.onerror = () => {
      if (handlers && typeof handlers.onError === "function") handlers.onError();
    };
    source.onopen = () => {
      if (handlers && typeof handlers.onOpen === "function") handlers.onOpen();
    };
    return source;
  }

  return {
    FIXTURE,
    snapshotV3Endpoint,
    fetchDashboard,
    fetchSnapshot,
    normalizeV3,
    validateSnapshotV3,
    rejectNonGet,
    subscribeEvents,
  };
})();

if (typeof module !== "undefined" && module.exports) {
  module.exports = { WlApi };
}
