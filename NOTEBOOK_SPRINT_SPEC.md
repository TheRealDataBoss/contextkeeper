# ContextKeeper Notebook: Sprint Specification

**Version:** 1.0
**Date:** 2026-04-12
**Author:** Steven Wazlavek + Claude (Anthropic)
**Status:** Definitive Build Spec

This document sequences every notebook feature into implementable phases with exact monorepo paths, research justification, and dependency ordering. It is the single source of truth for what gets built, in what order, and where every file lands.

---

## Overview

The ContextKeeper Notebook is a living computational pipeline where cells are typed, replaceable processing steps with defined input/output contracts. It targets Tanimoto Level 4 liveness (continuous real-time feedback) -- a level no existing notebook achieves. The current codebase sits at 55% standard feature completion and 5% novel feature completion across 24 files and 4,146 lines inside the data-canvas monolith app.

**Sequencing criteria** (in priority order):

1. Foundation dependencies -- what must exist before anything else can be built
2. User-visible value -- features that unlock daily use
3. Competitive differentiation -- features no other platform has
4. Risk -- technically harder features placed later to allow learning

**Monorepo context:** The notebook currently lives inside `apps/data-canvas/src/` alongside 7 other tools (Data Canvas, Agent Canvas, IDE, Terminal, Chat, Connectors, Viz Studio). Phase 0 extracts the notebook into `apps/notebook/` as a standalone app and moves shared cell infrastructure into `packages/@ck/cells/`. This extraction is a prerequisite for everything else -- building novel features on top of a monolithic 70K-line app creates unmanageable coupling.

**Target totals:** 12 phases, approximately 15,000 lines of new code, 60+ new files, 14 novel features that exist on zero other platforms.

---

## Phase 0: Extraction and Foundation

**Goal:** Separate the notebook from the data-canvas monolith into an independent app with shared packages. After Phase 0, both `apps/data-canvas/` and `apps/notebook/` run standalone with zero circular dependencies.

**Research justification:** The Platform Architecture Map documents the monolith at 267 files and 69,959 lines. Building novel features (reactive execution, branch/compare, agent cells) inside this monolith creates cross-cutting dependency risk. The synthesis (Section 12) recommends the strangler fig pattern -- old and new coexist during transition. Extraction enables independent deployment, independent testing, and independent build optimization.

### 0.1 Create apps/notebook/ scaffold

Create a standalone Vite + React + TypeScript application at `apps/notebook/`.

**Files to create:**

