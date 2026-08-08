# WORK-LAB Observer Visual Assets R2 — Desktop Component Status

> Status: `IMPLEMENTED_LOCAL_PENDING_CI`
>
> This document records the repository implementation of
> `WORK-LAB-OBSERVER-VISUAL-ASSETS-R2.zip`. It is a current implementation
> summary, not a release approval and not permission to perform live/global
> mutation.

## User requirement reconciled

The intended product surface is a **portable desktop component**, not a browser
website:

- Tauri owns the desktop shell, tray entry, borderless window, and floating panel.
- The local `web/` tree is the embedded WebView rendering layer; it is not the
  distribution surface users must open in a browser.
- The visual shell is stable after approval. Future updates should normally be
  projection data/parameters delivered through the read-only API, not frontend
  redesigns.
- Observer remains a strictly read-only consumer of the canonical projection.

## Implemented desktop contract

| Surface | Entry | Window contract |
|---|---|---|
| Main | `index.html?view=full&mode=LIVE&theme=dark` | 1180x760, borderless, transparent |
| Panel | `index.html?view=compact&mode=LIVE&theme=dark` | 440x780, fixed size, borderless, transparent, always-on-top, skip-taskbar |

The panel remains hidden until opened from the tray. Closing either surface
hides the application to the tray rather than executing an external action.

Relevant source:

- `30-observer/work-lab-observer/src-tauri/tauri.conf.json`
- `30-observer/work-lab-observer/src-tauri/src/lib.rs`
- `30-observer/work-lab-observer/src-tauri/capabilities/default.json`

## R2 visual implementation

Checked-in brand assets:

- `web/assets/brand/app-icon-512.png`
- `web/assets/brand/design-tokens.json`
- `web/assets/brand/observer-icons.svg`
- `web/assets/brand/work-lab-observer-symbol.svg`
- `web/assets/brand/work-lab-observer-tray.svg`

The Compact component now has:

- fixed 440px component width;
- four core KPIs: running, blocked, input tokens, API estimate/unknown cost;
- dense read-only project list capped at three visible projects;
- blocker, usage, and evidence/health sections;
- dark/light theme tokens and R2 status colors;
- no mutation controls or external runtime assets.

## Data boundary

The frontend consumes the projection through `GET /api/dashboard` only.

- POST/PUT/PATCH/DELETE are rejected by the client boundary.
- Unknown projection fields are ignored for forward compatibility.
- Unknown cost remains unknown; subscription usage remains `not-metered`.
- A bundled last-good/live snapshot is only a read-only fallback for offline
  rendering; it is not a new authoritative source.
- No credentials, prompt/response bodies, private session data, or provider
  auth state are read.

## Issues found and corrected during implementation

1. The Compact header inherited the shell's column direction and expanded
   vertically. It now has an explicit horizontal fixed component header.
2. Compact health cells read `v` while the source objects used `value`, causing
   blank values. The renderer now reads and escapes `value`.
3. Compact token values were formatted as strings and then passed through the
   integer formatter, producing `—`. The renderer now applies the explicit token
   formatter before escaping.
4. The visual asset contract test initially treated SVG's standard XML namespace
   as a remote asset. It now rejects only remote runtime/image references.
5. The desktop component contract test initially lacked the repository runner's
   `run()` export and overmatched the descriptive word `shell`. Both test-only
   false positives are corrected.

## Evidence and verification

Fresh local verification after the implementation:

```text
JS UI + desktop component tests: 39 passed, 0 failed
Python Observer tests: 8 + 10 + 5 passed
AD_HOC_R2_VERIFY_PASS
AD_HOC_DESKTOP_COMPONENT_VERIFY_PASS
node syntax: ok
SHA readback for copied brand assets: 5/5 match
runtime dirs: clean
browser QA console errors: 0
```

The browser was used only as a visual QA harness for the embedded frontend
layer. Full and Compact dark/light views were inspected; it is not evidence that
the packaged Tauri executable was built.

## Known limitation / explicit blocker

The current Windows environment does not have the Rust/Tauri build toolchain:

```text
cargo: unavailable
rustc: unavailable
cargo tauri: unavailable
```

Therefore the Tauri configuration and desktop contract are structurally
verified, but a real Windows portable EXE/ZIP has not been built or run here.
The portable artifact remains `PENDING_TOOLCHAIN_BUILD`.

This does not authorize installing an unknown toolchain, changing system-wide
configuration, or claiming a production release.

## Delivery state

- R2 implementation: complete in the local working tree.
- Required tests and focused verification: passed.
- External provider/live mutation: not executed.
- Human visual/release approval: still pending.
- R2 implementation commit/PR/CI/merge: PR `#30`, exact-head PR run
  `31251264323`, final main push run `31251306631`, merged implementation SHA
  `f141946bfa55fd77120443bacd45aee0049c16e2`.
- Final generated-state reconciliation: PR `#31`, exact-head PR run
  `31251503373`, final main push run `31251545134`, merged reconciliation SHA
  `5d2ceb264edf54c42e347acd1246202a0add31ac`.
- Local and remote `main` were read back equal after each merge. The two SHA
  values above are intentionally retained as implementation and reconciliation
  lineage, not conflated into one release SHA.

## Source and scope

- Source attachment: `.hermes/desktop-attachments/WORK-LAB-OBSERVER-VISUAL-ASSETS-R2.zip`
- Active modules remain exactly:
  - `10-workflow/workflow-assistance`
  - `30-observer/work-lab-observer`
- No second Observer UI, Agent/chat product, task runtime, memory service,
  provider gateway, or external mutation path was added.
