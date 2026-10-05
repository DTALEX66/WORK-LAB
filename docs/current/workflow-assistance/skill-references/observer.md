# Observer delivery reference

Scope: WORK-LAB Observer changes only. Current production roots are
`apps/observer/frontend` and `apps/observer/src-tauri`; `apps/observer/web` is legacy.
Observer is read-only: never introduce control-plane writes or write telemetry
for a display probe. Use disposable test fixtures for generated telemetry.

Read current frontend manifests, CI and the relevant backend contract. Find the
Runtime Descriptor rather than assuming a port; verify the actual process and
endpoint. Trace source -> canonical store -> snapshot/SSE -> frontend rendering.
UNKNOWN/null must not become fabricated zero or LIVE.

Run affected frontend and backend checks. For delivery, open the rendered page
and check affected full/compact views and real data; API/build success is not UI
or Windows/Tauri runtime proof. Describe unsupported native checks honestly.
