// GENERATED FILE — do not edit by hand.
// Source of truth: JSON Schema contracts referenced by the catalog
// (.project/governance/contracts/contract-catalog.json).
// Regenerate: python scripts/ci/generate_contract_types.py
// Each `// @contract <id>` marker is consumed by
// scripts/ci/verify_contract_ssot.py to prove generated == catalog.

export type ContractId =
  "module-profile"
  | "source-ledger"
  | "capability-conformance"
  | "task-card"
  | "runtime-lock"
  | "domain-pack"
  | "evidence-envelope"
  | "release-manifest"
  | "adapter-capability"
  | "action-plan"
  | "task-ledger-event"
  | "rule-asset"
  | "skill-package"
  | "growth-candidate"
  | "project-profile"
  | "gate-registry"
  | "gate-plan"
  | "blocker"
  | "ci-observation"
  | "evidence-manifest"
  | "model-policy"
  | "memory-record"
  | "rule-drift"
  | "platform-identity"
  | "config-ownership"
  | "observer-event"
  | "observer-pricing"
  | "data-quality"
  | "dashboard-projection"
  | "global-agent-policy"
  | "policy-projection-contract"
  | "policy-projection-loss-report"
  | "archive-manifest"
  | "software-installation-identity"
  | "software-update-preflight"
  | "execution-parallel-dispatch"
  | "software-update-postflight";

// @contract module-profile
// schema: .project/governance/contracts/module-profile.schema.json
export type ModuleProfile = {
    schemaVersion: unknown,
    id: string,
    path: string,
    owner: string,
    role: string,
    releasePrefix: string,
    dependsOn: string[],
    evidencePath?: string,
    externalMutationDefault?: unknown
  };

// @contract source-ledger
// schema: .project/governance/contracts/source-ledger.schema.json
export type SourceLedger = {
    "$schema"?: string,
    schemaVersion: unknown,
    ledgerVersion: unknown,
    scope: unknown,
    entries: unknown[]
  };

// @contract capability-conformance
// schema: .project/governance/contracts/capability-conformance.schema.json
export type CapabilityConformance = {
    "$schema"?: string,
    schemaVersion: unknown,
    scope: unknown,
    acp: unknown,
    skills: unknown,
    mcp: unknown
  };

// @contract task-card
// schema: packages/contracts/schemas/workflow/task-card.schema.json
export type TaskCard = {
    schema_version: unknown,
    id: string,
    title: string,
    scope: string,
    action: string,
    acceptance: string,
    phase?: string,
    priority?: ["P0", "P1", "P2", "P3"],
    constraints?: string[]
  };

// @contract runtime-lock
// schema: .project/governance/contracts/runtime-lock.schema.json
export type RuntimeLock = {
    schemaVersion: unknown,
    runId: string,
    root: Record<string, unknown>,
    modules: Record<string, unknown>
  };

// @contract domain-pack
// schema: packages/contracts/schemas/workflow/domain-pack.schema.json
export type DomainPack = {
    schema_version: unknown,
    pack_id: string,
    version: string,
    display_name: string,
    description: string,
    capabilities: string[],
    entrypoints: {
    human: string[],
    machine: string[]
  },
    evidence_policy: {
    minimum_level: ["E0", "E1", "E2", "E3", "E4", "E5"],
    required_artifacts: string[]
  },
    safety: {
    approval_required: unknown,
    forbidden_paths: string[],
    redaction_required: unknown
  }
  };

// @contract evidence-envelope
// schema: .project/governance/contracts/evidence-envelope.schema.json
export type EvidenceEnvelope = {
    schemaVersion: unknown,
    taskId: string,
    runId: string,
    status: ["PASS", "FAIL", "BLOCKED", "UNKNOWN"],
    source: string,
    contentBodies?: unknown,
    credentials?: unknown
  };

