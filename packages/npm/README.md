# workbench-ai

Universal AI session continuity protocol and CLI.

## Install

```sh
npm install -g workbench-ai
```

## Commands

### `workbench init`
Initialize workbench state files in the current project. Auto-detects project type, generates STATE_VECTOR.json and HANDOFF.md, and creates a `.workbench` config file.

```sh
cd my-project
workbench init
```

Options:
- `-p, --project <name>` — Project slug (default: directory name)
- `-t, --type <type>` — Project type override
- `--bridge <repo>` — Bridge repo (e.g. `yourname/workbench`)

### `workbench sync`
Sync state files to your workbench bridge repo.

```sh
workbench sync
```

Options:
- `--bridge <repo>` — Bridge repo override
- `--dry-run` — Preview without pushing

### `workbench status`
Show status of all projects in the bridge repo.

```sh
workbench status --bridge yourname/workbench
```

Options:
- `--bridge <repo>` — Bridge repo
- `--json` — Output as JSON

### `workbench bootstrap`
Generate a paste-ready bootstrap prompt for any AI chat.

```sh
workbench bootstrap -p my-project --clipboard
```

Options:
- `-p, --project <name>` — Project slug (required)
- `--bridge <repo>` — Bridge repo override
- `--clipboard` — Copy to clipboard

## How It Works

1. `workbench init` creates structured state files in your project
2. `workbench sync` pushes them to a central bridge repo on GitHub
3. `workbench bootstrap` generates a prompt you paste into any AI chat
4. The AI reads your state files and has full context in under 60 seconds

## License

MIT
