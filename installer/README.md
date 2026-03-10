# Workbench AI — Installers

## Quick Install

### macOS / Linux
```sh
curl -fsSL https://raw.githubusercontent.com/TheRealDataBoss/contextkeeper/main/installer/install.sh | sh
```

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/TheRealDataBoss/contextkeeper/main/installer/install.ps1 | iex
```

## What the Installer Does

1. **Detects your OS** — macOS, Linux, Windows/WSL, or Windows PowerShell
2. **Checks prerequisites** — git (required), node (optional), python (optional)
3. **Clones the workbench-ai repo** to `~/.workbench/src/`
4. **Creates a `workbench` wrapper** in `~/.workbench/bin/` that delegates to the Node.js or Python CLI
5. **Adds `~/.workbench/bin/` to your PATH**
6. **Verifies the installation**

## Prerequisites

- **git** — required
- **Node.js 18+** — optional, enables the npm-based CLI
- **Python 3.10+** — optional, enables the Python-based CLI

At least one of Node.js or Python is required for the CLI to function.

## Uninstall

### macOS / Linux
```sh
rm -rf ~/.workbench
# Remove the PATH line from your .bashrc / .zshrc / .profile
```

### Windows (PowerShell)
```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.workbench"
# Remove the PATH entry from User environment variables
```

## Alternative: Install via Package Managers

### npm
```sh
npm install -g workbench-ai
```

### pip
```sh
pip install workbench-ai
```
