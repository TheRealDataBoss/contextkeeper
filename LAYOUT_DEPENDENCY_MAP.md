# Agent-Canvas Layout Dependency Map

**Date:** 2026-04-13
**Purpose:** Complete transitive dependency tree for copying agent-canvas layout into notebook app

## Summary

- **Total unique internal files:** 36
- **Total lines:** ~12,547
- **Dependency layers:** 6 (Layer 0 has no internal deps, Layer 5 is the root)

## Deduplicated Master List (Dependency Order)

### Layer 0 -- No internal dependencies (14 files, ~3,233 lines)

| # | File | Lines | Category |
|---|------|-------|----------|
| 1 | @/lib/event-bus.ts | 6 | lib (re-export from @ck/bridge) |
| 2 | @/lib/types.ts | 209 | lib |
| 3 | @/lib/auth.ts | 178 | lib |
| 4 | @/lib/api-client.ts | 489 | lib |
| 5 | @/lib/feature-flags.ts | 159 | lib |
| 6 | @/components/ui/Toast.tsx | 149 | ui |
| 7 | @/components/ui/CommandPalette.tsx | 184 | ui |
| 8 | @/components/ui/Modal.tsx | 78 | ui |
| 9 | @/hooks/useResizable.ts | 110 | hook |
| 10 | @/engine/topologicalSort.ts | 180 | engine |
| 11 | @/stores/terminalStore.ts | 549 | store |
| 12 | @/features/notebook/notebook-modes.ts | 204 | feature |
| 13 | @/features/notebook/notebook-export.ts | 410 | feature |
| 14 | @/lib/aiNodeFeatures.ts | 328 | lib |

### Layer 1 -- Depends only on Layer 0 (6 files, ~1,243 lines)

| # | File | Lines | Depends On |
|---|------|-------|-----------|
| 15 | @/lib/kernel-client.ts | 16 | event-bus, @ck/kernel |
| 16 | @/lib/command-registry.ts | 110 | types, notebook-store, notebook-execute/export/modes/save, event-bus |
| 17 | @/features/notebook/notebook-execute.ts | 144 | kernel-client, event-bus, types |
| 18 | @/features/notebook/notebook-save.ts | 319 | event-bus, auth, api-client, types |
| 19 | @/features/notebook/notebook-store.ts | 341 | types |
| 20 | @/components/ui/BottomPanelActions.tsx | 313 | canvasStore, aiNodeFeatures |

### Layer 2 -- Depends on Layer 0-1 (10 files, ~3,042 lines)

| # | File | Lines | Depends On |
|---|------|-------|-----------|
| 21 | @/engine/resultExtractor.ts | 544 | kernel-client |
| 22 | @/engine/agentPipelineRunner.ts | 387 | canvasStore, event-bus |
| 23 | @/stores/canvasStore.ts | 432 | resultExtractor, agentPipelineRunner |
| 24 | @/components/HealthScore.tsx | 51 | canvasStore |
| 25 | @/features/ai/AiActions.ts | 221 | api-client, notebook-store, kernel-client, event-bus, types |
| 26 | @/features/ai/AiChat.tsx | 278 | api-client, notebook-store, kernel-client, Toast |
| 27 | @/components/ConsolePanel.tsx | 416 | event-bus, kernel-client, notebook-store |
| 28 | @/components/SettingsPanel.tsx | 336 | Modal, feature-flags |
| 29 | @/components/terminal/TerminalModelSelector.tsx | 142 | (no internal deps) |
| 30 | @/components/terminal/SplitPaneManager.tsx | 235 | terminalStore |

### Layer 3 -- Depends on Layer 0-2 (2 files, ~123 lines)

| # | File | Lines | Depends On |
|---|------|-------|-----------|
| 31 | @/components/layout/StatusBar.tsx | 120 | event-bus, kernel-client, notebook-store, notebook-save |
| 32 | @/features/ai/index.ts | 3 | AiChat, AiActions |

### Layer 4 -- Depends on Layer 0-3 (2 files, ~1,181 lines)

