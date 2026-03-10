# contextkeeper — HANDOFF.md
Last updated: 2026-03-10

## What This Is
contextkeeper is a CLI tool and universal session continuity protocol for AI agents.
Published on PyPI and npm. Zero model drift between AI agents — Claude, GPT, Gemini, any LLM.

## Current State
- PyPI: https://pypi.org/project/contextkeeper/0.2.1/ ✅ LIVE
- npm: https://www.npmjs.com/package/contextkeeper ✅ LIVE (v0.2.0, needs 0.2.1 bump)
- GitHub: https://github.com/TheRealDataBoss/contextkeeper
- Domain: contextkeeper.ai — PENDING REGISTRATION

## Completed
- [x] Phase 1.5 CLI hardening (enquirer → @inquirer/prompts, config.js, sync.js PAT flow, bootstrap.js clipboard, doctor.js 8-point check, error handling pass)
- [x] Renamed workbench-ai → agentlock → modelvault → contextkeeper
- [x] Published contextkeeper v0.2.0 to npm
- [x] Published contextkeeper v0.2.0 and v0.2.1 to PyPI
- [x] Rewrote README with badges, problem statement, quickstart, command table
- [x] PyPI trove classifiers — PENDING (CLI tool, not library)

## Active Tasks
- [ ] TASK-0007: Bump npm to v0.2.1 + update npm README to match PyPI
- [ ] TASK-0008: Fix pyproject.toml trove classifiers (Environment::Console, Topic::Utilities, remove library classifier)
- [ ] TASK-0009: Register contextkeeper.ai domain
- [ ] TASK-0010: Smoke test all 5 CLI commands end to end (init, sync, status, bootstrap, doctor)
- [ ] TASK-0011: Expose Python library API — public functions: bootstrap(), sync(), status(), init() importable from contextkeeper
- [ ] TASK-0012: Build MCP server — wrap CLI commands as MCP tools (contextkeeper_bootstrap, contextkeeper_sync, contextkeeper_status)
- [ ] TASK-0013: Build REST API (FastAPI) — single backend for MCP + GPT action
- [ ] TASK-0014: Write OpenAPI spec for GPT action distribution
- [ ] TASK-0015: Submit to MCP registry at modelcontextprotocol.io
- [ ] TASK-0016: Build contextkeeper.ai landing page (HTML already designed, needs hosting — GitHub Pages or Vercel)

## Decisions Made
- Product name: contextkeeper (final)
- Value prop: Zero model drift between AI agents
- Domain: contextkeeper.ai (.ai not .dev)
- CLI command: contextkeeper
- Both PyPI and npm as distribution channels
- Python library API to be exposed (low effort, enables MCP server)
- MCP server is highest leverage next move
- REST API backend enables MCP + GPT action from one codebase
- PyPI token: contextkeeper-publish2 (entire account scope)

## Architecture (target)
contextkeeper/
├── CLI (current) ← done
├── Python library API ← TASK-0011
├── MCP server ← TASK-0012
├── REST API (FastAPI) ← TASK-0013
└── GPT action (OpenAPI spec) ← TASK-0014

## Next Session Start
Load this file and STATE_VECTOR.json, confirm task queue, then proceed with TASK-0007.
