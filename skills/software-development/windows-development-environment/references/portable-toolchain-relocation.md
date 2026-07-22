# Portable Windows Toolchain Relocation Checklist

Use for Scoop/Rust relocation from a project or user profile to a dedicated toolchain directory.

## Boundaries

Move only reusable tool software and its explicitly required machine-local configuration:

- Scoop app versions, buckets, persist data, shims and cache;
- Rustup/Cargo homes, with an explicit pinned toolchain;
- optional language data such as Tesseract `tessdata`.

Do **not** include project virtual environments, build outputs, task artifacts, databases, logs, browser profiles, auth data, `.env`, OAuth state or credentials.

## Reliable sequence

1. Check capacity and processes whose executable path is under the source root.
2. Create destination layout with separate `toolchains/`, `scripts/`, `manifests/` and `docs/`.
3. Copy source before changing PATH or deleting data. Compare recursive file count and total regular-file bytes.
4. Rebuild Scoop application `current` links and shims from the destination. A filesystem copy can preserve, flatten or leave stale Windows junction targets; do not recursively delete a copied `current` directory until its reparse points are understood.
5. Define activation scripts for both `cmd.exe` and Git-Bash. In Bash, calculate the root then use `cygpath -w` for environment values consumed by Windows executables:

   ```bash
   ROOT_WIN="$(cygpath -w "$ROOT")"
   export SCOOP="$ROOT_WIN\\toolchains\\scoop"
   export RUSTUP_HOME="$ROOT_WIN\\toolchains\\rust\\rustup"
   export CARGO_HOME="$ROOT_WIN\\toolchains\\rust\\cargo"
   export PATH="$CARGO_HOME/bin:$SCOOP/shims:$PATH"
   ```

6. Validate exact executable paths and versions from the destination. For a Rust project, use `cargo metadata --no-deps --format-version 1` before costly compilation. For language data, verify the tool lists/loads the expected data.
7. Update persistent **user** environment variables only after validation. Remove only exact legacy-root PATH entries; retain unrelated entries.
8. Recheck that shim text and newly launched child processes no longer reference the source root.
9. Final cleanup must be fail-closed: abort if any process executable path is within the old root. If old hard-coded callers must survive, replace the removed source root with a Windows junction to the verified new root.

## Junction safety

Scoop may use junctions for `apps/<name>/current` and persisted settings. Never assume a junction is an ordinary directory because `Path.is_symlink()` may return false on Windows. Inspect reparse points with PowerShell:

```powershell
Get-ChildItem "$root\apps" -Directory | ForEach-Object {
  Get-Item (Join-Path $_.FullName 'current') -Force |
    Select-Object FullName, Attributes, LinkType, Target
}
```

For a cleanup script, remove reparse tags/links before recursive deletion so the delete cannot traverse a persistence target. Validate the target remains intact after unlinking. Prefer a tested PowerShell script over hand-written nested `cmd.exe` quoting from Git-Bash.

## Non-portable native build prerequisites

Rustup/Cargo can be relocated with `RUSTUP_HOME`/`CARGO_HOME`. An MSVC Rust target still needs a compatible Visual Studio Build Tools + Windows SDK linker setup. Do not copy a Build Tools directory and call it portable; store reproducible installation instructions or an approved offline layout instead, then test a real link separately.