// @contract release-manifest
// schema: .project/governance/contracts/release-manifest.schema.json
export type ReleaseManifest = {
    schemaVersion: unknown,
    releaseId: string,
    module: string,
    version: string,
    source: {
    repository: string,
    commit: string
  },
    artifacts: Record<string, unknown>[],
    evidence: string[],
    approval: {
    status: ["PENDING", "APPROVED", "REJECTED"],
    scope?: string
  }
  };

// @contract adapter-capability
// schema: packages/contracts/schemas/workflow/client-adapter.schema.json
export type AdapterCapability = {
    schema_version: unknown,
    interface: unknown[],
    entries: Record<string, unknown>[]
  };

// @contract action-plan
// schema: packages/contracts/schemas/workflow/action-plan.schema.json
export type ActionPlan = {
    schema_version: unknown,
    plan_id: string,
    task_id?: string,
    status: ["DRAFT", "WAITING_APPROVAL", "APPROVED", "EXECUTING", "SUCCEEDED", "FAILED", "BLOCKED", "ROLLED_BACK"],
    target: {
    adapter: string,
    operation: string,
    project_root: string
  },
    steps: Record<string, unknown>[],
    approval: {
    approval_required: unknown,
    status: ["PENDING", "APPROVED", "REJECTED"],
    approved_by?: string
  },
    rollback: {
    available: unknown,
    strategy: string,
    artifact?: string
  },
    constraints?: {
    allowed_paths?: string[],
    forbidden_paths?: string[],
    network?: ["none", "explicit"]
  }
  };

// @contract task-ledger-event
// schema: packages/contracts/schemas/workflow/run-event.schema.json
export type TaskLedgerEvent = {
    schema_version: unknown,
    event_id: string,
    run_id: string,
    task_id: string,
    phase: ["planning", "approval", "execution", "observation", "delivery", "review", "rollback"],
    status: ["QUEUED", "PLANNING", "WAITING_APPROVAL", "RUNNING", "RETRYING", "PAUSED", "BLOCKED", "REVIEWING", "COMPLETED", "FAILED", "CANCELLED"],
    timestamp: string,
    sequence?: number,
    payload?: {
    adapter?: string,
    operation?: string,
    checkpoint?: string,
    error_code?: string
  }
  };

// @contract rule-asset
// schema: packages/contracts/schemas/workflow/rule-asset.schema.json
export type RuleAsset = {
    schema_version: unknown,
    id: string,
    version: string,
    origin: string,
    scope: ["session", "project", "domain", "client", "global"],
    risk: ["low", "medium", "high", "critical"],
    status: ["candidate", "isolated", "approved", "deployed", "blocked", "retired"],
    packageDigest?: string
  };

// @contract skill-package
// schema: packages/contracts/schemas/workflow/skill-package.schema.json
export type SkillPackage = {
    schema_version: unknown,
    id: string,
    version: string,
    source: string,
    packageDigest: string,
    status: ["candidate", "isolated", "approved", "deployed", "blocked", "retired"],
    risk?: ["low", "medium", "high", "critical"]
  };

// @contract growth-candidate
// schema: packages/contracts/schemas/workflow/growth-candidate.schema.json
export type GrowthCandidate = {
    schema_version: unknown,
    candidateId: string,
    origin: string,
    classification: ["curator", "learn", "manual", "hub", "upstream", "deployment"],
    status: ["discovered", "isolated", "scanned", "evaluated", "candidate", "approved", "blocked", "retired"],
    risk: ["low", "medium", "high", "critical"],
    sourceDigest?: string
  };

