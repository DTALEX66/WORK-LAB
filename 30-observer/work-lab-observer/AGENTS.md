# Observer module rules

- Observer is read-only with respect to external systems and all authoritative module state.
- Observer may write only its own events, cache, projections, and reports under project-local ignored runtime paths.
- Do not add execution, approval, configuration-apply, Git mutation, shell, or hidden deep-link routes.
- Do not read credentials, cookies, auth stores, prompt/response bodies, private memory, session databases, or model weights.
- Keep one writer per checkout and preserve existing user changes.
- Structural checks and isolated projections are not live desktop or external-system evidence.
