# OPEN-DESIGN-Assistance Architecture V3

This is the Open Design-first architecture for keeping the assistance repository subordinate to the Open Design runtime while still adding professional design intelligence.

```text
User / files / images / references / existing project
                         ↓
        Source Intake + Rights + Brief Intelligence
                         ↓
              Commercial Design Router
                         ↓
 Domain Scenario + Project State + Controlled GenUI
                         ↓
 Research / Competitors / Reference DNA / Style Lineage
                         ↓
 Master Evidence → Anonymous Method Translation
                         ↓
 Three Structurally Distinct Directions → Human Lock
                         ↓
 DESIGN.md / DTCG Tokens / Components / Asset Contracts
                         ↓
 Generation: Image / HTML / PPTX / PDF / Motion / 3D / Spatial
                         ↓
 Domain Jury + Visual Quality Jury + Deterministic Checks
                         ↓
 Bounded Refinement Loop + Cross-format Coherence
                         ↓
 Digital / Print / Packaging / Spatial / Motion / 3D Preflight
                         ↓
 Editable Handoff + BOM + Provenance + Version + Rollback
                         ↓
 Benchmark Case + Human Review + Capability Evidence
```

## Seven layers

| Layer | Paths | Responsibility |
|---|---|---|
| Governance | `knowledge/governance/`, `research/*/SOURCE_REGISTRY*.json`, `LICENSING_DECISION_REQUIRED.md` | Source, license, security, capability evidence, risk and approval. |
| Knowledge | `knowledge/`, `research/master-studies/`, `research/style-lineages/` | Professional design rules, style lineages, master methods, standards and domain rules. |
| Protocol | `schemas/`, `config/product-manifest.json` | Contracts for briefs, directions, state, scoring, preflight, delivery and provenance. |
| Capability | `atoms/`, `bundles/` | Bounded, testable capability units and capability packages. |
| Orchestration | `scenarios/`, `plugins/` | Pipelines, human decision surfaces, compatibility with existing Open Design skills. |
| Execution | Open Design app/daemon, Hermes, Codex, external adapters | Real runtime invocation, preview, artifact generation/export and recovery. |
| Evidence | `evals/`, `exports/`, `.hermes/task-artifacts/` | Rubrics, baselines, regression cases, execution logs, runtime read-back and review records. |

## Single sources of truth

| File | Purpose |
|---|---|
| `opendesign-assistance/config/product-manifest.json` | Product layers, directory roles, capability families, entrypoints and evidence policy. |
| `opendesign-assistance/schemas/product-manifest.schema.json` | Machine validation for the product manifest. |
| `opendesign-assistance/research/global-absorption/SOURCE_REGISTRY.json` | External source registry and license/integration mode. |
| `opendesign-assistance/research/master-studies/MASTER_REGISTRY.json` | Master/workshop discovery registry and study status. |
| `opendesign-assistance/research/style-lineages/STYLE_LINEAGES.json` | Style lineage ontology and transfer rules. |
| `opendesign-assistance/config/capability-status.json` | Capability status and evidence-level enumeration. |

## Runtime truth rule

Manifest and schema validity are necessary but not sufficient. Runtime availability requires all of:

1. Open Design runtime discovers/registers the plugin, atom, scenario or bundle;
2. a supported API/CLI lists the runtime ID and version;
3. a minimal task runs through the declared stage contract;
4. output artifact, stage event and provenance can be read back;
5. failure/recovery behavior is recorded.

Until then the capability remains `structural` or `isolated`, not `runtime-ready`.

## Compatibility policy

- Existing seven plugins stay available as V1 compatibility surfaces.
- V2/V2.1 atoms, scenarios and bundles add the commercial design and visual-quality engine without deleting old triggers.
- Large tools and license-sensitive sources stay adapter/reference-only until explicit review.
- Generated indexes must be derivable from the product manifest and registries rather than hand-maintained counts.