// @contract project-profile
// schema: packages/contracts/schemas/workflow/project-profile.schema.json
export type ProjectProfile = {
    schema_version: unknown,
    project: {
    id: string,
    root_policy: ["discover_git_root", "explicit_git_root"],
    windows_native_first: boolean
  },
    configuration: {
    precedence: ["global_defaults", "project_profile", "local_runtime", "environment", "cli"][]
  },
    modules: Record<string, unknown>,
    risk_zones: Record<string, unknown>,
    gates: Record<string, unknown>,
    ci: {
    stable_aggregate_check: string,
    stable_aggregate_job?: string,
    workflow_file?: string,
    workflow_name?: string,
    release_workflow?: string,
    observation_privacy_policy?: string,
    watcher_policy?: Record<string, unknown>,
    exact_sha_required_for: string[],
    outage_blocks: string[]
  }
  };

// @contract gate-registry
// schema: packages/contracts/schemas/workflow/gate-registry.schema.json
export type GateRegistry = {
    schema_version: unknown,
    gate: unknown
  };

// @contract gate-plan
// schema: packages/contracts/schemas/workflow/gate-plan.schema.json
export type GatePlan = {
    schema_version: unknown,
    plan_id: string,
    source_identity: unknown,
    changed_paths: string[],
    required_gates: string[],
    skipped_gates: Record<string, unknown>[],
    risk: ["low", "medium", "high", "critical"],
    delivery_effect: ["none", "commit", "push", "pull_request", "merge", "release"],
    platform_scope: string[],
    plan_digest: unknown,
    generated_at: string
  };

// @contract blocker
// schema: packages/contracts/schemas/workflow/blocker.schema.json
export type Blocker = {
    schema_version: unknown,
    blocker_id: string,
    class: ["CODE_DEFECT", "TEST_FAILURE", "POLICY_VIOLATION", "APPROVAL_REQUIRED", "MISSING_CAPABILITY", "REMOTE_DIVERGENCE", "CI_OUTAGE", "CI_QUEUE_STALLED", "CI_RATE_LIMITED", "FLAKY_GATE", "ENVIRONMENT_UNAVAILABLE"],
    scope: ["task", "batch", "gate", "delivery", "release", "observation"],
    retry_policy: ["never", "once_after_recovery", "retry_after_retry_after", "budgeted_diagnostic"],
    fingerprint: string,
    message: string,
    created_at: string,
    resolved_at?: string | null
  };

// @contract ci-observation
// schema: packages/contracts/schemas/workflow/ci-observation.schema.json
export type CiObservation = {
    schema_version: unknown,
    observation_id: string,
    repository: string,
    commit: string,
    state: ["NOT_REQUESTED", "TRIGGER_EXPECTED", "DISCOVERING", "QUEUED_NO_JOB", "QUEUED_WITH_JOB", "RUNNING", "SUCCEEDED", "FAILED_PRODUCT", "FAILED_INFRASTRUCTURE", "CI_OUTAGE", "PLATFORM_OUTAGE", "CI_RATE_LIMITED", "TIMED_OUT", "CANCELLED", "STALE", "BLOCKED", "DEFERRED_CI"],
    workflow?: string | null,
    run_id?: number | string | null,
    attempt?: number | null,
    queue_age_seconds?: number | null,
    job_count?: number | null,
    observed_at: string,
    next_observation_at?: string | null,
    retry_budget: number,
    message?: string
  };

// @contract evidence-manifest
// schema: packages/contracts/schemas/workflow/evidence-manifest.schema.json
export type EvidenceManifest = {
    schema_version: unknown,
    manifest_id: string,
    source_identity: unknown,
    plan: {
    digest: unknown,
    base_oid: string,
    head_oid: string
  },
    evidence: Record<string, unknown>[],
    redaction: {
    policy: unknown,
    secrets_stored: unknown
  }
  };

