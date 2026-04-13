# ContextKeeper Notebook -- Architectural Vision
# Authored: April 2026
# Steven Wazlavek + Claude (Anthropic)

## Core Concept: The Living Pipeline Notebook

The ContextKeeper Notebook is NOT a document. It is a living computational 
pipeline where cells are typed, replaceable processing steps with defined 
input/output contracts. Data flows continuously top-to-bottom. The pipeline 
never stops unless you stop it.

## Execution Modes (all available, user chooses)

1. MANUAL -- traditional notebook, run cells on demand
2. REACTIVE -- cell re-executes when any upstream dependency changes (Marimo-style)
3. SCHEDULED -- pipeline runs on cron schedule (every 1min to monthly)
4. EVENT-DRIVEN -- pipeline triggers on data arrival, webhook, file change, API call
5. STREAMING -- each row flows through pipeline as it arrives (Kafka/Flink style)
6. CONTINUOUS -- pipeline runs in infinite loop, never stops
7. AUTONOMOUS -- fully automatic: monitors quality, branches, compares, replaces

All modes can be mixed. Individual cells can have different execution modes.

## The Branch/Compare/Replace System

Any cell can be branched:
- BRANCH: creates Cell 4B alongside Cell 4A
- Both receive identical input
- Both execute in parallel
- COMPARISON LAYER: statistical test determines winner
- REPLACE: winner replaces loser (with approval gate -- auto or manual, user chooses)

Statistical tests by output type:
- Regression output: RMSE/MAE/R² comparison + paired t-test
- Classification output: F1/AUC comparison + McNemar's test
- LLM output: DeepEval metrics (faithfulness, relevancy, coherence)
- Any numeric: Wilcoxon signed-rank test
- Time series: Diebold-Mariano test
- Significance threshold: configurable (default p < 0.05)
- Sequential testing: valid at any sample size (no peeking problem)

Replace options:
1. AUTO-REPLACE when winner is statistically significant
2. NOTIFY + one-click replace
3. SUGGEST only, human decides
4. NEVER replace, comparison is informational only

## Cell Types (all of the following, plus agent nodes)

Standard: Code, Markdown, SQL, JavaScript, R, Julia, Bash, Raw, HTML
Display: Chart, Map, Metric/KPI, Image, Video, Audio, LaTeX/Math, Mermaid
Input: Slider, Dropdown, DatePicker, TextInput, Button, FileUpload, ColorPicker
Data: Table/DataFrame, Profile, Schema, Validation
AI: LLM Call, Agent Pipeline, AI Narrative, AI Fix, AI Optimize
Pipeline: Contract, Branch, Comparison, Decision/Router, Merge, Live/Continuous
Meta: Version History, Diff, Test, Benchmark, Export, Import
Special: Voice-to-Code, Text-to-Speech, Tournament (N methods, pick winner)
Fine-Tune: Dataset Builder, Training Job, Model Eval, Model Deploy

All 178+ Agent Canvas node types are available as cells.
Architecture supports tens of thousands of node types via lazy-loaded plugin registry.

## Cell Contract System

Every cell optionally defines:
- INPUT CONTRACT: expected column names, types, value ranges, nullable flags
- OUTPUT CONTRACT: guaranteed output shape
- When violated: cell turns red, execution stops, specific error shown
- Branch cells inherit parent contract automatically
- Contract validation uses Pandera + Pydantic under the hood

## Pipeline Architecture

```
INPUT SOURCE (connector -- live, batch, or streaming)
    |
[Cell 1: Data Cleaning]     <- contract enforced
    |
[Cell 2: Feature Eng]       <- contract enforced  
    |
[Cell 3: Normalization]     <- contract enforced
    |
[Cell 4A: Lasso Regression] <- ACTIVE METHOD
[Cell 4B: ElasticNet]       <- BRANCH (parallel)
    |                    |
    +----[COMPARISON]----+   <- statistical test
    |
[Cell 5: Evaluation]        <- receives winner
    |
[Cell 6: Visualization]
    |
OUTPUT SINK
```

## Node Registry Architecture (supports 10k+ nodes)

- Lazy-loaded: nodes loaded on demand, not all at startup
- SQLite full-text search index for fast search across 100k+ nodes
- Plugin system: third parties can register node types
- Categories with subcategories, max 2 levels deep
- Each node: type, title, category, icon, description, input schema, output schema, 
  execution type, default config, system prompt template, user prompt template
- Versioned: nodes have versions, pipelines pin to specific versions

## Execution Engine

- Jupyter Kernel Gateway for Python/R/Julia execution
- WebAssembly fallback (Pyodide) for offline/browser execution
- Distributed execution: Dask/Ray/Spark for large data cells
- Multi-kernel: Python + R + SQL in same notebook
- Kernel pooling: pre-warmed kernels for instant execution
- Checkpointing: pipeline state saved every N steps
- Resumption: pipeline can resume from last checkpoint after failure

## Sync Between Notebook and Agent Canvas

Bidirectional:
- Pin any notebook cell as an Agent Canvas node
- Drag any Agent Canvas node into notebook as a cell
- Changes sync in both directions
- The notebook IS the development environment for building pipeline nodes

## Everything Has Both Options

- Manual AND automatic
- Local AND cloud
- Sequential AND parallel
- Synchronous AND streaming
- Human-in-loop AND fully autonomous
- Independent AND synced

No assumptions about how someone uses it.
Every option is available. Switches control behavior.