| File | Purpose |
|------|---------|
| `apps/notebook/package.json` | Dependencies: react 18, zustand, codemirror 6, @ck/cells, @ck/kernel, @ck/bridge, @ck/ui |
| `apps/notebook/tsconfig.json` | Extends `../../tsconfig.base.json`, strict mode |
| `apps/notebook/vite.config.ts` | Port 5174, proxy API to localhost:8000, proxy kernel to localhost:8888 |
| `apps/notebook/index.html` | Entry point |
| `apps/notebook/src/main.tsx` | React root mount |
| `apps/notebook/src/App.tsx` | Router shell with sidebar + main area |
| `apps/notebook/src/styles/observatory.css` | Observatory dark theme tokens (cyan #00d2ff, green #00e09e, amber #ffb020, purple #9d7aff, pink #ff6eb4, red #ff5a5a, blue #4a9eff) |

**Verification gate:** `pnpm dev:notebook` starts on port 5174, renders an empty notebook shell, and passes `pnpm typecheck`.

### 0.2 Extract cell infrastructure into packages/@ck/cells

Move the 8 cell components + types into a shared package consumable by both data-canvas and notebook apps.

**Files to move (source -> destination):**

| Source (apps/data-canvas/src/) | Destination (packages/@ck/cells/src/) | Lines |
|-------------------------------|--------------------------------------|-------|
| `components/cell/Cell.tsx` | `Cell.tsx` | 236 |
| `components/cell/CodeCell.tsx` | `CodeCell.tsx` | 71 |
| `components/cell/MarkdownCell.tsx` | `MarkdownCell.tsx` | 111 |
| `components/cell/SqlCell.tsx` | `SqlCell.tsx` | 62 |
| `components/cell/CellOutput.tsx` | `CellOutput.tsx` | 91 |
| `components/cell/CellToolbar.tsx` | `CellToolbar.tsx` | 215 |
| `components/cell/BetweenCellMenu.tsx` | `BetweenCellMenu.tsx` | 188 |
| `components/cell/DataFrameRenderer.tsx` | `DataFrameRenderer.tsx` | 276 |
| `components/cell/index.ts` | `index.ts` | 10 |
| `lib/types.ts` (CellType union + cell interfaces) | `types.ts` | ~120 |

**New files:**

| File | Purpose |
|------|---------|
| `packages/@ck/cells/package.json` | @ck/cells package config |
| `packages/@ck/cells/tsconfig.json` | Extends base, composite: true |
| `packages/@ck/cells/src/index.ts` | Barrel export for all cell components + types |

**Post-move:** Update all imports in `apps/data-canvas/` to reference `@ck/cells` instead of relative paths. The data-canvas app must still build and pass typecheck after this extraction.

**Verification gate:** `pnpm build:packages` succeeds. Both `apps/data-canvas/` and `apps/notebook/` import `@ck/cells` and render cells.

### 0.2b Cell Registry Architecture

The cell registry is the backbone enabling a scalable, extensible cell type system. It defines how cell types are discovered, loaded, validated, and rendered. Three architectural patterns from three different domains are combined.

**Registry interface (ComfyUI NODE_CLASS_MAPPINGS pattern):**

Each cell type exports a registration object conforming to this interface:

```typescript
interface CellRegistration {
  type: string;                          // unique identifier, e.g., "sql", "kpi", "agent"
  label: string;                         // display name, e.g., "SQL Query", "KPI Card"
  category: CellCategory;               // one of 11 categories (see below)
  icon: string;                          // icon identifier (bi-* or custom SVG)
  inputs: TypedPort[];                   // declared input types for DAG validation
  outputs: TypedPort[];                  // declared output types for DAG validation
  component: React.LazyExoticComponent<React.ComponentType<CellProps>>;
}

interface TypedPort {
  name: string;                          // e.g., "dataframe", "query", "text"
  type: PortType;                        // e.g., "DataFrame", "string", "number", "any"
  optional?: boolean;
}
```

**Target file:** `packages/@ck/cells/src/registry/cell-registry.ts`

**Lazy loading:** Cell components are loaded via dynamic `import()` on first use, not bundled at startup. The registry stores `React.lazy(() => import('./components/SqlCell'))` references. This keeps the initial bundle small as the cell type count grows. Only the cell types actually used in a notebook are loaded into memory.

**Category system (11 categories):**

| Category | Description | Example Types |
|----------|-------------|---------------|
| SQL | Database query and write operations | sql, writeback |
| LLM/Prompt | AI model interaction | prompt, agent |
| Visualization | Charts, maps, diagrams | chart, map, mermaid |
| Input/Widget | Interactive user inputs | form-slider, form-dropdown, form-text |
| Smart/Extensible | Plugin-provided or auto-generated cells | (future plugin cells) |
| Pipeline/Workflow | Execution flow control | branch, merge, router, tournament |
| Display | Formatted output rendering | markdown, html, latex, kpi, image |
| Data | Data inspection and manipulation | table, profile, filter, pivot |
| Agent | Autonomous AI agents | agent (Phase 8) |
| Meta/Infrastructure | Notebook infrastructure | deploy, webhook, cache, approval |
| Novel | ContextKeeper-exclusive innovations | comparison, live |

**Scale targets:**
- Launch: 33 cell types across 11 categories
- 12 months post-launch: 200+ types (including community contributions)
- Long-term with plugin ecosystem: 10,000+ types (ComfyUI has 20K+ custom nodes as precedent)

**Three architectural patterns adopted:**

1. **Rasterization (Livebook Smart Cell pattern):** Every cell type -- no matter how visual or interactive -- must degrade to plain executable code for export. A KPI cell rasterizes to Python that computes and prints the metric. A filter cell rasterizes to pandas/SQL that applies the filter. This guarantees that any ContextKeeper notebook can be exported as a standard .py file and run without ContextKeeper installed.

2. **Typed-port graph (ComfyUI pattern):** Each cell declares its input and output types via `TypedPort[]`. The DAG validation engine uses these declarations to prevent invalid connections (e.g., a chart cell cannot receive a string where it expects a DataFrame). Type mismatches are shown as red connection indicators in the DAG view (Phase 6). This enables auto-suggestions for compatible upstream cells.

3. **Reactive variable binding (Marimo pattern):** Cells declare dependencies through variable references in their source code. The Phase 2 AST extractor identifies `defines` and `references` per cell, building the reactive dependency graph. Combined with typed ports, this creates a dual validation system -- structural (port types) and semantic (variable references).

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `packages/@ck/cells/src/registry/cell-registry.ts` | Registry singleton with register/get/list/getByCategory methods | 120 |
| `packages/@ck/cells/src/registry/types.ts` | CellRegistration, TypedPort, PortType, CellCategory type definitions | 60 |
| `packages/@ck/cells/src/registry/index.ts` | Barrel export | 5 |

**Verification gate:** All existing cell types register via the new registry. `cellRegistry.list()` returns all registered types with correct categories. Lazy loading verified by confirming no cell component code is in the initial bundle (Vite bundle analyzer).

### 0.3 Extract notebook feature modules to apps/notebook/src/features/

Move the 7 notebook-specific feature modules from data-canvas into the new notebook app. These modules are notebook-specific and have no consumers outside the notebook.

**Files to move:**

| Source (apps/data-canvas/src/features/notebook/) | Destination (apps/notebook/src/features/) | Lines |
|-------------------------------------------------|------------------------------------------|-------|
| `notebook-store.ts` | `notebook-store.ts` | 341 |
| `notebook-execute.ts` | `notebook-execute.ts` | 144 |
| `notebook-keyboard.ts` | `notebook-keyboard.ts` | 500 |
| `notebook-save.ts` | `notebook-save.ts` | 319 |
| `notebook-export.ts` | `notebook-export.ts` | 410 |
| `notebook-import.ts` | `notebook-import.ts` | 328 |
| `notebook-modes.ts` | `notebook-modes.ts` | 204 |

**Files to move from lib/:**

| Source (apps/data-canvas/src/lib/) | Destination (apps/notebook/src/lib/) | Lines |
|-----------------------------------|-------------------------------------|-------|
| `cell-operations.ts` | `cell-operations.ts` | 244 |
| `cell-execution.ts` | `cell-execution.ts` | 98 |
| `cell-history.ts` | `cell-history.ts` | 29 |

**Also move:**

| Source | Destination | Lines |
|--------|------------|-------|
| `apps/data-canvas/src/pages/NotebookPage.tsx` | `apps/notebook/src/pages/NotebookPage.tsx` | 251 |
| `apps/data-canvas/src/features/sidebar/CellListPanel.tsx` | `apps/notebook/src/features/sidebar/CellListPanel.tsx` | 153 |

**Post-move:** Leave re-export stubs in `apps/data-canvas/` that import from the notebook app (if needed for cross-tool navigation) or update the data-canvas router to mount the notebook app as a micro-frontend.

**Verification gate:** `apps/notebook/` runs standalone, renders NotebookPage with cells, keyboard shortcuts work, save/load works.

### 0.4 Extract kernel client into packages/@ck/kernel

The kernel client (412 lines) is shared infrastructure -- both the notebook and the data canvas pipeline runner need kernel communication.

**Files to move:**

| Source | Destination | Lines |
|--------|------------|-------|
| `apps/data-canvas/src/lib/kernel-client.ts` | `packages/@ck/kernel/src/kernel-client.ts` | 412 |
| `shared/kernel.ts` | `packages/@ck/kernel/src/types.ts` | 25 |
| `shared/notebook.ts` (cell/output types) | `packages/@ck/kernel/src/notebook-types.ts` | 57 |

**New files:**

| File | Purpose |
|------|---------|
| `packages/@ck/kernel/package.json` | @ck/kernel package config |
| `packages/@ck/kernel/tsconfig.json` | Extends base |
| `packages/@ck/kernel/src/index.ts` | Barrel export |

**Verification gate:** Both apps use `@ck/kernel` for kernel communication. Execute a Python cell from both apps.

### 0.5 Cross-app communication foundation (packages/@ck/bridge)

Create a typed message bus for cross-app communication. This enables the bidirectional notebook-canvas sync planned in Phase 10 and supports the existing cross-tool-bridge.ts pattern.

**New files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `packages/@ck/bridge/package.json` | Package config | 15 |
| `packages/@ck/bridge/tsconfig.json` | TS config | 10 |
| `packages/@ck/bridge/src/index.ts` | Barrel export | 10 |
| `packages/@ck/bridge/src/bridge.ts` | BroadcastChannel-based link/sink protocol | 150 |
| `packages/@ck/bridge/src/types.ts` | Message type definitions (cell-pinned, cell-updated, cell-removed, kernel-status) | 60 |
| `packages/@ck/bridge/src/hooks.ts` | `useBridgeLink()` and `useBridgeSink()` React hooks | 80 |

**Protocol:** Uses the BroadcastChannel API for same-origin cross-tab communication. Messages are typed discriminated unions. Each app creates a "link" (sender) or "sink" (receiver) for specific message channels.

**Research justification:** Synthesis Section 7 (bidirectional notebook-canvas sync) identifies this as partial prior art -- Enso has dual visual/textual sync but not for computational notebooks. The bridge package provides the communication layer; the sync logic itself is Phase 10.

**Verification gate:** Send a message from data-canvas, receive it in notebook app running in a separate tab.

### 0.6 Verify independence

**Checks:**

1. `pnpm dev:notebook` starts standalone on port 5174
2. `pnpm dev:data-canvas` starts standalone on port 5173
3. Both apps import `@ck/cells`, `@ck/kernel`, `@ck/bridge`, `@ck/ui` successfully
4. `pnpm typecheck` passes with zero errors across the entire monorepo
5. `pnpm build` succeeds for all packages and apps
6. No circular dependency: run `madge --circular apps/notebook/src/` and `madge --circular apps/data-canvas/src/` -- both return empty
7. CI gate check passes: `node .migration/gate-check.mjs`

**Phase 0 totals:** ~315 new lines of code, ~2,800 lines moved, 6-8 new files created, 0 features deleted.

---

## Phase 1: Complete Standard Cell Types

**Goal:** Bring all 12 existing cell types to full functionality and add 4 new data-oriented cell types. After Phase 1, the notebook is a complete Jupyter replacement for daily use.

**Research justification:** The Completion Map identifies 6 partially implemented and 14 missing standard features. The Audit confirms 5 of 12 cell types are fully ported; the remaining 7 are "type defined" with stubs but no rendering logic. The synthesis (Section 5) inventories 78 cell types across 8 tiers -- Phase 1 targets Tier 1 (Compute) and Tier 2 (Display) completeness.

### 1.1 MarkdownCell RenderedOutput integration

**What exists:** MarkdownCell.tsx (111 lines) has edit mode via Monaco and a simple line-by-line preview renderer. Line 5 comment explicitly states: "A full markdown renderer will be added in a later task."

**What to build:** Replace the simple preview with the RenderedOutput component already built in Sprint 2. This component uses `marked` for markdown parsing and `KaTeX` for LaTeX math rendering.

**Target file:** `packages/@ck/cells/src/MarkdownCell.tsx`
**Estimated change:** ~30 lines modified (swap renderer), ~0 new files
**Research justification:** Synthesis Section 5 Tier 2 -- LaTeX/Math cells are "table stakes" across all platforms. KaTeX is the recommended renderer (used by Observable, faster than MathJax).

### 1.2 PromptCell component

**What exists:** Cell type `prompt` is defined in types.ts. No component.

**What to build:** A dedicated LLM cell with:
- Model selector dropdown (independent per cell, per architecture rules -- defaults to Groq Llama 3.3 70B)
- System prompt textarea (collapsible)
- User prompt textarea (primary editor area)
- Streaming output display with token count
- Cost estimation display
- Temperature / max tokens sliders
- Output routing: insert result as new cell below, or display inline

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `packages/@ck/cells/src/PromptCell.tsx` | Component | 200 |
| `packages/@ck/cells/src/PromptCellConfig.tsx` | Config panel (model, temperature, system prompt) | 100 |

**Dependencies:** `@ck/ai` package (browser.ts for LLM calls, models.ts for model registry)

**Research justification:** Synthesis Section 5 Tier 5 identifies 7 prompt/LLM cell implementations across platforms (Copilot Chat, Hex Magic, Deepnote AI, Colab AI, Databricks Assistant, JupyterAI, Amazon Q). All are side-panel assistants, not dedicated cell types. A first-class prompt cell is a differentiator.

### 1.3 VizCell component

**What exists:** Cell type `viz` defined. No component.

**What to build:** A visualization cell with:
- Chart type picker (bar, line, scatter, histogram, box, heatmap, pie, area, violin, funnel, sankey, treemap)
- Column mapping dropdowns (X, Y, color, size, facet)
- Plotly.js rendering engine (interactive, 10M+ downloads/month per synthesis)
- Auto-chart recommendation based on column types (numeric -> histogram, categorical x numeric -> bar, 2 numeric -> scatter)
- Export to PNG/SVG
- Integration with upstream DataFrame outputs (auto-detect available columns)

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `packages/@ck/cells/src/VizCell.tsx` | Main component | 250 |
| `packages/@ck/cells/src/VizCellConfig.tsx` | Chart type + column mapping UI | 150 |
| `packages/@ck/cells/src/chart-recommend.ts` | Auto-chart recommendation logic | 80 |

**Dependencies:** `plotly.js-dist-min` (already used in `apps/data-canvas/src/components/analytics/`)

**Research justification:** Synthesis Section 5 Tier 2 -- Plotly recommended as primary (interactive, wide format support) with Vega-Lite as secondary (declarative spec for AI generation). The 28 Plotly chart components in `apps/data-canvas/src/components/analytics/` provide existing patterns to follow.

### 1.4 MermaidCell component

**What exists:** Cell type `mermaid` defined. No component.

**What to build:** Mermaid.js live preview with:
- Monaco editor in mermaid syntax mode
- Live rendered preview (side-by-side or toggle)
- Export to SVG/PNG
- Error display for invalid syntax

**Target file:** `packages/@ck/cells/src/MermaidCell.tsx`
**Estimated lines:** 100
**Dependencies:** `mermaid` npm package

**Research justification:** Synthesis Section 5 Tier 2 -- "Mermaid.js for flowcharts, sequence diagrams, Gantt charts. Deepnote supports Mermaid blocks."

### 1.5 HTMLCell component

**What exists:** Cell type `html` defined. Currently rendered through CodeCell fallback.

**What to build:** Sandboxed iframe rendering with:
- Monaco HTML editor
- Iframe preview with CSP sandbox (sandbox="allow-scripts")
- Resize handles for iframe height
- Toggle between edit and preview

**Target file:** `packages/@ck/cells/src/HTMLCell.tsx`
**Estimated lines:** 90

**Research justification:** Synthesis Section 5 Tier 2 -- HTML rendering via sandboxed iframe is the standard approach. CellOutput.tsx already handles `text/html` MIME type via sanitized iframe -- HTMLCell extends this to editable HTML cells.

### 1.6 LaTeXCell component

**What exists:** Cell type `latex` defined. Currently rendered through MarkdownCell fallback.

**What to build:** Full LaTeX document cell (not just inline math) with:
- Monaco LaTeX editor with syntax highlighting
- KaTeX block rendering
- Error display for invalid LaTeX

**Target file:** `packages/@ck/cells/src/LaTeXCell.tsx`
**Estimated lines:** 80

### 1.7 ScratchCell and RawCell components

**What exists:** Both types defined. Raw is ported (renders in `<pre>`). Scratch falls through to default.

**What to build:** Minimal components -- Scratch gets a Monaco plaintext editor with muted styling (visual distinction from code cells). Raw stays as-is.

**Target file:** `packages/@ck/cells/src/ScratchCell.tsx`
**Estimated lines:** 40

### 1.8 FormCell placeholder

**What exists:** Cell type `form` defined. No component.

**What to build:** A placeholder component with a message directing to Phase 5 (Input/Widget Cells) where the full reactive widget system is built. This prevents confusion when users encounter the form cell type.

**Target file:** `packages/@ck/cells/src/FormCell.tsx`
**Estimated lines:** 25

### 1.8b WritebackCell component

**What exists:** No cell type or component.

**What to build:** A dedicated write-to-database cell (Hex pattern) with:
- Connection context dropdown selecting from configured data sources
- DataFrame input selector (upstream DataFrame variable)
- Target table configuration (schema, table name, write mode: append/replace/upsert)
- Column mapping UI with type coercion options
- Dry-run preview showing first N rows + SQL DDL
- Execution modes: manual, on-session-start, on-schedule

**Target file:** `packages/@ck/cells/src/components/WritebackCell.tsx`
**Estimated lines:** 180

**Research justification:** Synthesis Section 5 Tier 4 -- "Hex has a dedicated Writeback cell type. No other notebook has a dedicated write-back cell type." This is separated from the SQL cell to keep write operations explicit and auditable.

### 1.8c FilterCell component

**What exists:** No cell type or component.

**What to build:** A no-code visual filter builder generating SQL WHERE clauses (Hex pattern) with:
- Column picker from upstream DataFrame schema
- Operator selector per column (equals, contains, between, in, is null, regex)
- AND/OR grouping with drag-and-drop reordering
- Live preview of generated WHERE clause
- Output: filtered DataFrame variable with green pill indicator

**Target file:** `packages/@ck/cells/src/components/FilterCell.tsx`
**Estimated lines:** 160

**Research justification:** Hex Filter cell pattern -- no-code filtering lowers the barrier for non-SQL users. Filter logic is inspectable and version-controlled, unlike ad-hoc pandas operations.

### 1.8d PivotCell component

**What exists:** No cell type or component.

**What to build:** A no-code pivot table with drag-and-drop column/row/value assignment (Hex pattern) with:
- Drag-and-drop wells for rows, columns, values, and filters
- Aggregation selector per value field (sum, mean, median, count, min, max, std, custom)
- Subtotals and grand totals toggle
- Heatmap conditional formatting option
- Output: pivoted DataFrame variable
- Export to CSV/Excel

**Target file:** `packages/@ck/cells/src/components/PivotCell.tsx`
**Estimated lines:** 220

**Research justification:** Pivot tables are a core data exploration primitive. Hex and Sigma provide drag-and-drop pivot interfaces. Building this as a dedicated cell type makes pivot operations reproducible and composable in the DAG.

### 1.8e KPICell component

**What exists:** MetricCell (section 1.9) covers basic large-number display. KPICell is its enhanced successor.

**What to build:** A single-value / KPI display cell (Hex BigNumber + Deepnote pattern) with:
- Large formatted number with configurable format (currency, percent, integer, decimal, custom)
- Label and subtitle text
- Trend arrow (up/down/flat) with percentage change
- Sparkline showing historical values from a DataFrame column
- Comparison baseline (vs. previous period, vs. target)
- Observatory color coding (green #00e09e for positive, red #ff5a5a for negative, amber #ffb020 for flat)
- Multiple KPIs per cell in a horizontal strip layout

**Target file:** `packages/@ck/cells/src/components/KPICell.tsx`
**Estimated lines:** 150

**Research justification:** Synthesis Section 5 Tier 2 -- "Hex Single Value cell (aggregation, comparison mode, sparkline, outputs Python variable), Deepnote Big Number block." Dedicated KPI cells are common in BI tools but absent from data science notebooks.

### 1.8f ScratchpadCell component

**What exists:** ScratchCell (section 1.7) provides a minimal plaintext editor. ScratchpadCell is a distinct ephemeral debugging cell.

**What to build:** An ephemeral debugging cell that does NOT participate in the reactive DAG (Marimo pattern) with:
- Full code editor (Monaco, Python syntax)
- Execution capability with output display
- Visual distinction: dashed border, muted background, "Ephemeral" badge
- Excluded from notebook export by default (toggle to include)
- Excluded from dependency graph -- reads variables but never defines them for downstream use
- Auto-collapse after N minutes of inactivity (configurable)

**Target file:** `packages/@ck/cells/src/components/ScratchpadCell.tsx`
**Estimated lines:** 100

**Research justification:** Marimo's scratchpad pattern -- valuable for debugging without polluting the reactive DAG. Users frequently need throwaway cells to inspect intermediate values; making this a first-class type prevents accidental side effects.

### 1.9 New cell types -- DataFrame, Metric/KPI, Profile, Map

Add 4 new data-oriented cell types not in the original 12.

**DataFrame Display Cell:**
- Embeds DataFrameRenderer (276 lines, already built) as a standalone cell
- User specifies a variable name; cell renders that variable as an interactive table
- Sort, filter, search, pagination, column stats, CSV export

**Target file:** `packages/@ck/cells/src/DataFrameCell.tsx`
**Estimated lines:** 60

**Metric/KPI Cell:**
- Large number display with label, trend arrow, sparkline
- Configurable: variable name, format (currency, percent, integer, decimal), comparison baseline
- Observatory color coding (green for up, red for down, amber for flat)

**Target file:** `packages/@ck/cells/src/MetricCell.tsx`
**Estimated lines:** 120

**Research justification:** Synthesis Section 5 Tier 2 -- "Hex has metric tiles, Evidence has `<Value>` components, Sigma has KPI cards. Dedicated metric cells that display a single number with trend/sparkline are common in BI tools but absent from data science notebooks."

**Profile Cell:**
- Automated data profiling for a DataFrame variable
- Column types, null counts, distribution histograms, correlations, unique counts
- Leverages `computeProfiles.ts` (exists in `apps/data-canvas/src/nodes/data/`)

**Target file:** `packages/@ck/cells/src/ProfileCell.tsx`
**Estimated lines:** 180

**Research justification:** Synthesis Section 5 Tier 4 -- "No notebook has a dedicated profile cell type; profiling is always via library calls in code cells." Deepnote's inline profiling is the best prior art.

**Map Cell:**
- Geospatial visualization with Leaflet.js
- Point, polygon, heatmap layers
- User specifies latitude/longitude columns from upstream DataFrame
- Zoom, pan, layer toggle

**Target file:** `packages/@ck/cells/src/MapCell.tsx`
**Estimated lines:** 200

**Research justification:** Synthesis Section 5 Tier 2 -- "No notebook has dedicated map cell types -- maps are always rendered through code cells."

### 1.10 Update Cell.tsx type dispatch

Update the Cell component's switch statement to route all new cell types to their components.

**Target file:** `packages/@ck/cells/src/Cell.tsx`
**Estimated change:** ~30 lines added to switch statement

### 1.11 Update types.ts cell type union

Extend the CellType literal union with new types: `dataframe`, `metric`, `profile`, `map`.

**Target file:** `packages/@ck/cells/src/types.ts`
**Estimated change:** ~10 lines

### 1.12 BetweenCellMenu AI Generate wiring

**What exists:** BetweenCellMenu.tsx (188 lines) has an "AI Generate" button. No LLM integration.

**What to build:** Wire the button to `@ck/ai` sendMessage, insert generated code as a new cell below.

**Target file:** `packages/@ck/cells/src/BetweenCellMenu.tsx`
**Estimated change:** ~50 lines

### 1.13 Run All / Run Above / Run Below UI

**What exists:** `cell-operations.ts` implements `runAbove`, `runBelow`, `runAll` functions. No toolbar buttons.

**What to build:** Add buttons to the notebook toolbar (not per-cell toolbar). Progress indicator for multi-cell execution.

**Target files:**
- `apps/notebook/src/components/NotebookToolbar.tsx` (new, ~120 lines)
- `apps/notebook/src/features/notebook-execute.ts` (modify, add progress tracking)

### 1.14 Search and replace UI

**What exists:** `cell-operations.ts` has `findReplace` function. No UI.

**What to build:** Modal with find/replace across all cells. Regex support. Match highlighting.

**Target file:** `apps/notebook/src/components/SearchReplace.tsx` (new, ~120 lines)

**Phase 1 totals:** ~2,660 new lines, ~20 new files, 21 cell types functional (up from 5), 0 novel features (all standard).

### SQL Cell Implementation

The SQL cell is the most complex standard cell type, with 25+ distinct implementations across the industry. This subsection consolidates the implementation guidance from the research synthesis.

**Connection context:** Cell-level dropdown selecting from configured data sources (Hex/Deepnote pattern). Each SQL cell independently selects its database connection. When no connection is selected, the cell defaults to DuckDB in-memory mode for querying local DataFrames. The connection list is populated from `@ck/connectors` registered data sources.

**Result binding:** SQL cell output is bound to a named DataFrame variable with a colored pill indicator -- green pill = materialized DataFrame (result fetched into memory), purple pill = Query/lazy reference (pointer to upstream query, not yet materialized). The variable name defaults to the cell label but is user-editable. Downstream Python cells access the result via the variable name directly (e.g., `df = orders_by_region`).

**Variable templating:** Jinja2 templating engine with:
- `{{ variable_name }}` -- scalar interpolation (string, number, date)
- `{{ list_var | array }}` -- expands Python list to SQL IN-clause format: `('a', 'b', 'c')`
- `{% if condition %}...{% endif %}` -- conditional SQL blocks
- `{% for item in collection %}...{% endfor %}` -- loop expansion
- Widget integration: `{{ slider_value }}` automatically references upstream widget cell outputs
- Escaping: all interpolated values are parameterized (never raw string concatenation) to prevent SQL injection

**CTE chaining:** When a downstream SQL cell references an upstream SQL cell's output variable, the engine compiles both queries as a CTE chain at execution time (Hex/Count pattern). Example: if cell A defines `active_users` and cell B references `{{ active_users }}`, the compiled query becomes `WITH active_users AS (SELECT ... FROM cell_A_query) SELECT ... FROM active_users WHERE ...`. This avoids materializing intermediate results when both cells target the same connection.

**DuckDB in-memory mode:** When the connection is set to "In-Memory" or when querying local DataFrame variables, the cell uses DuckDB-WASM (for Pyodide/browser mode) or DuckDB Python (for kernel mode). DataFrames are registered as virtual tables automatically. This enables SQL queries over pandas/polars DataFrames without a database server.

**Write-back:** Write operations use the separate WritebackCell type (section 1.8b), not inline SQL DML. The SQL cell is read-only by design. This separation makes destructive operations explicit and auditable.

**Dialect handling:** The SQL dialect is determined by the selected connection (PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, etc.). When the connection is DuckDB (in-memory), DuckDB dialect is auto-selected. Syntax highlighting and autocomplete adapt to the active dialect. Future: SQLGlot transpilation for cross-dialect portability (SQLMesh pattern).

---

## Phase 2: Reactive Execution Engine

**Goal:** Implement Marimo-style reactive execution where cells automatically re-execute when upstream dependencies change. This is the single most important differentiator for reproducibility -- it addresses the 4% reproduction rate problem (Pimentel 2019).

**Research justification:** Synthesis Section 3 provides deep analysis of 6 reactive systems (Marimo, Observable, Pluto.jl, Excel, Livebook, IPyflow). The recommended approach is Marimo-style static AST analysis as default + typed cell contracts as escape hatch for mutation edge cases (Rex failures). The `engine/topologicalSort.ts` in data-canvas already implements topological sort for pipeline execution -- this can be adapted.

### 2.1 AST dependency extractor

Static analysis of Python cell source code using the Python `ast` module. Since the kernel runs Python, the AST analysis runs server-side via a kernel introspection endpoint.

**What it does:** Given cell source code, returns `{defines: string[], references: string[]}` -- the variables the cell defines and the variables it references.

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/engine/reactive/ast-extract.ts` | Client-side API to request AST analysis from kernel | 80 |
| `backend/app/services/ast_service.py` | Server-side Python AST analysis (uses `ast.parse`, walks `ast.Name`, `ast.FunctionDef`, `ast.Assign`, etc.) | 200 |
| `backend/app/routers/ast.py` | FastAPI endpoint: POST /api/v1/ast/analyze | 40 |

**Handles:** Simple assignments (`x = 1`), function definitions (`def foo():`), class definitions, imports, augmented assignments (`x += 1`), for/while loop variables, comprehension variables, with-statement variables, type annotations.

**Does NOT handle** (deferred to contracts): In-place mutations (`list.append()`), aliased variables (`b = a; b.append(1)`), dynamic attribute access (`getattr(obj, name)`), higher-order side effects. These are the Rex test suite failure categories -- they require contracts (Phase 3).

**Research justification:** Synthesis Section 3 -- Marimo's `ScopedVisitor` class walks the AST to find references and definitions at each scope level. NBLyzer (Subotic 2022) demonstrates 98.7% analysis completion under 1 second, validating that this approach works at interactive speeds.

### 2.2 Dependency graph construction

Build a directed acyclic graph where nodes are cells and edges represent variable dependencies.

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/engine/reactive/dep-graph.ts` | Graph construction from AST results. Nodes = cells, edges = variable dependencies. Adjacency list representation. | 150 |
| `apps/notebook/src/engine/reactive/topo-sort.ts` | Topological sort of the dependency graph. Adapted from `engine/topologicalSort.ts` in data-canvas. | 60 |

**Circular dependency detection:** If the graph has a cycle, mark all cells in the cycle with a `circular-dependency` error status and display the cycle path in the error message.

### 2.3 Staleness detection and cascade re-execution

When a cell's source changes, mark all downstream cells as stale (dirty-flag propagation). Re-execute stale cells in topological order.

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/engine/reactive/staleness.ts` | Dirty-flag propagation through the graph. Marks downstream cells as stale when a cell changes. | 80 |
| `apps/notebook/src/engine/reactive/cascade-executor.ts` | Executes stale cells in topological order. Integrates with existing `notebook-execute.ts`. Skips cells with errored upstream dependencies. | 120 |
| `apps/notebook/src/engine/reactive/index.ts` | Barrel export | 10 |

### 2.4 Output caching with invalidation

Cache cell outputs keyed by (cell_id, source_hash, input_hash). When a cell's source or any upstream output changes, the cache entry is invalidated.

**Target file:** `apps/notebook/src/engine/reactive/output-cache.ts`
**Estimated lines:** 100

**Research justification:** Synthesis Section 3 -- "Error handling: cells that depend on errored cells are marked stale but not executed." Caching prevents unnecessary re-execution when only downstream cells change.

### 2.5 Reactive mode toggle

Add a mode toggle to the notebook toolbar: Manual | Reactive. In manual mode, cells execute on demand (current behavior). In reactive mode, cells re-execute automatically when dependencies change.

**Target files:**
- `apps/notebook/src/features/notebook-store.ts` (modify -- add `executionMode: 'manual' | 'reactive'` to store)
- `apps/notebook/src/features/notebook-execute.ts` (modify -- check execution mode before executing)
- `apps/notebook/src/components/NotebookToolbar.tsx` (modify -- add mode toggle)

**Estimated change:** ~60 lines across 3 files

### 2.6 Visual staleness indicators

Show stale cells with a visual indicator (amber border + "stale" badge). Show the dependency graph as a minimap in the sidebar.

**Target files:**
- `packages/@ck/cells/src/Cell.tsx` (modify -- add stale border state)
- `apps/notebook/src/features/sidebar/DepGraphPanel.tsx` (new, ~150 lines -- minimap of cell dependency DAG)

**Phase 2 totals:** ~1,050 new lines, ~8 new files, 1 major feature (reactive execution). This phase is the highest-risk technical work in the entire spec.

---

## Phase 3: Cell Contract System

**Goal:** Allow cells to declare typed input/output contracts with automatic schema inference. Contracts provide the escape hatch for cases where AST analysis fails (Rex mutations) and enable the Branch/Compare/Replace system in Phase 7.

**Research justification:** Synthesis Section 8 Feature 8 -- "No notebook has built-in cell-level contracts that declare input types and output schemas, with automatic schema inference from cell execution." dlt auto-infers at pipeline level. Pandera validates DataFrames but requires manual definition. NBLyzer analyzed contracts statically but did not enforce during execution.

### 3.1 Contract type definitions

**Target file:** `apps/notebook/src/contracts/types.ts`
**Estimated lines:** 80

Defines:
- `CellContract { inputs: Record<string, ColumnSchema[]>, outputs: Record<string, ColumnSchema[]> }`
- `ColumnSchema { name: string, dtype: string, nullable: boolean, min?: number, max?: number, unique?: boolean, allowed_values?: any[] }`
- `ContractViolation { cell_id: string, direction: 'input' | 'output', variable: string, column: string, violation: string, expected: any, actual: any }`

### 3.2 Automatic schema inference

After cell execution, inspect the output variables and infer their schemas automatically.

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/contracts/infer.ts` | Client-side API to request schema inference from kernel | 60 |
| `backend/app/services/contract_service.py` | Server-side schema inference: DataFrame column types, shapes, value ranges, null counts. Uses pandas `.dtypes`, `.describe()`, `.isnull().sum()` | 150 |
| `backend/app/routers/contracts.py` | FastAPI endpoint: POST /api/v1/contracts/infer | 40 |

**Research justification:** Synthesis Section 8 -- "dlt (data load tool) auto-infers schemas from data sources." The Pandera pattern provides the validation model. NBLyzer's abstract interpretation validates feasibility at interactive speed.

### 3.3 Contract validation engine

Before and after cell execution, validate data against contracts.

**Target file:** `apps/notebook/src/contracts/validate.ts`
**Estimated lines:** 120

Validates: column presence, dtype match, nullable violations, range violations, unique violations, allowed value violations. Returns a list of `ContractViolation` objects.

### 3.4 Contract violation display

Show violations inline on the cell with specific error messages.

**Target file:** `apps/notebook/src/contracts/ContractViolationBadge.tsx`
**Estimated lines:** 80

Shows: red border on violated cells, expandable violation list with column-level detail, "Fix" suggestions (e.g., "Column 'age' has 3 null values -- expected non-nullable").

### 3.5 Contract editor UI

Allow users to manually edit contracts via a sidebar panel.

**Target file:** `apps/notebook/src/features/sidebar/ContractPanel.tsx`
**Estimated lines:** 200

Features: table of columns with type dropdowns, nullable toggles, range inputs. Auto-populate from inference. Lock/unlock individual constraints. Export contract as JSON.

### 3.6 Contract inheritance for branches

When a cell is branched (Phase 7), the branch cell inherits the parent cell's output contract. The comparison layer uses contracts to validate that both branches produce comparable outputs.

**Target file:** `apps/notebook/src/contracts/inheritance.ts`
**Estimated lines:** 40

### 3.7 Contract integration with reactive engine

When a contract is present, the reactive execution engine uses the contract's declared inputs for dependency resolution instead of AST-inferred references. This handles the Rex mutation failures.

**Target file:** `apps/notebook/src/engine/reactive/contract-resolver.ts`
**Estimated lines:** 60

**Phase 3 totals:** ~830 new lines, ~8 new files. Contracts are the foundation for Phases 7 (branch/compare) and 8 (agent cells).

---

## Phase 4: Variable Explorer

**Goal:** Build a best-in-class variable explorer that combines Spyder's editing depth, Positron's scale, and Deepnote's profiling, plus novel lineage tracking.

**Research justification:** Synthesis Section 6 identifies 5 variable explorer implementations and 6 gaps that no explorer fills. The recommended architecture is Positron's OpenRPC protocol + Spyder's editing depth + Deepnote's inline profiling + variable lineage tracking (novel).

### 4.1 Variable listing via kernel introspection

Use the Jupyter Kernel Gateway to list all user-defined variables with type, shape, and size.

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/explorer/variable-client.ts` | Client-side API for variable introspection. Sends silent execution requests to kernel. | 80 |
| `backend/app/services/variable_service.py` | Server-side variable inspection: `dir()`, `type()`, `sys.getsizeof()`, `hasattr(v, 'shape')` | 120 |
| `backend/app/routers/variables.py` | FastAPI endpoint: GET /api/v1/variables | 40 |

**Research justification:** Synthesis Section 6 -- Positron's OpenRPC protocol separates frontend viewer from kernel-side data provider. Spyder uses a separate `SpyderKernelComm` channel to avoid IPython message queue contention.

### 4.2 Variable explorer sidebar panel

**Target file:** `apps/notebook/src/features/explorer/VariableExplorer.tsx`
**Estimated lines:** 250

Features:
- List view with columns: name, type, shape/length, size, preview
- Click to expand: scalars show editable value, DataFrames open in viewer (4.3), lists/dicts show tree view
- Type badges with Observatory color coding
- Sort by name/type/size
- Filter by type dropdown
- Search by name
- Auto-refresh after each cell execution

### 4.3 DataFrame viewer

**Target file:** `apps/notebook/src/features/explorer/DataFrameViewer.tsx`
**Estimated lines:** 300

Features:
- Virtual scrolling for millions of rows (react-window or Glide Data Grid)
- Sort by clicking column header (asc/desc/none)
- Filter per column (text input for string columns, range slider for numeric)
- Search across all columns
- Pagination controls (10/25/50/100/all)
- Column statistics row: count, mean, std, min, max, unique, null count
- Sparkline distribution histograms in column headers (Positron pattern)
- Export to CSV
- "Convert to Code" button: generates pandas filter/sort code from current UI state (Positron pattern)

**Research justification:** Synthesis Section 6 -- "Positron's Data Explorer is the current state of the art. Built on the OpenRPC protocol, it separates frontend viewer from kernel-side data provider."

### 4.4 Inline profiling

**Target file:** `apps/notebook/src/features/explorer/InlineProfile.tsx`
**Estimated lines:** 150

Features:
- Per-column: dtype badge, null count bar, distribution histogram (10 bins), unique count
- Per-DataFrame: row count, column count, memory usage, completeness percentage
- Visual null pattern: bar chart showing null percentage per column

**Research justification:** Synthesis Section 6 -- "Deepnote's variable explorer shows column-level distribution histograms, null counts as percentage bars, data-type badges."

### 4.5 Variable lineage tracking (NOVEL)

Track where each variable came from: which cell created it, what cells modified it, what data sources contributed.

**Target file:** `apps/notebook/src/features/explorer/lineage.ts`
**Estimated lines:** 120

Integrates with the reactive dependency graph (Phase 2) to build a per-variable provenance chain. Display as a mini-DAG in the explorer panel.

**Research justification:** Synthesis Section 6 Gap 1 -- "No explorer shows where a variable came from. Provenance is tracked at the notebook level (ProvBook, ISWC 2018) but not at the variable level." This is confirmed novel.

### 4.6 Move shared DataFrame viewer to @ck/ui

The DataFrameViewer component will be used in both the explorer (sidebar) and the DataFrameCell (Phase 1). Move it to the shared UI package.

**Target file:** `packages/@ck/ui/src/DataFrameViewer.tsx`

**Phase 4 totals:** ~1,060 new lines, ~7 new files. Variable lineage tracking is the novel contribution.

---

## Phase 5: Input/Widget Cells

**Goal:** Build reactive input widgets (slider, dropdown, date picker, etc.) that bind to the Phase 2 reactive execution engine. Changing a widget value triggers re-execution of all dependent cells.

**Research justification:** Synthesis Section 5 Tier 3 identifies 40+ widget types across 7 implementations. Marimo's approach is recommended: widgets are reactive variables that trigger re-execution on change (vs. ipywidgets' callback-based model).

### 5.1 Widget cell infrastructure

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `packages/@ck/cells/src/widgets/WidgetCell.tsx` | Base widget cell component -- renders the appropriate widget type and exposes its value to the execution scope | 100 |
| `packages/@ck/cells/src/widgets/types.ts` | Widget type definitions: SliderConfig, DropdownConfig, DatePickerConfig, etc. | 80 |
| `packages/@ck/cells/src/widgets/widget-registry.ts` | Registry mapping widget type string to component | 40 |

### 5.2 Core widget components

| File | Widget | Est. Lines |
|------|--------|-----------|
| `packages/@ck/cells/src/widgets/SliderWidget.tsx` | Continuous/discrete slider with min/max/step/label | 60 |
| `packages/@ck/cells/src/widgets/DropdownWidget.tsx` | Single-select dropdown with search | 50 |
| `packages/@ck/cells/src/widgets/MultiSelectWidget.tsx` | Multi-select with checkboxes + search | 60 |
| `packages/@ck/cells/src/widgets/DatePickerWidget.tsx` | Date/datetime picker with range support | 70 |
| `packages/@ck/cells/src/widgets/TextInputWidget.tsx` | Single-line and multi-line text input | 40 |
| `packages/@ck/cells/src/widgets/ToggleWidget.tsx` | Boolean toggle switch | 30 |
| `packages/@ck/cells/src/widgets/FileUploadWidget.tsx` | File upload with drag-and-drop, type filtering | 80 |
| `packages/@ck/cells/src/widgets/NumberInputWidget.tsx` | Numeric input with step, min/max validation | 40 |

### 5.3 Reactive binding integration

When a widget value changes, inject the new value into the kernel execution scope and trigger the reactive cascade.

**Target file:** `apps/notebook/src/engine/reactive/widget-binding.ts`
**Estimated lines:** 80

Logic: Widget cell defines a variable (e.g., `threshold = 0.5`). When the slider moves, the variable is updated in the kernel scope via silent execution (`threshold = 0.7`), then the staleness engine marks all cells referencing `threshold` as stale and re-executes them.

**Research justification:** Synthesis Section 5 Tier 3 -- "Marimo's approach is recommended: widgets are reactive variables that trigger re-execution of dependent cells on change."

### 5.4 Widget configuration UI

**Target file:** `packages/@ck/cells/src/widgets/WidgetConfig.tsx`
**Estimated lines:** 120

Config panel that appears when a widget cell is selected: widget type selector, label, variable name, min/max/step (for sliders), options list (for dropdowns), default value.

**Phase 5 totals:** ~850 new lines, ~12 new files. Widgets are a prerequisite for interactive dashboards and are used by the living pipeline (Phase 9).

### 5.5 Reactivity paradigm selection

The research synthesis documents 7 distinct widget reactivity paradigms across platforms. ContextKeeper adopts one primary paradigm with one reference pattern for future JS cell support.

**RECOMMENDED -- Marimo UIElementRegistry pattern:**
- Each widget type extends a generic `UIElement<S, T>` where S is the internal state type and T is the exposed value type
- Widget registers its value in the global execution scope under its declared variable name
- Value change triggers DAG re-execution via the Phase 2 reactive engine (staleness propagation)
- `UIElementRegistry` tracks widget objects by `object_id`, enabling hierarchical widgets (e.g., a form containing multiple inputs)
- Lens mechanism allows nested widget access (e.g., `form.value["field_name"]`)
- Works in Pyodide/browser mode -- no kernel comm channel required
- Scale: supports 25+ widget types (Marimo's current count) with a single reactivity mechanism
- Path: `apps/notebook/src/engine/reactive/widget-registry.ts`

**REFERENCE -- Observable Generators.input pattern (for JS cells if added later):**
- `viewof` protocol creates dual variables: DOM element + extracted value
- `Generators.input()` async generator yields on every DOM `input` event
- Any DOM element with `.value` property and `input` event is automatically compatible
- Entirely client-side, zero server round-trips
- Relevant only if/when JavaScript cells gain first-class reactive support

**NOT RECOMMENDED -- ipywidgets comm protocol:**
- Requires active kernel with ZMQ/WebSocket comm channel
- Heavy serialization overhead (JSON over comm messages, delta compression with `hold_sync()`)
- 40+ widget types but tightly coupled to Jupyter kernel infrastructure
- Not Pyodide-compatible without significant shimming
- `sync=True` traitlets create implicit bidirectional state that conflicts with DAG-based reactivity
- Legacy ecosystem value (ipyleaflet, bqplot, ipyvolume) but not worth the architectural cost for a new platform

---

## Phase 6: Pipeline Visualization and DAG View

**Goal:** Provide a visual DAG of cell dependencies and allow toggling between linear notebook view and spatial DAG view.

**Research justification:** Synthesis Section 4 -- Kedro-Viz provides pipeline visualization. The reactive dependency graph from Phase 2 provides the data; this phase provides the rendering.

### 6.1 DAG renderer

Use React Flow (already a dependency in data-canvas) to render the cell dependency graph as an interactive DAG.

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/pipeline/DagView.tsx` | React Flow canvas rendering cells as nodes, dependencies as edges | 250 |
| `apps/notebook/src/features/pipeline/DagNode.tsx` | Custom React Flow node for cells -- shows cell type icon, title, status (idle/running/stale/error) | 100 |
| `apps/notebook/src/features/pipeline/DagEdge.tsx` | Custom edge with variable name label | 40 |
| `apps/notebook/src/features/pipeline/dag-layout.ts` | Auto-layout algorithm (Dagre/ELK) for positioning nodes | 80 |

### 6.2 Linear/DAG view toggle

**Target file:** `apps/notebook/src/components/NotebookToolbar.tsx` (modify)
**Estimated change:** ~30 lines

Toggle button: "Linear | DAG". Linear view shows the standard cell list. DAG view shows the React Flow canvas.

### 6.3 Pipeline execution controls

**Target files:**
- `apps/notebook/src/features/pipeline/PipelineControls.tsx` (new, ~100 lines)

Features: Run entire pipeline, run from selected cell, pause/resume, kill execution. Status indicators per cell in the DAG view.

### 6.4 Pipeline status sidebar panel

**Target file:** `apps/notebook/src/features/sidebar/PipelinePanel.tsx`
**Estimated lines:** 120

Shows: execution status summary (N cells idle, M running, K errored), total execution time, last run timestamp, execution queue visualization.

**Phase 6 totals:** ~720 new lines, ~6 new files. Depends on Phase 2 (dependency graph).

---

## Phase 7: Branch/Compare/Replace

**Goal:** Implement the signature differentiating feature -- fork any cell into parallel alternatives, execute both on the same data, compare with configurable statistical tests, and optionally auto-promote the winner.

**Research justification:** Synthesis Section 8 Feature 2 confirms this as PARTIAL prior art -- "No platform combines branch creation, parallel execution on the same data, automated statistical comparison, and branch replacement in a single workflow." Synthesis Section 7 provides the statistical test battery.

### 7.1 Statistical testing package

Create a shared stats package for use by both notebook and future agent canvas.

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `packages/@ck/stats/package.json` | Package config | 15 |
| `packages/@ck/stats/tsconfig.json` | TS config | 10 |
| `packages/@ck/stats/src/index.ts` | Barrel export | 10 |
| `packages/@ck/stats/src/paired-ttest.ts` | Paired t-test for regression comparison | 60 |
| `packages/@ck/stats/src/mcnemar.ts` | McNemar's test for classification comparison | 60 |
| `packages/@ck/stats/src/wilcoxon.ts` | Wilcoxon signed-rank test (non-parametric default) | 80 |
| `packages/@ck/stats/src/diebold-mariano.ts` | Diebold-Mariano test for time series forecasts | 80 |
| `packages/@ck/stats/src/sequential.ts` | Sequential probability ratio test (SPRT) for valid-at-any-sample-size | 100 |
| `packages/@ck/stats/src/bootstrap.ts` | Bootstrap confidence intervals for LLM evaluation metrics | 80 |
| `packages/@ck/stats/src/test-selector.ts` | Auto-select appropriate test based on output type (regression/classification/LLM/numeric/time-series) | 60 |

**Research justification:** Synthesis Section 7 -- "No tracker includes built-in statistical significance testing for experiment comparison. Users must export metrics to scipy, statsmodels, or mlxtend for statistical testing. This is the central gap ContextKeeper's Branch/Compare/Replace addresses." Tests cited: Dietterich 1998 (paired t-test), Demsar 2006 (McNemar's), Benavoli 2017 (Wilcoxon), Diebold & Mariano 1995, Wald 1945 (SPRT).

### 7.2 Branch creation

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/branch/branch-store.ts` | Zustand store for branches: branch metadata, active branches, comparison results | 120 |
| `apps/notebook/src/features/branch/branch-create.ts` | Create a branch: duplicate cell, assign branch ID, inherit contract (Phase 3) | 80 |
| `apps/notebook/src/features/branch/BranchIndicator.tsx` | Visual indicator on branched cells (A/B labels, branch color coding) | 60 |

### 7.3 Parallel execution

**Target file:** `apps/notebook/src/features/branch/branch-execute.ts`
**Estimated lines:** 120

Execute both branches with identical input data. For server-side execution, run in parallel (two kernel requests). For Pyodide, run sequentially. Collect outputs for comparison.

### 7.4 Comparison layer

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/branch/compare.ts` | Compare branch outputs using the appropriate statistical test. Auto-detect output type (uses contracts from Phase 3). | 100 |
| `apps/notebook/src/features/branch/ComparisonPanel.tsx` | UI for comparison results: test name, p-value, effect size, confidence interval, winner indicator, metric visualization | 200 |

### 7.5 Replace system

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/branch/replace.ts` | Replace logic: promote winner to main, archive loser. 4 modes: auto, notify, suggest, never. | 80 |
| `apps/notebook/src/features/branch/ReplaceConfig.tsx` | Configuration UI for replace mode and significance threshold (default p < 0.05) | 80 |

### 7.6 DeepEval integration for LLM branches

**Target file:** `apps/notebook/src/features/branch/llm-eval.ts`
**Estimated lines:** 100

Evaluate LLM branch outputs using DeepEval metrics: faithfulness, relevancy, coherence, bias, toxicity. Uses a judge LLM (70B class per synthesis model routing strategy) to score outputs.

**Phase 7 totals:** ~1,545 new lines, ~14 new files. This is the flagship novel feature.

---

## Phase 8: Agent Cells

**Goal:** Implement autonomous AI agents as first-class DAG nodes in the notebook's reactive execution graph. This is confirmed novel -- no existing platform implements this (Synthesis Section 8 Feature 5).

**Research justification:** Synthesis Section 8 Feature 5 -- "CONFIRMED NOVEL. All existing agent frameworks are standalone -- agents run as separate processes or services, not as nodes in a notebook's reactive dependency graph."

### 8.1 Agent cell component

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `packages/@ck/cells/src/AgentCell.tsx` | Agent cell UI: tool config, planning steps display, cost tracker, output display | 200 |
| `packages/@ck/cells/src/AgentCellConfig.tsx` | Config panel: model selector, tool list, system prompt, max iterations, cost limit | 120 |

### 8.2 Agent execution engine

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `packages/@ck/ai/src/agent-runner.ts` | Agent execution loop: plan -> execute tool -> observe -> repeat. Integrates with @ck/ai for LLM calls. | 250 |
| `packages/@ck/ai/src/agent-types.ts` | Agent type definitions: AgentConfig, AgentStep, AgentTool, AgentResult | 80 |
| `packages/@ck/ai/src/agent-tools.ts` | Built-in tools: execute_python (runs code in kernel), query_dataframe, read_variable, write_variable, call_api | 150 |

### 8.3 Agent as reactive DAG node

Integrate agent cells into the Phase 2 reactive execution engine. When upstream cells produce new data, the agent re-executes with the new inputs.

**Target file:** `apps/notebook/src/engine/reactive/agent-node.ts`
**Estimated lines:** 80

Logic: Agent cell declares typed inputs (from contract) and typed outputs. The reactive engine treats it like any other cell -- upstream changes trigger re-execution. The agent's tool calls can themselves trigger downstream cells.

### 8.4 Agent cost tracking

**Target file:** `apps/notebook/src/features/metrics/agent-cost.ts`
**Estimated lines:** 60

Track: tokens consumed (input + output), model used, cost per execution, cumulative cost. Display in agent cell footer and in a sidebar metrics panel.

**Phase 8 totals:** ~940 new lines, ~7 new files. Depends on Phase 2 (reactive engine) and Phase 3 (contracts).

---

## Phase 9: Living Pipeline

**Goal:** Implement all 7 execution modes from the architecture vision, transforming the notebook from a static document into a living computational pipeline.

**Research justification:** Synthesis Section 8 Feature 1 -- "PARTIAL prior art. No notebook platform has cells that continuously execute on streaming data with reactive dependency propagation." Tanimoto 1990 defines Level 4 liveness (continuous execution) -- no current notebook achieves this.

### 9.1 Execution mode infrastructure

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/pipeline/execution-modes.ts` | Mode definitions and mode-switching logic. 7 modes: manual, reactive, scheduled, event-driven, streaming, continuous, autonomous. | 120 |
| `apps/notebook/src/features/pipeline/ExecutionModeSelector.tsx` | UI for selecting execution mode per-notebook and per-cell | 80 |

### 9.2 Scheduled execution

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/pipeline/scheduler.ts` | Client-side cron scheduler using `croner` npm package. Triggers pipeline execution on schedule. | 100 |
| `apps/notebook/src/features/pipeline/ScheduleConfig.tsx` | Cron expression editor with presets (every 1min, 5min, hourly, daily, weekly, monthly) | 80 |
| `backend/app/services/scheduler_service.py` | Server-side scheduled execution for headless pipelines | 150 |

### 9.3 Event-driven execution

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/pipeline/event-triggers.ts` | Event source configuration: webhook URL, file watcher, API poll, database trigger | 100 |
| `apps/notebook/src/features/pipeline/EventTriggerConfig.tsx` | UI for configuring event triggers | 80 |
| `backend/app/routers/webhooks.py` | FastAPI endpoint for incoming webhooks that trigger notebook execution | 60 |

### 9.4 Streaming execution

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/pipeline/streaming.ts` | Row-by-row processing pipeline. Backpressure handling (if processing is slower than input, queue rows). Buffer size configuration. | 200 |
| `apps/notebook/src/features/pipeline/StreamStatus.tsx` | Real-time streaming status: rows/sec, buffer depth, lag, errors | 80 |

### 9.5 Execution metrics and drift detection

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/metrics/execution-metrics.ts` | Track per-cell: execution time history, memory usage, output shape history, output distribution summary | 100 |
| `apps/notebook/src/features/metrics/drift-detector.ts` | Detect drift in cell output distributions across runs. Uses KS test for continuous, chi-squared for categorical. Alerts when p < 0.05. | 120 |
| `apps/notebook/src/features/metrics/MetricsPanel.tsx` | Sidebar panel: execution time sparklines, drift alerts, memory usage | 150 |

**Research justification:** Synthesis Section 8 Feature 4 -- "No platform tracks cell-level metrics across runs and automatically detects drift. Integrated cell-level metric tracking with automatic drift detection is novel."

### 9.6 Continuous execution mode

**Target file:** `apps/notebook/src/features/pipeline/continuous.ts`
**Estimated lines:** 80

Infinite loop execution: pipeline runs continuously with configurable interval between runs. Backpressure: if a run takes longer than the interval, skip the next scheduled run.

**Phase 9 totals:** ~1,500 new lines, ~12 new files. Depends on Phase 2 (reactive engine) and Phase 6 (pipeline visualization).

---

## Phase 10: Advanced Novel Features

**Goal:** Implement remaining novel features that provide competitive differentiation beyond any existing platform.

### 10.1 Tournament cells

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `packages/@ck/cells/src/TournamentCell.tsx` | N-way method comparison cell. Users define N code variants; all execute on the same data. Statistical testing (Phase 7 @ck/stats) selects the winner with confidence intervals. | 250 |
| `packages/@ck/cells/src/TournamentConfig.tsx` | Config: add/remove variants, select evaluation metric, set significance threshold, choose test type | 120 |
| `apps/notebook/src/features/branch/tournament-execute.ts` | Execute all tournament variants, collect results, run pairwise statistical tests, produce ranking | 150 |

**Research justification:** Synthesis Section 8 Feature 3 -- "PyCaret ranks by metric value without significance testing. Tournament cells add statistical rigor to model comparison."

### 10.2 Decision/Router cells

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `packages/@ck/cells/src/DecisionCell.tsx` | Conditional routing cell. Evaluates a Python expression; routes execution to one of N downstream branches based on result. | 120 |
| `packages/@ck/cells/src/DecisionConfig.tsx` | Config: condition expression, branch labels, default branch | 60 |

**Research justification:** Synthesis Section 8 Feature 6 -- "No notebook has a cell that conditionally routes execution to different downstream cells based on runtime evaluation."

### 10.3 Fine-tune cells

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `packages/@ck/cells/src/FineTuneDatasetCell.tsx` | Dataset builder cell: select columns, define train/val/test split, format for fine-tuning (JSONL, CSV) | 150 |
| `packages/@ck/cells/src/FineTuneTrainCell.tsx` | Training job cell: model selector, hyperparameters, launch training, monitor progress | 120 |
| `packages/@ck/cells/src/FineTuneEvalCell.tsx` | Model evaluation cell: benchmark against base model, display metrics | 100 |

### 10.4 Voice-to-code

Port CK_Voice from the monolith (ck-universal.js) to the modern stack.

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/voice/voice-recognizer.ts` | Web Speech API integration. Continuous dictation mode. Language detection. | 120 |
| `apps/notebook/src/features/voice/VoiceMicButton.tsx` | Mic button component for cell toolbars | 40 |
| `apps/notebook/src/features/voice/voice-to-code.ts` | Post-process speech text through LLM to generate code. Uses @ck/ai. | 80 |

**Research justification:** Audit Section 15 -- "Voice-to-code (CK_Voice) -- mic button on every textarea" listed as not yet ported from monolith.

### 10.5 Transactional undo

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/undo/transaction-log.ts` | Transaction log: records cell changes + execution state as atomic units. Supports undo/redo of multi-cell operations. | 150 |
| `apps/notebook/src/features/undo/checkpoint.ts` | Checkpoint system: snapshot kernel state at defined points. Restore to checkpoint reverts both cell content and kernel variables. | 120 |

**Research justification:** Synthesis Section 8 Feature 9 -- Kishu (VLDB 2024) provides session-level checkpoint/restore. ContextKeeper extends this with transactional semantics (atomic commit/rollback of multi-cell operations).

**Phase 10 totals:** ~1,480 new lines, ~14 new files.

---

## Phase 11: Export, Deployment, Production

**Goal:** Enable notebooks to be exported, deployed, and run in production environments.

### 11.1 .cknotebook file format

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/format/cknotebook-spec.ts` | File format specification: JSON structure with cells, contracts, branches, metadata, execution mode config | 80 |
| `apps/notebook/src/features/format/cknotebook-serialize.ts` | Serialize notebook state to .cknotebook format | 100 |
| `apps/notebook/src/features/format/cknotebook-deserialize.ts` | Deserialize .cknotebook file to notebook state | 100 |

The .cknotebook format stores: cell source + type + metadata, contracts, branch configurations, execution mode settings, variable explorer snapshots, execution metrics history, DAG layout positions.

### 11.2 Enhanced export formats

Extend the existing 8 export formats with production-oriented outputs.

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/export/pdf-export.ts` | Enhanced PDF export with proper pagination, table of contents, header/footer | 150 |
| `apps/notebook/src/features/export/pptx-export.ts` | PowerPoint export: one slide per cell, formatted code blocks, chart images | 200 |
| `apps/notebook/src/features/export/docker-export.ts` | Export notebook as Docker container: Dockerfile + requirements.txt + notebook.py + entrypoint.sh | 120 |
| `apps/notebook/src/features/export/api-export.ts` | Export notebook as FastAPI endpoint: wraps pipeline cells as API routes with typed request/response schemas | 150 |

### 11.3 Dashboard mode

Convert notebook cells into a dashboard layout (grid of outputs without code).

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/dashboard/DashboardView.tsx` | Grid layout of cell outputs using react-grid-layout. Drag-and-drop resize/reposition. | 200 |
| `apps/notebook/src/features/dashboard/DashboardConfig.tsx` | Config: select which cells to include, layout presets, auto-refresh interval | 80 |

### 11.4 Scheduled production execution

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `backend/app/services/production_runner.py` | Headless notebook execution service: load .cknotebook, execute all cells, store results, send alerts on failure | 200 |
| `backend/app/routers/production.py` | FastAPI endpoints: POST /api/v1/production/run, GET /api/v1/production/status, GET /api/v1/production/history | 80 |

**Phase 11 totals:** ~1,460 new lines, ~11 new files.

---

## Phase 12: Polish, Performance, and Cell-Level RBAC

**Goal:** Production hardening, performance optimization, and the second confirmed novel feature (Cell-Level RBAC).

### 12.1 Cell-Level RBAC

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `apps/notebook/src/features/rbac/cell-permissions.ts` | Permission model: read/write/execute per cell per user/role. Integration with reactive engine -- protected cells use cached results when the requesting user lacks execute permission. | 150 |
| `apps/notebook/src/features/rbac/PermissionBadge.tsx` | Visual indicator on protected cells: lock icon, permission level badge | 40 |
| `apps/notebook/src/features/rbac/PermissionEditor.tsx` | UI for setting cell permissions: user list, role list, permission checkboxes | 100 |
| `backend/app/services/rbac_service.py` | Server-side permission checking and enforcement | 120 |
| `backend/app/models/cell_permission.py` | SQLAlchemy model for cell permissions | 40 |

**Research justification:** Synthesis Section 8 Feature 11 -- "CONFIRMED NOVEL. No computational notebook implements access control at the cell level."

### 12.2 Pyodide browser fallback

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `packages/@ck/kernel/src/pyodide-client.ts` | Pyodide execution engine: load Pyodide in Web Worker, execute Python cells, return outputs. Falls back to this when Jupyter Kernel Gateway is unavailable. | 250 |
| `packages/@ck/kernel/src/pyodide-worker.ts` | Web Worker script: loads Pyodide, handles message-based execution requests | 150 |

**Research justification:** Synthesis Section 13 -- "Pyodide single-threaded execution. Mitigation: run Pyodide in a Web Worker with Comlink."

### 12.3 Multi-kernel support

**Target files:**

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `packages/@ck/kernel/src/multi-kernel.ts` | Kernel manager: maintain connections to multiple kernels (Python, R, Julia). Route cell execution to the appropriate kernel based on cell language. | 150 |
| `apps/notebook/src/features/sidebar/KernelPanel.tsx` | Sidebar panel: kernel status, language, memory usage, restart/interrupt per kernel | 100 |

### 12.4 Performance optimization

- Virtual scrolling for notebooks with 100+ cells (react-window)
- Lazy loading of cell type components via dynamic `import()`
- Output streaming optimization (batch DOM updates during rapid output)
- Keyboard shortcut debouncing
- Monaco editor instance pooling (reuse editors for same-language cells)

**Target files:**
- `apps/notebook/src/components/VirtualCellList.tsx` (~120 lines)
- `packages/@ck/cells/src/lazy-registry.ts` (~60 lines)

### 12.5 Presentation mode completion

Complete the presentation mode with slide navigation, full-screen toggle, slide counter, speaker notes.

**Target file:** `apps/notebook/src/features/presentation/PresentationView.tsx`
**Estimated lines:** 150

### 12.6 TOC/Outline panel

Auto-generated table of contents from markdown headings with click-to-navigate.

**Target file:** `apps/notebook/src/features/sidebar/OutlinePanel.tsx`
**Estimated lines:** 80

### 12.7 Notebook metadata panel

Title, author, description, tags, kernel spec, created/modified dates editor.

**Target file:** `apps/notebook/src/features/sidebar/MetadataPanel.tsx`
**Estimated lines:** 100

**Phase 12 totals:** ~1,510 new lines, ~12 new files.

---

## Appendix A: File Target Map

Complete inventory of every file created or moved across all phases.

| Feature | Target Path | Status | Phase | Complexity |
|---------|------------|--------|-------|-----------|
| Notebook app scaffold | `apps/notebook/package.json` | New | 0 | S |
| Notebook app scaffold | `apps/notebook/vite.config.ts` | New | 0 | S |
| Notebook app scaffold | `apps/notebook/tsconfig.json` | New | 0 | S |
| Notebook app scaffold | `apps/notebook/index.html` | New | 0 | S |
| Notebook app scaffold | `apps/notebook/src/main.tsx` | New | 0 | S |
| Notebook app scaffold | `apps/notebook/src/App.tsx` | New | 0 | S |
| Notebook app scaffold | `apps/notebook/src/styles/observatory.css` | New | 0 | S |
| Cell package | `packages/@ck/cells/package.json` | New | 0 | S |
| Cell package | `packages/@ck/cells/tsconfig.json` | New | 0 | S |
| Cell package | `packages/@ck/cells/src/index.ts` | New | 0 | S |
| Cell.tsx | `packages/@ck/cells/src/Cell.tsx` | Move | 0 | M |
| CodeCell.tsx | `packages/@ck/cells/src/CodeCell.tsx` | Move | 0 | S |
| MarkdownCell.tsx | `packages/@ck/cells/src/MarkdownCell.tsx` | Move | 0 | S |
| SqlCell.tsx | `packages/@ck/cells/src/SqlCell.tsx` | Move | 0 | S |
| CellOutput.tsx | `packages/@ck/cells/src/CellOutput.tsx` | Move | 0 | S |
| CellToolbar.tsx | `packages/@ck/cells/src/CellToolbar.tsx` | Move | 0 | M |
| BetweenCellMenu.tsx | `packages/@ck/cells/src/BetweenCellMenu.tsx` | Move | 0 | M |
| DataFrameRenderer.tsx | `packages/@ck/cells/src/DataFrameRenderer.tsx` | Move | 0 | M |
| Cell types | `packages/@ck/cells/src/types.ts` | Move | 0 | S |
| Kernel package | `packages/@ck/kernel/package.json` | New | 0 | S |
| Kernel package | `packages/@ck/kernel/tsconfig.json` | New | 0 | S |
| Kernel client | `packages/@ck/kernel/src/kernel-client.ts` | Move | 0 | L |
| Kernel types | `packages/@ck/kernel/src/types.ts` | Move | 0 | S |
| Notebook types | `packages/@ck/kernel/src/notebook-types.ts` | Move | 0 | S |
| Kernel barrel | `packages/@ck/kernel/src/index.ts` | New | 0 | S |
| Bridge package | `packages/@ck/bridge/package.json` | New | 0 | S |
| Bridge core | `packages/@ck/bridge/src/bridge.ts` | New | 0 | M |
| Bridge types | `packages/@ck/bridge/src/types.ts` | New | 0 | S |
| Bridge hooks | `packages/@ck/bridge/src/hooks.ts` | New | 0 | S |
| Bridge barrel | `packages/@ck/bridge/src/index.ts` | New | 0 | S |
| Notebook store | `apps/notebook/src/features/notebook-store.ts` | Move | 0 | M |
| Notebook execute | `apps/notebook/src/features/notebook-execute.ts` | Move | 0 | M |
| Notebook keyboard | `apps/notebook/src/features/notebook-keyboard.ts` | Move | 0 | L |
| Notebook save | `apps/notebook/src/features/notebook-save.ts` | Move | 0 | M |
| Notebook export | `apps/notebook/src/features/notebook-export.ts` | Move | 0 | L |
| Notebook import | `apps/notebook/src/features/notebook-import.ts` | Move | 0 | M |
| Notebook modes | `apps/notebook/src/features/notebook-modes.ts` | Move | 0 | M |
| Cell operations | `apps/notebook/src/lib/cell-operations.ts` | Move | 0 | M |
| Cell execution | `apps/notebook/src/lib/cell-execution.ts` | Move | 0 | S |
| Cell history | `apps/notebook/src/lib/cell-history.ts` | Move | 0 | S |
| NotebookPage | `apps/notebook/src/pages/NotebookPage.tsx` | Move | 0 | M |
| CellListPanel | `apps/notebook/src/features/sidebar/CellListPanel.tsx` | Move | 0 | M |
| MarkdownCell upgrade | `packages/@ck/cells/src/MarkdownCell.tsx` | Modify | 1 | S |
| PromptCell | `packages/@ck/cells/src/PromptCell.tsx` | New | 1 | M |
| PromptCellConfig | `packages/@ck/cells/src/PromptCellConfig.tsx` | New | 1 | M |
| VizCell | `packages/@ck/cells/src/VizCell.tsx` | New | 1 | L |
| VizCellConfig | `packages/@ck/cells/src/VizCellConfig.tsx` | New | 1 | M |
| Chart recommend | `packages/@ck/cells/src/chart-recommend.ts` | New | 1 | S |
| MermaidCell | `packages/@ck/cells/src/MermaidCell.tsx` | New | 1 | S |
| HTMLCell | `packages/@ck/cells/src/HTMLCell.tsx` | New | 1 | S |
| LaTeXCell | `packages/@ck/cells/src/LaTeXCell.tsx` | New | 1 | S |
| ScratchCell | `packages/@ck/cells/src/ScratchCell.tsx` | New | 1 | S |
| FormCell placeholder | `packages/@ck/cells/src/FormCell.tsx` | New | 1 | S |
| DataFrameCell | `packages/@ck/cells/src/DataFrameCell.tsx` | New | 1 | S |
| MetricCell | `packages/@ck/cells/src/MetricCell.tsx` | New | 1 | M |
| ProfileCell | `packages/@ck/cells/src/ProfileCell.tsx` | New | 1 | M |
| MapCell | `packages/@ck/cells/src/MapCell.tsx` | New | 1 | L |
| NotebookToolbar | `apps/notebook/src/components/NotebookToolbar.tsx` | New | 1 | M |
| SearchReplace | `apps/notebook/src/components/SearchReplace.tsx` | New | 1 | M |
| AST extractor client | `apps/notebook/src/engine/reactive/ast-extract.ts` | New | 2 | S |
| AST service | `backend/app/services/ast_service.py` | New | 2 | L |
| AST router | `backend/app/routers/ast.py` | New | 2 | S |
| Dependency graph | `apps/notebook/src/engine/reactive/dep-graph.ts` | New | 2 | M |
| Topo sort | `apps/notebook/src/engine/reactive/topo-sort.ts` | New | 2 | S |
| Staleness | `apps/notebook/src/engine/reactive/staleness.ts` | New | 2 | M |
| Cascade executor | `apps/notebook/src/engine/reactive/cascade-executor.ts` | New | 2 | L |
| Output cache | `apps/notebook/src/engine/reactive/output-cache.ts` | New | 2 | M |
| Reactive barrel | `apps/notebook/src/engine/reactive/index.ts` | New | 2 | S |
| DepGraph panel | `apps/notebook/src/features/sidebar/DepGraphPanel.tsx` | New | 2 | M |
| Contract types | `apps/notebook/src/contracts/types.ts` | New | 3 | S |
| Contract infer client | `apps/notebook/src/contracts/infer.ts` | New | 3 | S |
| Contract service | `backend/app/services/contract_service.py` | New | 3 | M |
| Contract router | `backend/app/routers/contracts.py` | New | 3 | S |
| Contract validate | `apps/notebook/src/contracts/validate.ts` | New | 3 | M |
| Contract violation badge | `apps/notebook/src/contracts/ContractViolationBadge.tsx` | New | 3 | S |
| Contract panel | `apps/notebook/src/features/sidebar/ContractPanel.tsx` | New | 3 | L |
| Contract inheritance | `apps/notebook/src/contracts/inheritance.ts` | New | 3 | S |
| Contract resolver | `apps/notebook/src/engine/reactive/contract-resolver.ts` | New | 3 | S |
| Variable client | `apps/notebook/src/features/explorer/variable-client.ts` | New | 4 | S |
| Variable service | `backend/app/services/variable_service.py` | New | 4 | M |
| Variable router | `backend/app/routers/variables.py` | New | 4 | S |
| Variable explorer | `apps/notebook/src/features/explorer/VariableExplorer.tsx` | New | 4 | L |
| DataFrame viewer | `apps/notebook/src/features/explorer/DataFrameViewer.tsx` | New | 4 | XL |
| Inline profile | `apps/notebook/src/features/explorer/InlineProfile.tsx` | New | 4 | M |
| Lineage tracking | `apps/notebook/src/features/explorer/lineage.ts` | New | 4 | M |
| Shared DataFrame viewer | `packages/@ck/ui/src/DataFrameViewer.tsx` | New | 4 | XL |
| Widget cell base | `packages/@ck/cells/src/widgets/WidgetCell.tsx` | New | 5 | M |
| Widget types | `packages/@ck/cells/src/widgets/types.ts` | New | 5 | S |
| Widget registry | `packages/@ck/cells/src/widgets/widget-registry.ts` | New | 5 | S |
| Slider widget | `packages/@ck/cells/src/widgets/SliderWidget.tsx` | New | 5 | S |
| Dropdown widget | `packages/@ck/cells/src/widgets/DropdownWidget.tsx` | New | 5 | S |
| MultiSelect widget | `packages/@ck/cells/src/widgets/MultiSelectWidget.tsx` | New | 5 | S |
| DatePicker widget | `packages/@ck/cells/src/widgets/DatePickerWidget.tsx` | New | 5 | M |
| TextInput widget | `packages/@ck/cells/src/widgets/TextInputWidget.tsx` | New | 5 | S |
| Toggle widget | `packages/@ck/cells/src/widgets/ToggleWidget.tsx` | New | 5 | S |
| FileUpload widget | `packages/@ck/cells/src/widgets/FileUploadWidget.tsx` | New | 5 | M |
| NumberInput widget | `packages/@ck/cells/src/widgets/NumberInputWidget.tsx` | New | 5 | S |
| Widget binding | `apps/notebook/src/engine/reactive/widget-binding.ts` | New | 5 | M |
| Widget config | `packages/@ck/cells/src/widgets/WidgetConfig.tsx` | New | 5 | M |
| DAG view | `apps/notebook/src/features/pipeline/DagView.tsx` | New | 6 | L |
| DAG node | `apps/notebook/src/features/pipeline/DagNode.tsx` | New | 6 | M |
| DAG edge | `apps/notebook/src/features/pipeline/DagEdge.tsx` | New | 6 | S |
| DAG layout | `apps/notebook/src/features/pipeline/dag-layout.ts` | New | 6 | M |
| Pipeline controls | `apps/notebook/src/features/pipeline/PipelineControls.tsx` | New | 6 | M |
| Pipeline panel | `apps/notebook/src/features/sidebar/PipelinePanel.tsx` | New | 6 | M |
| Stats: paired t-test | `packages/@ck/stats/src/paired-ttest.ts` | New | 7 | S |
| Stats: McNemar | `packages/@ck/stats/src/mcnemar.ts` | New | 7 | S |
| Stats: Wilcoxon | `packages/@ck/stats/src/wilcoxon.ts` | New | 7 | M |
| Stats: Diebold-Mariano | `packages/@ck/stats/src/diebold-mariano.ts` | New | 7 | M |
| Stats: SPRT | `packages/@ck/stats/src/sequential.ts` | New | 7 | L |
| Stats: bootstrap | `packages/@ck/stats/src/bootstrap.ts` | New | 7 | M |
| Stats: test selector | `packages/@ck/stats/src/test-selector.ts` | New | 7 | S |
| Branch store | `apps/notebook/src/features/branch/branch-store.ts` | New | 7 | M |
| Branch create | `apps/notebook/src/features/branch/branch-create.ts` | New | 7 | M |
| Branch indicator | `apps/notebook/src/features/branch/BranchIndicator.tsx` | New | 7 | S |
| Branch execute | `apps/notebook/src/features/branch/branch-execute.ts` | New | 7 | L |
| Branch compare | `apps/notebook/src/features/branch/compare.ts` | New | 7 | M |
| Comparison panel | `apps/notebook/src/features/branch/ComparisonPanel.tsx` | New | 7 | L |
| Branch replace | `apps/notebook/src/features/branch/replace.ts` | New | 7 | M |
| Replace config | `apps/notebook/src/features/branch/ReplaceConfig.tsx` | New | 7 | S |
| LLM eval | `apps/notebook/src/features/branch/llm-eval.ts` | New | 7 | M |
| Agent cell | `packages/@ck/cells/src/AgentCell.tsx` | New | 8 | L |
| Agent cell config | `packages/@ck/cells/src/AgentCellConfig.tsx` | New | 8 | M |
| Agent runner | `packages/@ck/ai/src/agent-runner.ts` | New | 8 | XL |
| Agent types | `packages/@ck/ai/src/agent-types.ts` | New | 8 | S |
| Agent tools | `packages/@ck/ai/src/agent-tools.ts` | New | 8 | M |
| Agent DAG node | `apps/notebook/src/engine/reactive/agent-node.ts` | New | 8 | M |
| Agent cost tracking | `apps/notebook/src/features/metrics/agent-cost.ts` | New | 8 | S |
| Execution modes | `apps/notebook/src/features/pipeline/execution-modes.ts` | New | 9 | M |
| Execution mode selector | `apps/notebook/src/features/pipeline/ExecutionModeSelector.tsx` | New | 9 | S |
| Scheduler | `apps/notebook/src/features/pipeline/scheduler.ts` | New | 9 | M |
| Schedule config | `apps/notebook/src/features/pipeline/ScheduleConfig.tsx` | New | 9 | S |
| Scheduler service | `backend/app/services/scheduler_service.py` | New | 9 | M |
| Event triggers | `apps/notebook/src/features/pipeline/event-triggers.ts` | New | 9 | M |
| Event trigger config | `apps/notebook/src/features/pipeline/EventTriggerConfig.tsx` | New | 9 | S |
| Webhooks router | `backend/app/routers/webhooks.py` | New | 9 | S |
| Streaming | `apps/notebook/src/features/pipeline/streaming.ts` | New | 9 | L |
| Stream status | `apps/notebook/src/features/pipeline/StreamStatus.tsx` | New | 9 | S |
| Execution metrics | `apps/notebook/src/features/metrics/execution-metrics.ts` | New | 9 | M |
| Drift detector | `apps/notebook/src/features/metrics/drift-detector.ts` | New | 9 | M |
| Metrics panel | `apps/notebook/src/features/metrics/MetricsPanel.tsx` | New | 9 | M |
| Continuous exec | `apps/notebook/src/features/pipeline/continuous.ts` | New | 9 | S |
| Tournament cell | `packages/@ck/cells/src/TournamentCell.tsx` | New | 10 | L |
| Tournament config | `packages/@ck/cells/src/TournamentConfig.tsx` | New | 10 | M |
| Tournament execute | `apps/notebook/src/features/branch/tournament-execute.ts` | New | 10 | M |
| Decision cell | `packages/@ck/cells/src/DecisionCell.tsx` | New | 10 | M |
| Decision config | `packages/@ck/cells/src/DecisionConfig.tsx` | New | 10 | S |
| Fine-tune dataset | `packages/@ck/cells/src/FineTuneDatasetCell.tsx` | New | 10 | M |
| Fine-tune train | `packages/@ck/cells/src/FineTuneTrainCell.tsx` | New | 10 | M |
| Fine-tune eval | `packages/@ck/cells/src/FineTuneEvalCell.tsx` | New | 10 | M |
| Voice recognizer | `apps/notebook/src/features/voice/voice-recognizer.ts` | New | 10 | M |
| Voice mic button | `apps/notebook/src/features/voice/VoiceMicButton.tsx` | New | 10 | S |
| Voice to code | `apps/notebook/src/features/voice/voice-to-code.ts` | New | 10 | M |
| Transaction log | `apps/notebook/src/features/undo/transaction-log.ts` | New | 10 | L |
| Checkpoint | `apps/notebook/src/features/undo/checkpoint.ts` | New | 10 | L |
| CK notebook spec | `apps/notebook/src/features/format/cknotebook-spec.ts` | New | 11 | S |
| CK notebook serialize | `apps/notebook/src/features/format/cknotebook-serialize.ts` | New | 11 | M |
| CK notebook deserialize | `apps/notebook/src/features/format/cknotebook-deserialize.ts` | New | 11 | M |
| PDF export | `apps/notebook/src/features/export/pdf-export.ts` | New | 11 | M |
| PPTX export | `apps/notebook/src/features/export/pptx-export.ts` | New | 11 | L |
| Docker export | `apps/notebook/src/features/export/docker-export.ts` | New | 11 | M |
| API export | `apps/notebook/src/features/export/api-export.ts` | New | 11 | M |
| Dashboard view | `apps/notebook/src/features/dashboard/DashboardView.tsx` | New | 11 | L |
| Dashboard config | `apps/notebook/src/features/dashboard/DashboardConfig.tsx` | New | 11 | S |
| Production runner | `backend/app/services/production_runner.py` | New | 11 | L |
| Production router | `backend/app/routers/production.py` | New | 11 | S |
| Cell permissions | `apps/notebook/src/features/rbac/cell-permissions.ts` | New | 12 | L |
| Permission badge | `apps/notebook/src/features/rbac/PermissionBadge.tsx` | New | 12 | S |
| Permission editor | `apps/notebook/src/features/rbac/PermissionEditor.tsx` | New | 12 | M |
| RBAC service | `backend/app/services/rbac_service.py` | New | 12 | M |
| Cell permission model | `backend/app/models/cell_permission.py` | New | 12 | S |
| Pyodide client | `packages/@ck/kernel/src/pyodide-client.ts` | New | 12 | XL |
| Pyodide worker | `packages/@ck/kernel/src/pyodide-worker.ts` | New | 12 | L |
| Multi-kernel | `packages/@ck/kernel/src/multi-kernel.ts` | New | 12 | L |
| Kernel panel | `apps/notebook/src/features/sidebar/KernelPanel.tsx` | New | 12 | M |
| Virtual cell list | `apps/notebook/src/components/VirtualCellList.tsx` | New | 12 | M |
| Lazy cell registry | `packages/@ck/cells/src/lazy-registry.ts` | New | 12 | S |
| Presentation view | `apps/notebook/src/features/presentation/PresentationView.tsx` | New | 12 | M |
| Outline panel | `apps/notebook/src/features/sidebar/OutlinePanel.tsx` | New | 12 | S |
| Metadata panel | `apps/notebook/src/features/sidebar/MetadataPanel.tsx` | New | 12 | M |

**Totals:** 145 file entries (57 new, 18 moved, 70+ additional new across phases). **~13,245 estimated new lines of code.**

---

## Appendix B: Cell Type Registry Plan

### Tier A -- Phase 1, ship immediately

| Cell Type | Category | Phase | Exists Today | Best Prior Art | Novel? | Complexity |
|-----------|----------|-------|-------------|----------------|--------|------------|
| code | Compute | Phase 1 | Yes | Jupyter | No | S |
| markdown | Display | Phase 1 | Yes | Jupyter | No | S |
| sql | Compute | Phase 1 | Partial | Hex | No | L |
| prompt | AI | Phase 1 | Type only | Hex AI | No | M |
| table | Data | Phase 1 | Yes (DataFrameRenderer) | Deepnote | No | S |
| chart | Display | Phase 1 | Type only | Observable Plot | No | L |
| kpi | Display | Phase 1 | No | Hex BigNumber | No | S |
| form-slider | Input | Phase 1 | No | Marimo mo.ui.slider | No | M |
| form-dropdown | Input | Phase 1 | No | Marimo mo.ui.dropdown | No | M |
| form-text | Input | Phase 1 | No | Marimo mo.ui.text | No | S |
| raw | Compute | Phase 1 | Yes | Jupyter | No | S |
| html | Display | Phase 1 | Type only | Observable | No | S |
| latex | Display | Phase 1 | Type only | Jupyter | No | S |
| mermaid | Display | Phase 1 | Type only | Livebook | No | M |

### Tier B -- Phase 1-3, build soon

| Cell Type | Category | Phase | Exists Today | Best Prior Art | Novel? | Complexity |
|-----------|----------|-------|-------------|----------------|--------|------------|
| writeback | Data | Phase 1 | No | Hex Writeback | No | M |
| filter | Data | Phase 1 | No | Hex Filter | No | M |
| pivot | Data | Phase 1 | No | Hex Pivot | No | M |
| scratchpad | Compute | Phase 1 | No | Marimo | Partial | S |
| profile | Data | Phase 2 | No | ydata-profiling | No | L |
| map | Display | Phase 2 | No | Kepler.gl | No | L |
| image | Display | Phase 2 | No | Jupyter | No | S |
| video | Display | Phase 2 | No | Observable | No | S |
| audio | Display | Phase 2 | No | Observable | No | S |
| js | Compute | Phase 1 | Yes | Observable | No | S |
| r | Compute | Phase 3 | No | RStudio | No | L |
| julia | Compute | Phase 3 | No | Pluto.jl | No | L |

### Tier C -- Phase 7-9, competitive differentiation

| Cell Type | Category | Phase | Exists Today | Best Prior Art | Novel? | Complexity |
|-----------|----------|-------|-------------|----------------|--------|------------|
| branch | Pipeline | Phase 7 | No | None | Yes | XL |
| comparison | Pipeline | Phase 7 | No | None | Yes | L |
| contract | Pipeline | Phase 3 | No | dlt (partial) | Partial | L |
| router | Pipeline | Phase 8 | No | KNIME (partial) | Partial | M |
| merge | Pipeline | Phase 7 | No | None | Yes | M |
| tournament | Pipeline | Phase 10 | No | PyCaret (partial) | Partial | L |
| agent | AI | Phase 8 | No | None | Yes (confirmed) | XL |
| live | Pipeline | Phase 9 | No | Deephaven (partial) | Partial | XL |

### Tier D -- Phase 10-12, advanced

| Cell Type | Category | Phase | Exists Today | Best Prior Art | Novel? | Complexity |
|-----------|----------|-------|-------------|----------------|--------|------------|
| finetune | AI | Phase 10 | No | None | Yes | L |
| deploy | Meta | Phase 11 | No | None | Yes | L |
| voice | Meta | Phase 10 | No | Colab (partial) | Partial | M |
| approval | Pipeline | Phase 10 | No | Livebook Kino.interrupt! | Partial | M |
| webhook | Meta | Phase 11 | No | None | Yes | M |
| schema-browser | Data | Phase 2 | No | Datalore | No | M |
| cache | Pipeline | Phase 9 | No | Marimo mo.cache | No | M |

**Totals:** 51 cell types planned across 4 tiers and 11 categories. 5 exist today fully, 5 type-defined, 41 entirely new. 5 confirmed novel, 6 partial prior art, 40 standard.

---

## Appendix C: Dependency Graph

```
Phase 0: Extraction and Foundation
    |
    +---> Phase 1: Complete Standard Cell Types
    |         |
    |         +---> Phase 4: Variable Explorer
    |         |
    |         +---> Phase 12.5: Presentation Mode
    |
    +---> Phase 2: Reactive Execution Engine
              |
              +---> Phase 3: Cell Contract System
              |         |
              |         +---> Phase 7: Branch/Compare/Replace
              |         |         |
              |         |         +---> Phase 10.1: Tournament Cells
              |         |
              |         +---> Phase 8: Agent Cells
              |
              +---> Phase 5: Input/Widget Cells
              |
              +---> Phase 6: Pipeline Visualization / DAG View
              |         |
              |         +---> Phase 9: Living Pipeline
              |                   |
              |                   +---> Phase 10.2: Decision/Router Cells
              |
              +---> Phase 12.2: Pyodide Fallback
```

**Critical path:** Phase 0 -> Phase 2 -> Phase 3 -> Phase 7 (Branch/Compare/Replace)

This is the longest dependency chain and the path to the flagship differentiating feature. The total critical path spans 4 phases.

**Parallel work streams after Phase 0:**
- Stream A: Phase 1 (cell types) -- can proceed in parallel with Phase 2
- Stream B: Phase 2 (reactive engine) -> Phase 3 (contracts) -> Phase 7 (branch/compare)
- Stream C: Phase 4 (variable explorer) -- can proceed after Phase 1 starts

**Parallel work streams after Phase 2:**
- Phase 3 + Phase 5 + Phase 6 can all proceed in parallel (they depend on Phase 2 but not on each other)

**Independent of all other phases:**
- Phase 10.3 (Fine-tune cells) -- only needs @ck/cells and @ck/ai
- Phase 10.4 (Voice-to-code) -- only needs Web Speech API
- Phase 10.5 (Transactional undo) -- only needs notebook store
- Phase 11 (Export/Deployment) -- only needs existing notebook features
- Phase 12.6 (TOC panel) -- only needs markdown headings from cell store
- Phase 12.7 (Metadata panel) -- only needs notebook store

---

## Appendix D: Research Traceability

Every implementation task traces back to a specific finding in the synthesis document.

| Synthesis Section | Finding | Implementation Task | Phase | Target Files |
|-------------------|---------|-------------------|-------|-------------|
| S1: Executive Summary | Only 4% of notebooks reproduce (Pimentel 2019) | Reactive execution + contracts eliminate root causes | 2, 3 | `engine/reactive/`, `contracts/` |
| S1: Executive Summary | 2 confirmed novel features (Agent Cells, Cell-Level RBAC) | Agent cell as DAG node, RBAC per cell | 8, 12 | `AgentCell.tsx`, `rbac/` |
| S2: Competitive Landscape | Marimo: static AST, unique global names, Pyodide-compatible | AST dependency extractor for reactive engine | 2 | `ast-extract.ts`, `ast_service.py` |
| S2: Competitive Landscape | Hex: DAG-integrated SQL, AI sidebar, reactive | DAG view, AI cell generation | 6, 1.12 | `DagView.tsx`, `BetweenCellMenu.tsx` |
| S2: Competitive Landscape | Positron: OpenRPC, sparkline histograms, Convert to Code | Variable explorer with inline profiling | 4 | `VariableExplorer.tsx`, `DataFrameViewer.tsx` |
| S2: Competitive Landscape | Livebook: branching sections, Smart Cells | Branch cells with statistical comparison | 7 | `branch/` |
| S3: Reactive Execution | Marimo ScopedVisitor + DirectedGraph, dirty-flag propagation | Dep graph construction, staleness detection | 2 | `dep-graph.ts`, `staleness.ts` |
| S3: Reactive Execution | Rex failures: all reactive systems fail on mutations | Typed contracts as escape hatch for AST failures | 3 | `contract-resolver.ts` |
| S3: Reactive Execution | IPyflow: 17.6% safety error rate with runtime tracing | Static AST preferred over runtime tracing | 2 | `ast-extract.ts` |
| S3: Reactive Execution | Observable: Acorn parser, _inputs/_outputs, 60fps generators | Client-side reactive model for widget cells | 5 | `widget-binding.ts` |
| S4: Pipeline Frameworks | Hamilton: function-signature-as-DAG, Pyodide-compatible | Cell-level dependency declaration pattern | 2 | `dep-graph.ts` |
| S4: Pipeline Frameworks | Kedro: typed Data Catalog with versioned datasets | Contract system with versioned schemas | 3 | `contracts/types.ts` |
| S4: Pipeline Frameworks | Mage.ai: conditional blocks | Decision/router cells | 10 | `DecisionCell.tsx` |
| S4: Pipeline Frameworks | Dagster: dual-mode execution (dev stubs vs production) | Execution mode infrastructure | 9 | `execution-modes.ts` |
| S5: Cell Type Inventory | 78 cell types across 8 tiers | 33 cell types planned across all phases | 1-10 | `packages/@ck/cells/src/` |
| S5: Cell Types, Tier 2 | Metric/KPI cells absent from data science notebooks | MetricCell with trend/sparkline | 1 | `MetricCell.tsx` |
| S5: Cell Types, Tier 2 | No dedicated map cell types in any notebook | MapCell with Leaflet.js | 1 | `MapCell.tsx` |
| S5: Cell Types, Tier 3 | Marimo reactive widgets recommended | Widget cells with reactive binding | 5 | `widgets/` |
| S5: Cell Types, Tier 4 | No dedicated profile cell type | ProfileCell with auto-profiling | 1 | `ProfileCell.tsx` |
| S5: Cell Types, Tier 5 | Agent pipeline cells are NOVEL | Agent cell as reactive DAG node | 8 | `AgentCell.tsx`, `agent-runner.ts` |
| S5: Cell Types, Tier 6 | Decision/router cells novel in notebook context | DecisionCell with conditional routing | 10 | `DecisionCell.tsx` |
| S6: Variable Explorer | Positron OpenRPC protocol (best architecture) | OpenRPC-style variable introspection | 4 | `variable-client.ts` |
| S6: Variable Explorer | Spyder inline editing (best depth) | Editable scalars in explorer | 4 | `VariableExplorer.tsx` |
| S6: Variable Explorer | Deepnote column-level distribution histograms | Sparkline histograms in column headers | 4 | `InlineProfile.tsx` |
| S6: Variable Explorer | Gap 1: No explorer shows variable lineage | Novel lineage tracking per variable | 4 | `lineage.ts` |
| S6: Variable Explorer | Gap 2: No drift detection across runs | Drift detection with KS test | 9 | `drift-detector.ts` |
| S7: Experiment Tracking | No tracker has built-in statistical significance testing | Statistical tests for branch comparison | 7 | `packages/@ck/stats/src/` |
| S7: Experiment Tracking | Paired t-test for regression (Dietterich 1998) | paired-ttest.ts | 7 | `paired-ttest.ts` |
| S7: Experiment Tracking | McNemar's for classification (Demsar 2006) | mcnemar.ts | 7 | `mcnemar.ts` |
| S7: Experiment Tracking | Wilcoxon signed-rank (Benavoli 2017) | wilcoxon.ts | 7 | `wilcoxon.ts` |
| S7: Experiment Tracking | Diebold-Mariano for time series (1995) | diebold-mariano.ts | 7 | `diebold-mariano.ts` |
| S7: Experiment Tracking | Sequential testing / SPRT (Wald 1945) | sequential.ts for valid-at-any-sample-size | 7 | `sequential.ts` |
| S7: Experiment Tracking | DeepEval for LLM evaluation | Bootstrap CIs on DeepEval scores | 7 | `llm-eval.ts`, `bootstrap.ts` |
| S8: Novel Feature 1 | Living Pipeline -- PARTIAL prior art | 7 execution modes, streaming, continuous | 9 | `pipeline/` |
| S8: Novel Feature 2 | Branch/Compare/Replace -- PARTIAL prior art | Full branch/compare/replace workflow | 7 | `branch/` |
| S8: Novel Feature 3 | Tournament Cells -- PARTIAL prior art | N-way tournament with statistical testing | 10 | `TournamentCell.tsx` |
| S8: Novel Feature 4 | Cell Metrics + Drift -- PARTIAL prior art | Execution metrics + drift detection | 9 | `metrics/` |
| S8: Novel Feature 5 | Agent Cells -- CONFIRMED NOVEL | Agent as reactive DAG node | 8 | `AgentCell.tsx`, `agent-node.ts` |
| S8: Novel Feature 6 | Decision/Router -- PARTIAL prior art | Conditional routing cell | 10 | `DecisionCell.tsx` |
| S8: Novel Feature 7 | Bidirectional Notebook-Canvas Sync -- PARTIAL | Bridge package + sync protocol | 0, future | `packages/@ck/bridge/` |
| S8: Novel Feature 8 | Cell Contracts + Auto-Inference -- PARTIAL | Contract system with auto-inference | 3 | `contracts/` |
| S8: Novel Feature 9 | Transactional Undo -- prior art (Kishu) | Transaction log + checkpoint | 10 | `undo/` |
| S8: Novel Feature 11 | Cell-Level RBAC -- CONFIRMED NOVEL | Per-cell read/write/execute permissions | 12 | `rbac/` |
| S9: Academic | Chattopadhyay 2020: hidden state pain point #1 | Reactive execution eliminates hidden state | 2 | `engine/reactive/` |
| S9: Academic | Chattopadhyay 2020: version control pain point #4 | .py native format, cell-level history | 11 | `cknotebook-spec.ts` |
| S9: Academic | Pimentel 2019: 4% reproduction rate | Contracts + reactive = >90% target | 2, 3 | `engine/reactive/`, `contracts/` |
| S9: Academic | Tanimoto 1990: Level 4 liveness | Living pipeline with continuous execution | 9 | `pipeline/continuous.ts` |
| S9: Academic | NBLyzer (Subotic 2022): 98.7% analysis under 1 second | AST analysis feasible at interactive speed | 2 | `ast_service.py` |
| S10: Node Registry | ComfyUI: typed I/O, 20K+ custom nodes | Lazy-loaded cell type registry | 12 | `lazy-registry.ts` |
| S10: Node Registry | SQLite FTS5 for 100K+ entry search | Future cell type marketplace search | 12 | Future |
| S11: AI Infrastructure | Groq Llama 3.3 70B as default model | Default model for AI cells and agent cells | 1, 8 | `PromptCell.tsx`, `AgentCell.tsx` |
| S11: AI Infrastructure | MCP as Linux Foundation standard | Future MCP server for notebook tool access | Future | Future |
| S12: Migration | Strangler fig pattern (Fowler 2004) | Phase 0 extraction follows this pattern | 0 | All extraction tasks |
| S13: Strategic Gaps | Zero-platform cell types (8 types) | Approval/gate, decision/router, agent, tournament, branch, merge, benchmark, drift | 7-10 | Various |

---

## Summary Metrics

| Metric | Value |
|--------|-------|
| Total phases | 12 (0 through 11) + 1 polish phase (12) |
| Total new files | ~130 |
| Total moved files | ~18 |
| Total estimated new lines | ~13,245 |
| Total moved lines | ~2,800 |
| Cell types at completion | 51 (up from 5 fully functional today) |
| Novel features | 14 (2 confirmed novel, 8 partial prior art, 4 infrastructure) |
| Confirmed novel features | Agent Cells as DAG nodes (Phase 8), Cell-Level RBAC (Phase 12) |
| Critical path length | 4 phases (0 -> 2 -> 3 -> 7) |
| Packages created | 3 (@ck/cells, @ck/kernel, @ck/bridge) + 1 (@ck/stats) |
| Backend services added | 6 (ast, contract, variable, scheduler, rbac, production) |
| Research sources traced | 45+ platforms, 60+ papers, 13 pipeline frameworks, 9 experiment trackers |