// @contract model-policy
// schema: packages/contracts/schemas/workflow/model-policy.schema.json
export type ModelPolicy = {
    schema_version: unknown,
    policy_id: string,
    task_class: ["planning", "coding", "review", "observer", "design", "recovery"],
    model_class: ["reasoning", "general", "fast", "local", "unknown"],
    selection: ["user-selected", "capability-match", "offline-fixture", "unavailable"],
    context_budget: {
    input_tokens: number,
    output_tokens: number,
    reserved_tokens: number,
    overflow: ["fail-closed", "summarize", "drop-oldest"]
  },
    cost: {
    mode: ["unknown", "estimated", "subscription", "not-metered", "reconciled"],
    currency?: string,
    unit_price_per_million_tokens?: number,
    effective_at?: string,
    source: string
  },
    redaction: {
    prompt_response_bodies: unknown,
    credentials: unknown
  },
    degradation: ["unknown-when-unavailable", "blocked-when-unavailable"]
  };

// @contract memory-record
// schema: packages/contracts/schemas/workflow/memory-record.schema.json
export type MemoryRecord = {
    schema_version: unknown,
    ttlSeconds: number,
    authoritative: boolean,
    memory_id: string,
    layer: ["ephemeral", "session", "project", "domain", "global"],
    kind: ["fact", "preference", "procedure", "candidate", "event"],
    status: ["observed", "proposed", "approved", "blocked", "retired"],
    project_id: string,
    scope?: ["project", "domain", "global"],
    valid_from?: string | null,
    valid_to?: string | null,
    ttl_days?: number | null,
    supersedes?: string | null,
    conflicts_with?: string[] | null,
    last_used_at?: string | null,
    pinned_context?: boolean,
    source_digest: string,
    content_digest: string,
    confidence: ["low", "medium", "high"],
    promotion: ["never", "manual-approval"],
    redaction: {
    prompt_response_bodies: unknown,
    credentials: unknown
  }
  };

// @contract rule-drift
// schema: packages/contracts/schemas/workflow/rule-drift.schema.json
export type RuleDrift = {
    schema_version: unknown,
    drift_id: string,
    rule_id: string,
    baseline_digest: string | null,
    observed_digest: string | null,
    state: ["unchanged", "changed", "missing", "new"],
    severity: ["info", "medium", "high"],
    action: ["report-only", "quarantine", "manual-review"]
  };

// @contract platform-identity
// schema: packages/contracts/schemas/workflow/platform-identity.schema.json
export type PlatformIdentity = {
    schema_version: unknown,
    platform_id: string,
    logical_instance_id: string,
    package_identity: string,
    publisher: string,
    install_channel: ["store", "official-installer", "package-manager", "portable", "source", "unknown"],
    executable_realpath: string,
    binary_digest: string,
    discovered_version: string,
    launcher_id: string,
    launcher_target: string,
    arguments: string[],
    working_directory: string,
    effective_config_root: string,
    profile_id: string,
    user_context: ["current-user", "service-user", "unknown"],
    capabilities: string[],
    evidence_source: string[],
    observed_at: string,
    freshness: ["CURRENT", "STALE", "UNKNOWN"],
    state: ["UNIQUE", "ALIAS_DUPLICATE", "STALE_SHORTCUT", "CONFIG_SPLIT", "VERSION_COLLISION", "DUAL_INSTALLATION", "PROFILE_SPLIT", "IDENTITY_AMBIGUOUS", "UNAVAILABLE"]
  };

// @contract config-ownership
// schema: packages/contracts/schemas/workflow/config-ownership.schema.json
export type ConfigOwnership = {
    schema_version: unknown,
    single_authority: unknown,
    note: string,
    layers: Record<string, unknown>,
    operation_modes: ["MANAGE", "OBSERVE", "IGNORE", "FORBIDDEN"][],
    default_unknown: {
    mode: unknown,
    quarantine: unknown
  },
    adapter_defaults: Record<string, unknown>,
    fields: Record<string, unknown>[],
    rules: Record<string, unknown>
  };

