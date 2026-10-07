// WORK-LAB Observer — typed model of the REAL v3 snapshot
// (packages/client-neutral-core/scripts/snapshot_api.py::build_snapshot,
//  authoritative in tests/workflow-assistance/test_sidecar_v3_snapshot.py).
//
// The legacy front rendered a PHANTOM schema (agents[]/models[]/cost[]/
// resources{cpu,mem}/services[]/memory[]). None of those exist in v3. This
// file mirrors ONLY the fields build_snapshot actually emits. U07 (taskpack
// 20260919) front-truth discipline: no frontend price/FX/quota — the only cost
// truth the back end projects is tokenSummary.costQuality.

export type SchemaVersion = 'workflow/snapshot/v3'

export type TransportState = 'LIVE' | 'DELAYED' | 'OFFLINE' | 'CONNECTING' | 'UNKNOWN'
export type FreshnessState = 'FRESH' | 'STALE' | 'UNKNOWN'
export type GitMatchState = 'MATCH' | 'UNVERIFIED' | 'DRIFT' | 'UNKNOWN'
export type FamilyState = 'CLEAN' | 'DRIFT' | 'UNKNOWN'
export type ProjectActivityState = 'ACTIVE' | 'REGISTERED' | 'IDLE' | 'UNKNOWN'
export type ExecutionState =
  | 'RUNNING' | 'STARTING' | 'WAITING_USER' | 'WAITING_APPROVAL' | 'BLOCKED'
  | 'COMPLETED' | 'FAILED' | 'UNKNOWN'
export type CostQuality = 'EXACT' | 'ESTIMATED' | 'UNKNOWN'

export interface SnapshotTransport {
  transportState: TransportState
  freshnessState: FreshnessState
  connectedSince: string | null
  eventsUrl: string | null
  eventStreamConnected?: boolean
  lastHeartbeatAt?: string | null
  writerWatermarkAt?: string | null
}

export interface SnapshotCoverage {
  numerator: number | null
  denominator: number | null
  scope: string | null
}

export interface GovernanceFamily {
  state: FamilyState
  current: unknown | null
  drift: number | null
}

export interface SnapshotGovernance {
  state: string
  families: {
    rules: GovernanceFamily
    skills: GovernanceFamily
    memory: GovernanceFamily
    adapters: GovernanceFamily
  }
}

export interface ProjectGit {
  localSha: string | null
  remoteSha: string | null
  matchState: GitMatchState
  branch: string | null
  dirtyCount: number | null
  observedAt: string | null
  quality: string | null
  freshness: string | null
  sourceRef: string | null
}

export interface ProjectToken {
  inputTokens: number | null
  outputTokens: number | null
  totalTokens: number | null
  costQuality: CostQuality
}

export interface CiRun {
  runId: string | null
  workflow: string | null
  headSha: string | null
  status: string | null
  conclusion: string | null
  sourceRef: string | null
}

export interface Project {
  projectId: string
  displayName: string | null
  agentPlatform: string | null
  identityState: string
  activityState: ProjectActivityState
  attentionState: string
  activeExecutionCount: number
  workingAreas: string[]
  visibility: string
  quality: string
  lastStrongEvidenceAt: string | null
  repositories: unknown[]
  git: ProjectGit
  token: ProjectToken
  ci: CiRun[]
  executionIds: string[]
  sourceRefs: string[]
}

export interface Execution {
  executionId: string
  anchorProjectId: string | null
  workingArea: string | null
  state: ExecutionState
  stateQuality: string
  agent: string | null
  sessionId: string | null
  sourceRef: string | null
}

// P1-02: one task record projected from the canonical store by the unique Snapshot API
// (packages/client-neutral-core/scripts/snapshot_api.py::project_task_record). checkpoint VALUES never
// cross the read-only boundary — the projection carries whether a checkpoint exists, its key names,
// and a digest that moves when it changes.
export interface TaskRecord {
  taskId: string | null
  projectId: string | null
  status: string | null
  createdAt: string | null
  updatedAt: string | null
  leaseHolder: string | null
  leaseExpiresAt: string | null
  fencingToken: number | null
  checkpointPresent: boolean
  checkpointKeys: string[]
  checkpointDigest: string | null
}

