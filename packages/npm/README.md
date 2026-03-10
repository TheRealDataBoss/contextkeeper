# agentlock

Zero model drift between AI agents. Universal session continuity protocol and CLI for Claude, GPT, Gemini, and any LLM.

## Install

```sh
npm install -g agentlock
```

## Commands

### `agentlock init`
Initialize agentlock state files in the current project. Auto-detects project type, generates STATE_VECTOR.json and HANDOFF.md, and creates a `.workbench` config file.

```sh
cd my-project
agentlock init
```

Options:
- `-p, --project <name>` — Project slug (default: directory name)
- `-t, --type <type>` — Project type override
- `--bridge <repo>` — Bridge repo (e.g. `yourname/workbench`)

### `agentlock sync`
Sync state files to your bridge repo.

```sh
agentlock sync
```

Options:
- `--bridge <repo>` — Bridge repo override
- `--dry-run` — Preview without pushing

### `agentlock status`
Show status of all projects in the bridge repo.

```sh
agentlock status --bridge yourname/workbench
```

Options:
- `--bridge <repo>` — Bridge repo
- `--json` — Output as JSON

### `agentlock bootstrap`
Generate a paste-ready bootstrap prompt for any AI chat.

```sh
agentlock bootstrap -p my-project --clipboard
```

Options:
- `-p, --project <name>` — Project slug (required)
- `--bridge <repo>` — Bridge repo override
- `--clipboard` — Copy to clipboard

### `agentlock doctor`
Check environment and configuration health.

```sh
agentlock doctor
```

## How It Works

1. `agentlock init` creates structured state files in your project
2. `agentlock sync` pushes them to a central bridge repo on GitHub
3. `agentlock bootstrap` generates a prompt you paste into any AI chat
4. The AI reads your state files and has full context in under 60 seconds

## License

MIT