// @contract observer-event
// schema: apps/observer/schemas/observer-event.schema.json
export type ObserverEvent = {
    eventId: string,
    schemaVersion: unknown,
    eventType: string,
    sourceModule: string,
    sourceId?: string,
    projectId?: string,
    taskId?: string,
    taskTitle?: string,
    runId?: string,
    observedAt: string,
    occurredAt?: string,
    originId?: string,
    causationId?: string,
    correlationId?: string,
    contentDigest: string,
    coverage?: ["full", "partial", "unknown"],
    quality: ["source-exact", "deduplicated", "partial", "unknown"],
    usage?: {
    input_tokens: number | null,
    output_tokens: number | null,
    total_tokens: number | null,
    records: number | null,
    observation_state: ["observed", "estimated", "unknown"]
  },
    evidenceRefs?: string[],
    telemetry?: {
    operation?: string,
    provider?: string,
    model?: string,
    input_tokens?: number,
    output_tokens?: number,
    total_tokens?: number,
    reasoning_tokens?: number,
    latency_ms?: number,
    cache_read_tokens?: number,
    cache_write_tokens?: number,
    outcome?: string,
    error_class?: string
  }
  };

// @contract observer-pricing
// schema: apps/observer/schemas/observer-pricing.schema.json
export type ObserverPricing = Record<string, unknown>;

// @contract data-quality
// schema: apps/observer/schemas/data-quality.schema.json
export type DataQuality = {
    quality: ["source-exact", "deduplicated", "partial", "unknown"],
    coverage: ["full", "partial", "unknown"],
    sourceCount: number,
    acceptedCount: number,
    rejectedCount: number,
    reason?: string
  };

// @contract dashboard-projection
// schema: apps/observer/schemas/dashboard-projection.schema.json
export type DashboardProjection = {
    schemaVersion: string,
    mode: ["LIVE", "SNAPSHOT", "FIXTURE", "STALE", "OFFLINE", "UNKNOWN"],
    generatedAt: string,
    window?: {
    from?: string,
    to?: string
  },
    freshness: {
    state: string,
    ageSeconds?: number | null,
    lastGoodAt?: string | null
  },
    summary: {
    registeredProjects: number,
    activeProjects: number,
    tasks?: Record<string, unknown>
  },
    projects: Record<string, unknown>[],
    primaryBlocker?: Record<string, unknown> | null,
    usage: {
    inputTokens?: number | null,
    outputTokens?: number | null,
    reasoningTokens?: number | null,
    cacheReadTokens?: number | null,
    cacheWriteTokens?: number | null,
    cost?: Record<string, unknown>,
    subscriptionUsage?: string | null,
    series?: unknown[],
    quality?: Record<string, unknown>
  },
    ci: {
    exactShaBound?: number,
    exactShaRequired?: number,
    queuedNoJob?: number,
    running?: number,
    passed?: number,
    failed?: number,
    unknown?: number,
    quality?: Record<string, unknown>
  },
    governance: {
    rules?: Record<string, unknown>,
    skills?: Record<string, unknown>,
    adapters?: Record<string, unknown>,
    memoryContext?: Record<string, unknown>
  },
    quality: {
    sourceCoverage: Record<string, unknown>,
    evidenceCompleteness: string,
    freshness?: string,
    unknown?: number,
    malformed?: number,
    dropped?: number,
    duplicate?: number,
    projectionLagMs?: unknown,
    lastGoodAt?: unknown
  },
    sourceRefs?: unknown[],
    mutationSurface?: {
    externalMutation?: boolean,
    ledgerMutation?: boolean,
    approvalMutation?: boolean,
    gitControl?: boolean
  }
  };