// P1-03 / F1: the seven-layer capability ladder, projected by
// packages/client-neutral-core/scripts/adapter_capability_projection.py. Each layer is its own claim:
// MET requires a named source, and anything unprobed arrives as NOT_PROBED carrying the reason for the
// gap. A card may not promote a layer because a neighbouring layer succeeded.
export type CapabilityLayer =
  | 'REGISTERED' | 'INSTALLED' | 'LOADED_CONNECTED' | 'QUALIFIED'
  | 'ENABLED_FOR_TASK' | 'NATIVE_PROJECTION' | 'OBSERVED_IN_EXECUTION'

export interface CapabilityLayerState {
  layer: CapabilityLayer
  state: 'MET' | 'NOT_PROBED' | 'NOT_SUPPORTED'
  evidenceLevel: 'NO_EVIDENCE' | 'SIMULATED' | 'SYNTHETIC' | 'INTEGRATED' | 'REAL'
  source: string | null
  reason: string
}

// P1-03 open item, the verb dimension: the seven layers say what a CLIENT is; they cannot say which verbs of
// the adapter interface the client actually answers. This orthogonal row set is projected by
// packages/client-neutral-core/scripts/adapter_capability_projection.py from the read-only probe record in
// docs/audits/EXECUTOR_LIVE_PROBE_2026-10-08.json#verbProbe. One row per contract verb, each either MET from
// a named read-only call, NOT_SUPPORTED from a named declaration, or NOT_PROBED carrying the concrete
// refusal reason. `attempted` is what separates two very different NOT_PROBED statements — the probe ran
// the call and the answer was not creditable (attempted=true) versus the probe refused to run it at all
// (attempted=false). A verb row never promotes a layer.
//
// On the card the whole dimension is OPTIONAL: an absent probe record emits NO `verbEvidence` key at all
// rather than an empty list, because an empty list would render as "declares nothing" where the truth is
// "I did not look". The Observer renders that absence as the named source gap, never as zero rows.
export type VerbEvidenceState = 'MET' | 'NOT_PROBED' | 'NOT_SUPPORTED'
export type VerbEvidenceLevel = 'NO_EVIDENCE' | 'SIMULATED' | 'SYNTHETIC' | 'INTEGRATED' | 'REAL'

export interface AdapterVerbEvidenceRow {
  verb: string
  state: VerbEvidenceState
  evidenceLevel: VerbEvidenceLevel
  source: string | null
  reason: string | null
  attempted: boolean
  probedAt?: string | null
  command?: string[]
  exitCode?: number | null
  outputDigest?: string
  outputLines?: number
  detail?: string
  basis?: string
  declaredIn?: Record<string, boolean>
  declaresDrift?: string
  entryResolution?: string
  checkedPaths?: string[]
  ref?: string
}

export interface AdapterCapabilityCard {
  clientId: string
  displayName: string
  supportLevel: string
  declaredOperations: string[]
  matrixOperations: string[]
  operationsDrift: boolean
  registryStatus: string
  writePolicy: string
  risk: string
  runtimeAdapter: string | null
  configOwnershipDefault: { layer?: string, mode?: string, preserve_unknown?: boolean } | null
  clientNote?: string | null
  declaredVersion: string | null
  versionReadbackMethod: string | null
  versionObservedAt: string | null
  versionSource: string | null
  detectionMode: string | null
  detectionEvidenceState: string
  protocolConformance: Record<string, string>
  observedAt: string | null
  layers: CapabilityLayerState[]
  nativeStatus: 'NOT_IMPLEMENTED' | 'NOT_PROBED' | 'NATIVELY_VERIFIED'
  // Optional per-verb dimension (see AdapterVerbEvidenceRow). ABSENT (no key) is the probe-record gap and
  // renders as such; it is never synthesised into an empty list.
  verbEvidence?: AdapterVerbEvidenceRow[]
  verbEvidenceCounts?: Partial<Record<VerbEvidenceState, number>> & Record<string, number>
  verbEvidenceProbedAt?: string | null
}

