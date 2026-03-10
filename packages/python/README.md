# contextkeeper

mcp-name: io.github.TheRealDataBoss/contextkeeper

[![PyPI version](https://img.shields.io/pypi/v/contextkeeper?color=00e5ff&labelColor=0d1320)](https://pypi.org/project/contextkeeper/)
[![Python](https://img.shields.io/pypi/pyversions/contextkeeper?color=00ffa3&labelColor=0d1320)](https://pypi.org/project/contextkeeper/)
[![License](https://img.shields.io/pypi/l/contextkeeper?color=7b61ff&labelColor=0d1320)](https://github.com/TheRealDataBoss/contextkeeper/blob/main/LICENSE)
[![npm](https://img.shields.io/npm/v/contextkeeper?color=ffb300&labelColor=0d1320)](https://www.npmjs.com/package/contextkeeper)

> **Zero model drift between AI agents.**
> Universal session continuity protocol and CLI for Claude, GPT, Gemini, and any LLM.

---

## The Problem

You switch from Claude to GPT mid-project. You open a new chat. You spend 20 minutes re-explaining your stack, your decisions, your constraints. Again. The AI confidently suggests something you already ruled out three sessions ago.

**Every AI session starts with amnesia. contextkeeper fixes this.**

It gives every project a structured state file — synced to GitHub — that any AI agent can read in under 60 seconds.

---

## Install
```bash
pip install contextkeeper
# or
npm install -g contextkeeper
```

---

## How It Works
contextkeeper init    →  generates STATE_VECTOR.json + HANDOFF.md
contextkeeper sync    →  pushes state to your GitHub bridge repo
contextkeeper bootstrap →  generates a paste-ready prompt for any AI
paste it in → full context in < 60 seconds

Works with **Claude**, **ChatGPT**, **Gemini**, **Llama**, **Mistral**, or any LLM that can read a URL.

---

## Quickstart
```bash
cd my-project
contextkeeper init

# sync state to GitHub
contextkeeper sync

# generate bootstrap prompt and copy to clipboard
contextkeeper bootstrap -p my-project --clipboard

# paste into Claude, GPT, Gemini — full context restored instantly
```

---

## Commands

| Command | Description |
|---|---|
| `contextkeeper init` | Auto-detect project type, generate `STATE_VECTOR.json` + `HANDOFF.md` |
| `contextkeeper sync` | Push state files to your GitHub bridge repo |
| `contextkeeper bootstrap` | Generate paste-ready AI prompt, optionally copy to clipboard |
| `contextkeeper status` | Show all tracked projects in the bridge repo |
| `contextkeeper doctor` | 8-point health check — token, git, schema, GitHub API |

### init
```bash
contextkeeper init [-p PROJECT] [-t TYPE] [--bridge REPO]
```

### sync
```bash
contextkeeper sync [--bridge REPO] [--dry-run]
```

### bootstrap
```bash
contextkeeper bootstrap -p PROJECT [--bridge REPO] [--clipboard]
```

### status
```bash
contextkeeper status [--bridge REPO] [--json]
```

### doctor
```bash
contextkeeper doctor
```

---

## Requirements

- Python 3.10+
- `git` on PATH
- GitHub PAT token (for sync)

---

## License

MIT © [TheRealDataBoss](https://github.com/TheRealDataBoss)