// @contract global-agent-policy
// schema: packages/contracts/schemas/workflow/global-agent-policy.schema.json
export type GlobalAgentPolicy = {
    schema_version: unknown,
    policy_id: string,
    revision?: number,
    created?: string,
    supersedes?: string,
    ownership: {
    layer: unknown,
    mode: unknown,
    single_source: unknown,
    is_authority: unknown,
    note?: string
  },
    communication: {
    default_language: string,
    proceed_on_obvious_default?: boolean,
    avoid_low_value_clarification: boolean,
    ask_only_when_scope_risk_or_side_effect_changes?: boolean
  },
    execution: {
    proportionate_to_scale_and_risk: boolean,
    finish_to_closure?: boolean,
    keep_concise_plan_for_multistep?: boolean,
    one_actively_owned_item?: boolean,
    preserve_dirty_work: boolean
  },
    authority_discovery: {
    resolve_current_main_first: boolean,
    read_top_authority_before_history?: boolean,
    historical_records_non_normative: boolean,
    precedence?: string[]
  },
    authorization: {
    valid_within_task: boolean,
    grants_do_not_outlive_their_task: boolean,
    low_value_confirmation_avoided?: boolean,
    task_grant_respects_platform_hard_limits: boolean,
    explicit_side_effects_require_explicit_authorization?: boolean,
    privilege_ladder: string[]
  },
    task_grant?: {
    granular_permissions_required?: boolean,
    read_only_default?: boolean,
    side_effects_default?: string,
    cannot_override_platform_hard_limits?: boolean
  },
    workspace_boundary: {
    default_scope: string,
    keep_task_data_in_project: boolean,
    never_spill_to_user_home_or_other_projects?: boolean,
    project_local_runtime_root?: string,
    external_output_requires_exact_auth?: boolean
  },
    protected_storage: {
    protected_drives: string[],
    drive_default: unknown,
    authorization_granularity: unknown,
    forbid_before_authorization?: string[]
  },
    credentials: {
    plaintext_forbidden: unknown,
    never_print_or_commit: unknown,
    session_access_default?: string,
    session_access_ladder?: string[],
    raw_body_min_needed_only?: boolean,
    project_rules_cannot_weaken_credential_boundary?: boolean
  },
    session_privacy: {
    default: string,
    minimum_necessary_access: boolean,
    redacted_summary_preferred?: boolean,
    permission_denial_is_a_correct_boundary_signal?: boolean,
    never_elevate_to_bypass_a_denied_private_path?: boolean
  },
    network: {
    public_read_scoped_to_current_sandbox_or_tool?: boolean,
    authenticated_write_requires_auth?: boolean,
    upload_requires_auth?: boolean,
    paid_model_call_requires_auth?: boolean,
    paid_service_requires_auth?: boolean
  },
    git_safety: {
    preserve_dirty_work: boolean,
    stage_owned_changes_only: boolean,
    no_default_git_add_all: boolean,
    no_default_reset_or_clean?: boolean,
    no_force_push_default: boolean,
    do_not_rewrite_history_default?: boolean
  },
    dependency_policy?: {
    prefer_project_interpreter_and_locked_deps?: boolean,
    lockfile_regeneration_is_destructive?: boolean,
    save_exact_diff_before_regenerating?: boolean,
    no_unsolicited_new_dependencies?: boolean
  },
    evidence_semantics: {
    unknown_is_zero: unknown,
    unknown_is_success: unknown,
    simulated_is_real: unknown,
    local_test_is_ci: unknown,
    build_is_runtime: unknown,
    merge_is_installed: unknown,
    plan_equals_write: unknown,
    apply_equals_verified: unknown,
    real_evidence_requires_readback: unknown,
    missing_is_unknown_never_fabricated?: boolean,
    evidence_levels?: string[]
  },
    verification: {
    report_layers_independently: boolean,
    structural_check_separate_from_runtime?: boolean,
    failed_or_skipped_required_check_is_not_pass?: boolean,
    honest_status_vocabulary: string[],
    independent_readback_required_for_verified?: boolean
  },
    parallelism: {
    independent_reads: string,
    isolated_writers?: string,
    overlapping_writes: unknown,
    one_writer_owns_a_checkout: boolean
  },
    skills?: {
    scan_before_executing?: boolean,
    load_matching_skill_before_manual_attempt?: boolean,
    complex_techniques_are_on_demand_skills_not_global_policy?: boolean,
    skill_is_guidance_not_authorization?: boolean
  },
    model_neutrality: {
    preserve_user_provider: unknown,
    preserve_user_model: unknown,
    preserve_user_reasoning: unknown,
    preserve_user_auth: unknown,
    no_hardcoded_model_id_default: unknown,
    no_global_cost_or_rate_clamp_default?: boolean,
    user_model_is_user_owned_not_worklab_managed: unknown
  },
    tool_truth?: {
    use_real_command_output?: boolean,
    never_fabricate_or_invent_state?: boolean,
    do_not_invent_files_apis_or_commands?: boolean,
    keep_working_until_verified_or_exact_blocker?: boolean
  },
    historical_record_policy?: {
    frozen_and_non_normative?: boolean,
    current_authority_first?: boolean,
    never_bulk_search_history_by_default?: boolean,
    history_retrievable_from_frozen_commit?: boolean
  }
  };