export interface TokenSummary {
  inputTokens: number | null
  outputTokens: number | null
  totalTokens: number | null
  costQuality: CostQuality
}

export interface TopGit {
  localSha: string | null
  remoteSha: string | null
  ciSha: string | null
  matchState: GitMatchState
}

export interface WorkspaceEvidence {
  plan?: {
    status?: string
    counts?: Record<string, number>
    tasks?: { taskId?: string; [k: string]: unknown }[]
    approvals?: { state?: string; [k: string]: unknown }[]
  }
  governance?: { contracts?: number; [k: string]: unknown }
  history?: { totalErrors?: number; recentErrors?: { errorId?: string; [k: string]: unknown }[]; [k: string]: unknown }
  // packages/client-neutral-core/scripts/workspace_evidence.py appends one row per loaded surface:
  // {path, evidenceKind, loadedAt} (+ generatedAt for the JSON projections). `path` is a repository-RELATIVE
  // POSIX path — the projection has no project root to absolutize it with, which is exactly why an
  // evidence-range read of it comes back refused rather than empty.
  sources?: { evidenceKind?: string; path?: string; loadedAt?: string; generatedAt?: string; [k: string]: unknown }[]
  [k: string]: unknown
}

// S31/32 (taskpack 20260919): read-only software installation-identity
// projection. The Observer projects this (U17/P0-07 contract) when the backend
// carries it; when absent the panel shows UNKNOWN, NEVER a fabricated "Healthy".
// It is NOT a second Update Authority — no relocation / delete / act-on.
export type SoftwareLocationStatus =
  | 'NOT_INSTALLED' | 'SINGLE_VERIFIED' | 'SINGLE_UNVERIFIED'
  | 'LOCATION_DRIFT' | 'DUAL_INSTALLATION' | 'MISSING_EXPECTED_INSTALL'
  | 'RELOCATION_REQUESTED' | 'OS_MANAGED' | 'UNKNOWN'

export interface SoftwareIdentity {
  softwareId: string
  displayName: string | null
  installRoot: string | null
  executableRealpath: string | null
  discoveredVersion: string | null
  releaseChannel: string | null
  updateAvailable: boolean | null
  duplicateInstallation: boolean
  expectedLocation: string | null
  observedLocation: string | null
  locationStatus: SoftwareLocationStatus
  lastVerified: string | null
  discoverySource: string | null
}

export interface SnapshotV3 {
  schemaVersion: SchemaVersion
  revision: number
  generatedAt: string | null
  sourceWatermark: string | null
  transport: SnapshotTransport
  coverage: SnapshotCoverage
  governance: SnapshotGovernance
  workspace: WorkspaceEvidence
  projects: Project[]
  executions: Execution[]
  tasks: Record<string, number>
  tokenSummary: TokenSummary
  git: TopGit
  ci: CiRun[]
  sourceRefs: string[]
  // Optional install-identity projection (U17/P0-07) when the backend carries
  // it. Absent => the software panel shows UNKNOWN (never a fake Healthy).
  software?: SoftwareIdentity[]
  // P1-02 deep-link target records. ABSENT means the producer did not query the task table, which is a
  // different statement from an empty list (queried, nothing there). The Work lane renders the first as
  // 后端未提供 and only the second as 无任务 — never a padded 0.
  taskRecords?: TaskRecord[]
  // P1-03: per-client capability cards with the seven-layer ladder. ABSENT (producer could not read the
  // declared sources) is reported as a source gap, not as "no adapters".
  adapterCapabilities?: AdapterCapabilityCard[]
}
