# MINIGAME Domain Pack Source-of-Truth Boundary

## Canonical sources inside WORK-LAB

| Role | Canonical path | Meaning |
|---|---|---|
| Domain contract | `20-design/open-design/domain-packs/minigame-design/manifest.json` | Capabilities, excluded capabilities, evidence minimum and safety boundary. |
| Runtime fixture | `20-design/open-design/minigame-runtime/` | The only in-repository runtime sample used for deterministic smoke and handoff checks. |
| Design rules | `20-design/open-design/domain-packs/minigame-design/rules.md` | Human-readable visual and interaction constraints. |
| Handoff contract | `20-design/open-design/domain-packs/minigame-design/handoff.md` | Required evidence and non-mutating delivery boundary. |

## Explicit non-sources

`D:\\All projects\\MINIGAME` and other external historical copies are not read,
rewritten, copied, or treated as a second live source by this module. They may be
referenced only as historical provenance when a separately approved audit requires
it. The domain pack does not publish, build, configure advertising, or release a
MINIGAME product.

## Evidence boundary

The manifest's minimum evidence level is `E2`. A passing local validator proves only
that the contract and repository boundary are structurally coherent. It does not
promote the pack to E3 runtime registration, E4 release, or E5 commercial acceptance.
