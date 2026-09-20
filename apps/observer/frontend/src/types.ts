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
  sources?: { evidenceKind?: string; [k: string]: unknown }[]
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
}
