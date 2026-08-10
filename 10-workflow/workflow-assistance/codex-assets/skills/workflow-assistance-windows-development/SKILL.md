---
name: workflow-assistance-windows-development
description: "Use for Windows development failures involving PowerShell, Git Bash, paths, quoting, Node, Python, ports, processes, encoding, or desktop runtimes."
---

# Windows development

- Identify the active shell and executable with real commands. Do not mix PowerShell, cmd.exe, Git Bash, MSYS, WSL, and native Windows syntax.
- Use native `C:\...` paths for Windows Python `Path` code; MSYS `/c/...` paths are shell conveniences and may resolve incorrectly in native programs.
- Verify interpreter and package-manager pairing before installs (`python --version`, `python3 --version`, launcher path, and environment).
- Quote paths containing spaces and pass argument lists instead of shell strings in scripts.
- Inspect live ports and processes before starting or stopping services. Do not kill shared proxy, browser, desktop, or authentication processes for a diagnostic shortcut.
- Keep generated runtime state inside the target Git project and verify restart/readback for desktop or service claims.