// @contract policy-projection-contract
// schema: packages/contracts/schemas/workflow/policy-projection-contract.schema.json
export type PolicyProjectionContract = {
    schema_version: unknown,
    adapter: string,
    policy_version: string,
    renderer: string,
    capability_states: Record<string, unknown>,
    detect_supported?: boolean,
    plan_supported?: boolean,
    apply_supported?: boolean,
    readback_supported?: boolean,
    rollback_supported?: boolean,
    drift_supported?: boolean,
    native_targets?: string[],
    extensions_path?: string,
    loss_report?: Record<string, unknown> | null
  };

// @contract policy-projection-loss-report
// schema: packages/contracts/schemas/workflow/policy-projection-loss-report.schema.json
export type PolicyProjectionLossReport = {
    schema_version: unknown,
    adapter: string,
    policy_version: string,
    projection_state?: ["UNSUPPORTED", "DETECTED", "PLANNED", "WAITING_AUTHORIZATION", "APPLIED", "APPLIED_UNVERIFIED", "READBACK_VERIFIED", "DRIFT", "ROLLBACK_REQUIRED", "ROLLBACK_VERIFIED"],
    native_enforced: string[],
    native_guidance: string[],
    workflow_guard: string[],
    observe_only: string[],
    unsupported: string[],
    readback_verified?: boolean,
    notes?: string
  };

// @contract archive-manifest
// schema: .project/governance/contracts/archive-manifest.schema.json
export type ArchiveManifest = {
    archiveId: string,
    source: string,
    classification: ["product-history", "fixture-source", "reference-only", "regenerate-or-exclude"],
    recovery: {
    repository: string,
    refs: string[],
    verification: string
  },
    status: ["planned", "recorded", "verified", "blocked"]
  };

// @contract software-installation-identity
// schema: packages/contracts/schemas/workflow/software-installation-identity.schema.json
export type SoftwareInstallationIdentity = {
    schema_version: unknown,
    software_id: string,
    package_identity?: string | null,
    installed: boolean,
    install_type?: ["community_desktop_release", "isolated_source_checkout", "native_package_manager", "os_managed", "store_appx", "portable", "unknown", null] | null,
    install_root?: string | null,
    executable_realpath?: string | null,
    launcher_targets?: string | null[],
    config_root?: string | null,
    data_root?: string | null,
    cache_root?: string | null,
    runtime_root?: string | null,
    discovered_version?: string | null,
    release_channel?: ["stable", "beta", "canary", "dev", "unknown", null] | null,
    active_process_path?: string | null,
    discovery_sources?: ["user_declared", "observed_existing", "os_registered", "package_manager", "project_adapter_known_candidate", "running_process", "start_menu_launcher", "desktop_launcher", "vendor_default", "worklab_recommended", "none"][],
    user_declared_location?: string | null,
    observed_existing_location?: string | null,
    os_registered_location?: string | null,
    location_status: ["NOT_INSTALLED", "SINGLE_VERIFIED", "SINGLE_UNVERIFIED", "LOCATION_DRIFT", "DUAL_INSTALLATION", "MISSING_EXPECTED_INSTALL", "RELOCATION_REQUESTED", "OS_MANAGED"],
    location_basis?: string | null,
    binary_digest?: string | null,
    verified_at?: string | null
  };

