// WUI-15 · the front model consumes the generated contract projection.
//
// `packages/client-neutral-core/generated/contracts.ts` is generated from the JSON Schema SSOT
// (`scripts/ci/generate_contract_types.py`), and until now the front model in `src/types.ts` was a second
// hand-written spelling of the same fact, checked against the schema by a Python gate but never actually
// IMPORTED from the generated artifact. This file is that import: it asserts, per path, that the front's
// declaration is a REFINEMENT of what the generator produced -- same field, same or narrower type -- so the
// two spellings cannot drift apart without failing the compile.
//
// The paths the generator cannot name are listed in GENERATED_COLLAPSED_PATHS instead of being asserted:
// the projection collapses them to `Record<string, unknown>` / `unknown[]` (depth and free-form sections,
// the generator's documented limit), and an interface is NOT assignable to an index-signature type in
// TypeScript, so pretending those would refine would be a compile error that means nothing. The Python gate
// (`tests/workflow-assistance/test_generated_contract_types_project_the_schema.py`) re-reads the generated
// file and proves this inventory is exactly the set of collapses inside `WorkflowSnapshotV3` -- a list that
// quietly stopped matching reality is a red, not a hint.
import type { WorkflowSnapshotV3 } from '../../../../packages/client-neutral-core/generated/contracts'
import type { SnapshotV3 } from '@/types'

/** `[Hand] extends [Generated]` -- the front may be narrower, never wider, never a different shape. */
type Refines<Hand, Generated> = [Hand] extends [Generated] ? true : false

/** A compile-time assertion: `Expect<false>` is an error, so a drifted path fails `tsc`. */
type Expect<T extends true> = T

export const GENERATED_CONTRACT_MODULE = 'packages/client-neutral-core/generated/contracts'

/**
 * Paths where the generated projection stops naming fields. Each entry is a measured collapse, and the gate
 * test compares this list against the generated text, so adding a richer front type here without the schema
 * gaining the fields is impossible.
 */
// WUI-21 (20261012): the isolated-trial sections. `isolation` is a deliberately free-form object in the
// contract, so the generator collapses it and it is exempted here. The three separated stages are NOT
// on this list: they were first declared through $defs, the generator cannot follow a $ref and emitted
// `unknown` for every stage, and the honest fix was to inline the stage shape in the schema so the
// projection names it. Four exemptions became one.
export const GENERATED_COLLAPSED_PATHS = [
  'governance.families',
  'workspace',
  'tasks',
  'ci',
  'projects[].repositories',
  'projects[].ci',
  'artifactHandlesSummary.refused',
  'isolatedTrials[].isolation',
] as const

export type CollapsedPath = typeof GENERATED_COLLAPSED_PATHS[number]

// --- the top-level keys the generator does name -------------------------------------------------------
export type SchemaVersionRefines = Expect<Refines<SnapshotV3['schemaVersion'], WorkflowSnapshotV3['schemaVersion']>>
export type RevisionRefines = Expect<Refines<SnapshotV3['revision'], WorkflowSnapshotV3['revision']>>
export type SourceWatermarkRefines = Expect<Refines<SnapshotV3['sourceWatermark'], WorkflowSnapshotV3['sourceWatermark']>>
export type TransportRefines = Expect<Refines<SnapshotV3['transport'], WorkflowSnapshotV3['transport']>>
export type CoverageRefines = Expect<Refines<SnapshotV3['coverage'], WorkflowSnapshotV3['coverage']>>
export type ExecutionIdsRefines = Expect<Refines<SnapshotV3['sourceRefs'], WorkflowSnapshotV3['sourceRefs']>>
export type TokenSummaryRefines = Expect<Refines<SnapshotV3['tokenSummary'], WorkflowSnapshotV3['tokenSummary']>>
export type ExecutionsRefines = Expect<Refines<SnapshotV3['executions'], WorkflowSnapshotV3['executions']>>

// --- how many paths this module actually pins; the Python gate floors this number -------------------
export const PINNED_REFINEMENT_PATHS = [
  'schemaVersion', 'revision', 'sourceWatermark', 'transport', 'coverage',
  'sourceRefs', 'tokenSummary', 'executions',
] as const

/**
 * The negative control, written so it fails in BOTH directions.
 *
 * `{ revision: string }` must NOT refine the generated `revision: number`, so `Expect<…>` receives `false`
 * and tsc raises TS2344 -- which the directive below consumes. If the generated contract ever widened
 * `revision`, or this module stopped reading it, the error would disappear and tsc would then raise TS2578
 * ("unused '@ts-expect-error' directive"). A control that can only fail one way proves nothing.
 */
// @ts-expect-error TS2344: a string revision does not refine the generated `revision: number`
export type PlantedDriftIsRejected = Expect<Refines<{ revision: string }, Pick<WorkflowSnapshotV3, 'revision'>>>