| # | File | Lines | Depends On |
|---|------|-------|-----------|
| 33 | @/components/layout/Topbar.tsx | 812 | event-bus, HealthScore, kernel-client, canvasStore, topologicalSort, notebook-save, notebook-store |
| 34 | @/components/layout/Sidebar.tsx | 369 | useResizable, event-bus, 20+ sidebar panels |

### Layer 5 -- Root components (2 files, ~858 lines)

| # | File | Lines | Depends On |
|---|------|-------|-----------|
| 35 | @/layouts/AppLayout.tsx | 47 | layout components, features/ai, ConsolePanel, CommandPalette, SettingsPanel, Toast, command-registry, event-bus |
| 36 | @/components/BottomPanel.tsx | 811 | canvasStore, topologicalSort, kernel-client, event-bus, BottomPanelActions, SplitPaneManager, terminalStore, TerminalModelSelector |

## What the Notebook Already Has vs What Needs Copying

### Already in notebook (from Phase 0-12 extraction):
- event-bus (via @ck/bridge)
- kernel-client (via @ck/kernel)
- notebook-store, notebook-execute, notebook-save, notebook-keyboard, notebook-export, notebook-import, notebook-modes
- types (via @ck/cells)
- All sidebar panels (DepGraphPanel, ContractPanel, VariableExplorer, PipelinePanel, MetricsPanel, KernelPanel, OutlinePanel, MetadataPanel)

### NOT in notebook (would need to copy or stub):
- canvasStore (432 lines) -- canvas-specific, need stub for HealthScore
- terminalStore (549 lines) -- terminal-specific, need stub for BottomPanel terminal tab
- auth.ts (178 lines) -- authentication, need stub
- api-client.ts (489 lines) -- HTTP client, need stub
- feature-flags.ts (159 lines) -- feature toggles, need stub
- aiNodeFeatures.ts (328 lines) -- canvas AI features, not needed
- resultExtractor.ts (544 lines) -- canvas pipeline results, not needed
- agentPipelineRunner.ts (387 lines) -- agent execution, not needed
- BottomPanelActions.tsx (313 lines) -- canvas bottom panel, not needed
- SplitPaneManager.tsx (235 lines) -- terminal split panes, need for terminal tab
- TerminalModelSelector.tsx (142 lines) -- model selector, not needed
- ConsolePanel.tsx (416 lines) -- console output, nice to have
- SettingsPanel.tsx (336 lines) -- settings modal, nice to have
- AiChat.tsx (278 lines) -- AI sidebar, nice to have
- AiActions.ts (221 lines) -- AI actions, nice to have
- HealthScore.tsx (51 lines) -- health gauge, nice to have
- CommandPalette.tsx (184 lines) -- Ctrl+Shift+P, nice to have
- Modal.tsx (78 lines) -- modal wrapper, nice to have
- Toast.tsx (149 lines) -- notifications, nice to have
- useResizable.ts (110 lines) -- resize hook, need for sidebar
- command-registry.ts (110 lines) -- command definitions, nice to have
- topologicalSort.ts (180 lines) -- already in notebook reactive engine

## Recommendation

The notebook's current layout components (Topbar, Sidebar, BottomPanel, StatusBar) are functionally complete with Tailwind styling. Rather than copying the full 12,547-line dependency tree from agent-canvas, progressively copy the most valuable components:

**Priority 1 (high value, low risk):**
- Toast.tsx (149 lines) -- notifications
- Modal.tsx (78 lines) -- modal wrapper
- CommandPalette.tsx (184 lines) -- Ctrl+Shift+P
- useResizable.ts (110 lines) -- sidebar resize

**Priority 2 (medium value, medium risk):**
- SettingsPanel.tsx (336 lines) -- needs Modal + feature-flags
- HealthScore.tsx (51 lines) -- needs canvasStore stub

**Priority 3 (nice to have, high risk):**
- AiChat.tsx (278 lines) -- needs api-client + many deps
- ConsolePanel.tsx (416 lines) -- needs kernel-client integration
- Full BottomPanel with terminal (811 lines) -- needs terminalStore + SplitPaneManager