// @contract software-update-preflight
// schema: packages/contracts/schemas/workflow/software-update-preflight.schema.json
export type SoftwareUpdatePreflight = {
    schema_version: unknown,
    software_id: string,
    update_mode: ["IN_PLACE_ONLY", "RELOCATION", "FRESH_INSTALL", "BLOCKED", "PRESERVE_OFFICIAL_CHANNEL"],
    location_status: ["NOT_INSTALLED", "SINGLE_VERIFIED", "SINGLE_UNVERIFIED", "LOCATION_DRIFT", "DUAL_INSTALLATION", "MISSING_EXPECTED_INSTALL", "RELOCATION_REQUESTED", "OS_MANAGED"],
    approved_operation?: ["UPDATE", "RELOCATION", null] | null,
    relocation_approved?: boolean,
    before?: {
    install_root: string | null,
    executable_realpath: string | null,
    launcher?: string | null,
    version?: string | null
  },
    after?: {
    install_root: string | null,
    executable_realpath: string | null,
    launcher?: string | null,
    version?: string | null
  },
    location_readback_required: boolean,
    location_readback_passed?: boolean | null,
    overall?: ["PASS", "FAIL", "PENDING"],
    reasons?: ["IN_PLACE_UPDATE_OK", "INSTALL_ROOT_CHANGE_REQUIRES_EXPLICIT_RELOCATION", "DUAL_INSTALLATION_UPDATE_BLOCKED", "LOCATION_DRIFT_UPDATE_BLOCKED", "MISSING_EXPECTED_INSTALL_NO_VENDOR_FALLBACK", "SINGLE_UNVERIFIED_IDENTITY_VALIDATION_FIRST", "OS_MANAGED_PRESERVE_OFFICIAL_CHANNEL", "LOCATION_READBACK_FAIL", "RELOCATION_APPROVED", "RELOCATION_NOT_APPROVED"][]
  };

// @contract execution-parallel-dispatch
// schema: packages/contracts/schemas/workflow/execution-parallel-dispatch.schema.json
export type ExecutionParallelDispatch = {
    schema_version: unknown,
    op: ["NEW", "PROMPT"],
    executors: string[],
    payload?: Record<string, unknown>,
    adapter_kind?: ["new", "prompt"],
    per_executor_timeout?: number,
    fail_fast?: boolean,
    status: ["OK", "PARTIAL", "DEGRADED", "FAILED"],
    per_executor?: Record<string, unknown>,
    succeeded?: string[],
    failed?: string[],
    timed_out?: string[],
    unknown?: string[],
    events: Record<string, unknown>[],
    events_stream?: Record<string, unknown>[],
    streamed?: boolean,
    notes?: string[]
  };

// @contract software-update-postflight
// schema: packages/contracts/schemas/workflow/software-update-postflight.schema.json
export type SoftwareUpdatePostflight = {
    schema_version: unknown,
    software_id: string,
    target_version: string,
    before: Record<string, unknown>,
    after: Record<string, unknown>,
    checks: Record<string, unknown>[],
    location_readback_passed: boolean,
    overall: ["PASS", "FAIL", "PENDING"],
    reasons: ["POSTFLIGHT_ALL_CHECKS_PASS", "VERSION_READBACK_FAIL", "BODY_INTEGRITY_FAIL", "LAUNCHER_PINNING_FAIL", "DATA_ROOT_PINNING_FAIL", "C_RESIDUE_DETECTED", "LOCATION_READBACK_FAIL", "RUNTIME_HEALTH_UNVERIFIED", "RUNTIME_HEALTH_FAIL", "POSTFLIGHT_INCOMPLETE"][]
  };

