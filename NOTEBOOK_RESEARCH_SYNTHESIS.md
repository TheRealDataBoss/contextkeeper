# ContextKeeper Notebook: Comprehensive Research Synthesis

Compiled: April 2026
Sources: 11 research documents, 45+ platforms, 60+ academic papers, 78 cell types, 13 pipeline frameworks, 9 experiment trackers

---

## 1. Executive Summary

The computational notebook ecosystem is large, fragmented, and converging on a small set of ideas that no single platform has fully unified. Across 45+ platforms reviewed -- from Jupyter's decade-long dominance to reactive newcomers like Marimo, Hex, and Observable -- the central finding is that only 4% of notebooks reproduce (Pimentel et al. 2019, analysis of 1.45M GitHub notebooks). The root causes are well-documented: hidden state from out-of-order execution, implicit dependencies between cells, absence of typed contracts on cell outputs, and version control systems designed for text files rather than computational artifacts. Reactive execution addresses the hidden state problem but introduces new constraints (Marimo requires unique global names; Pluto.jl restricts one expression per cell), and the Rex test suite (Zheng et al. 2025) demonstrates that all three major reactive systems fail on simple list mutations. No platform combines reactive execution with typed cell contracts, branch/compare/replace workflows, and a scalable node registry into one coherent system.

ContextKeeper's design space is defined by 2 confirmed novel features -- Agent Cells as composable DAG nodes and Cell-Level RBAC -- plus 8 features with partial prior art that leave significant implementation gaps. Agent Cells treat autonomous LLM agents as first-class nodes in a notebook's dependency graph, with typed inputs, outputs, and tool declarations; no existing platform (including LangGraph, AutoGen, or CrewAI) embeds agents as reactive DAG nodes inside a notebook execution model. Cell-Level RBAC applies role-based access control at the individual cell level, a granularity that exists in Google Sheets (range protection) but has never been implemented in a computational notebook. The 8 partial-prior-art features -- living pipelines, branch/compare/replace with statistical testing, tournament cells, cell metrics with drift detection, decision/router cells, bidirectional notebook-canvas sync, cell contracts with auto-inference, and audit log with provenance -- each have scattered implementations across different tools but none are unified in a single notebook environment.

The current migration from a 15,403-line monolith (data-lab.html) to a modern React/TypeScript/FastAPI stack is 55% complete: 4,146 lines across 24 files, with 26 features complete, 6 partial, 14 missing-but-standard, and 14 novel features not yet started. The strangler fig migration pattern preserves the 228+ NB.* functions, 8 export formats, and .ipynb compatibility while incrementally replacing the rendering pipeline (DOM to React), state management (globals to Zustand), and editor (custom to Monaco/CodeMirror 6). The recommended execution model is Marimo-style static AST analysis (Pyodide-compatible) augmented with typed contracts for cases where static analysis fails, backed by Hamilton-style function-signature-as-DAG for pipeline integration and Positron-style OpenRPC for variable exploration.

---

## 2. The Competitive Landscape (45+ Platforms)

### Tier 1: Direct Competitors

**Marimo** (reactive, 15K+ GitHub stars, pure Python files). Marimo's core innovation is that notebooks are stored as pure .py files with a custom `app = marimo.App()` wrapper, making them executable with `python notebook.py` and diff-friendly in Git. The reactive engine uses Python's `ast` module with a `ScopedVisitor` class to build a `DirectedGraph` of cell dependencies. Enforces a unique-global-names constraint: no two cells may define the same variable at module scope. Runs in Pyodide for zero-server deployment. Strengths: reproducibility by construction (no hidden state), Git-native files, browser-only mode, excellent developer experience. Weaknesses: the unique-global-names constraint is restrictive for exploratory workflows, no enterprise features (RBAC, audit), limited cell types (code and markdown only), no pipeline integration, no branching/comparison. ContextKeeper differentiation: typed contracts relax the unique-names constraint, branch/compare/replace adds experiment management, 78 cell types vs. Marimo's 2, agent cells enable AI-native workflows.

**Hex** ($150M+ funding, Series C 2023). Reactive DAG execution with SQL-first design. AI sidebar ("Magic") generates SQL and Python from natural language. Variable pills show DAG-aware dependency information. Dual-mode: notebook for exploration, app builder for dashboards. Strengths: best-in-class SQL integration (12+ warehouse connectors), strong collaboration features, reactive execution with visual DAG, AI assistance. Weaknesses: proprietary SaaS only (no self-hosted), expensive ($50+/user/month for teams), limited to Python and SQL (no R/Julia), no pipeline export, no cell-level access control. ContextKeeper differentiation: self-hosted option, 78 cell types, pipeline integration, branch/compare/replace, cell-level RBAC, agent cells.

**Deepnote** (reactive since 2024, collaborative). Jupyter-compatible with real-time collaboration. Added reactive execution in 2024, joining Marimo and Hex. Column-level distribution histograms and null counts in variable explorer. Strengths: Jupyter compatibility (runs existing .ipynb files), good collaboration, SQL integration, variable profiling. Weaknesses: limited reactive model (opt-in, not enforced), no pipeline framework, no branching, proprietary. ContextKeeper differentiation: enforced reactivity, typed contracts, branch/compare, pipeline integration, agent cells.

**Observable** (client-side reactive JavaScript, created by Mike Bostock of D3). Built on a custom reactive runtime where cells are JavaScript generators. Uses the Acorn JS parser to extract doubly-linked `_inputs` and `_outputs` arrays per cell. A `_version` counter tracks staleness. Generator cells can run at 60fps for animations. Observable Plot replaces D3 for most charting. Strengths: best-in-class data visualization, reactive by design, free for public notebooks, Observable Framework for static sites. Weaknesses: JavaScript only (no Python/R), steep learning curve, Observable-specific syntax, limited data science tooling, no ML pipeline integration. ContextKeeper differentiation: Python-first with multi-language support, ML pipeline integration, typed contracts, agent cells, enterprise features.

**Livebook** (Elixir, branching sections, Smart Cells). Built on the Erlang/OTP runtime. Unique branching sections allow parallel execution paths from a shared state. Smart Cells provide no-code interfaces for database connections, charting, and ML. Uses Elixir AST for dependency analysis with snapshot-based staleness detection. Strengths: branching execution model (closest prior art to ContextKeeper's branch/compare), excellent concurrency via OTP, Smart Cells pattern. Weaknesses: Elixir-only (niche language), small ecosystem, no Python/R, limited ML tooling. ContextKeeper differentiation: Python-first, statistical comparison in branches, 78 cell types, agent cells, enterprise features. Livebook's branching is the strongest prior art for ContextKeeper's branch/compare feature but lacks statistical comparison and replace workflows.

**Positron** (Posit, OpenRPC protocol, Rust kernel). Posit's next-generation IDE, successor to RStudio. Built on VS Code with a custom Rust-based kernel communication layer using OpenRPC (JSON-RPC 2.0). Data Explorer supports sparkline histograms, millions of rows, and "Convert to Code" (generates dplyr, pandas, or SQL from UI operations). Strengths: best-in-class variable explorer and data viewer, OpenRPC protocol is clean and extensible, R and Python support, Posit's institutional backing. Weaknesses: IDE-focused (not notebook-first), no reactive execution, no pipeline integration, no AI features, early stage. ContextKeeper differentiation: notebook-first with reactive execution, pipeline integration, agent cells, branch/compare. Positron's OpenRPC pattern is recommended for ContextKeeper's variable explorer.

### Tier 2: Enterprise Platforms

**Jupyter/JupyterLab** (the standard, but linear). The dominant notebook platform with an estimated 10M+ users. IPython kernel protocol is the de facto standard. JupyterLab 4.x adds real-time collaboration via Yjs. Strengths: universal compatibility, massive ecosystem (thousands of extensions), .ipynb is the interchange format, free and open source. Weaknesses: linear execution (hidden state problem), no reactivity, poor version control (JSON diffs), limited collaboration, extension quality varies wildly. ContextKeeper differentiation: reactive execution, typed contracts, branch/compare, 78 cell types, agent cells, .ipynb compatibility maintained.

**Databricks** (Spark-native, Unity Catalog). The dominant enterprise data platform. Notebooks are secondary to the lakehouse architecture. Unity Catalog provides data governance. SQL, Python, R, Scala cells. Strengths: Spark integration, Unity Catalog governance, massive enterprise adoption, MLflow built-in. Weaknesses: expensive, lock-in to Databricks runtime, notebooks are basic (no reactivity, limited cell types), poor local development story. ContextKeeper differentiation: local-first, reactive, 78 cell types, agent cells, no vendor lock-in.

**SageMaker** (AWS-integrated). SageMaker Studio provides Jupyter-based notebooks with AWS service integration. SageMaker Pipelines for ML workflows. Strengths: deep AWS integration, managed infrastructure, built-in ML lifecycle tools. Weaknesses: AWS lock-in, notebooks are standard Jupyter (no reactivity), expensive, complex setup. ContextKeeper differentiation: cloud-agnostic, reactive, simpler setup, agent cells.

**Google Colab** (free GPU). The most accessible notebook platform. Free T4 GPU tier drives adoption. Strengths: free compute including GPU, Google Drive integration, zero setup, massive user base. Weaknesses: ephemeral runtimes, limited collaboration, no reactivity, no pipeline integration, Google lock-in. ContextKeeper differentiation: persistent state, reactive execution, pipeline integration, self-hosted option.

**Datalore** (JetBrains). JetBrains' notebook platform with smart coding assistance. Reactive execution mode added 2023. Strengths: JetBrains IDE quality, good code completion, reactive mode, SQL integration. Weaknesses: small user base, JetBrains subscription required for full features, limited ecosystem. ContextKeeper differentiation: 78 cell types, agent cells, branch/compare, open architecture.

### Tier 3: Specialized Platforms

**Count** (canvas-based SQL). A canvas-style SQL notebook where queries are nodes on a spatial canvas. Strengths: best-in-class SQL canvas experience, visual query composition. Weaknesses: SQL-only, no Python/R, limited analysis capabilities, small user base. ContextKeeper differentiation: multi-language, 78 cell types, reactive execution, agent cells. Count's canvas model is prior art for ContextKeeper's bidirectional notebook-canvas sync.

**Sigma Computing** ($1.5B valuation, warehouse-native). Spreadsheet-like interface directly on cloud data warehouses. Strengths: familiar spreadsheet paradigm, warehouse-native (no data movement), strong enterprise adoption. Weaknesses: not a notebook, limited to SQL/spreadsheet operations, expensive. ContextKeeper differentiation: full notebook with code execution, 78 cell types, ML pipeline integration.

**Mode** (SQL-first BI). SQL-first analytics with Python/R notebooks for deeper analysis. Strengths: SQL editor with schema browser, good BI reporting, Python/R integration. Weaknesses: SQL-centric (Python/R secondary), limited notebook features, BI-focused. ContextKeeper differentiation: notebook-first, reactive execution, 78 cell types, agent cells.

**Evidence** (code-first BI). Markdown files with SQL code blocks that generate BI reports. Strengths: code-first approach, Git-native, fast build times, good for data teams. Weaknesses: SQL and markdown only, no Python, no interactivity, reporting-focused. ContextKeeper differentiation: full notebook with interactive execution, 78 cell types, pipeline integration.

**Quarto** (publishing). Pandoc-based publishing system for notebooks. Supports Jupyter, Observable, and knitr. Strengths: best-in-class publishing (PDF, HTML, Word, slides), multi-engine support, academic-quality output. Weaknesses: publishing-focused (not an execution environment), no reactivity, no collaboration. ContextKeeper differentiation: interactive execution environment, reactive, agent cells.

**nbdev** (library development). fast.ai's system for developing Python libraries inside notebooks. Strengths: novel approach to literate programming, automated testing from notebooks, pip-installable output. Weaknesses: specific to library development, fast.ai ecosystem, limited adoption outside ML. ContextKeeper differentiation: general-purpose notebook, 78 cell types, pipeline integration.

### Tier 4: Dead or Declining

**Iodide** (Mozilla, dead 2021). Browser-based scientific computing with JSMD format (JavaScript, Markdown, CSS, Python via Pyodide). Mozilla created Pyodide for this project; Pyodide survived but Iodide did not. Lesson: Pyodide is viable but needs a sustainable business model.

**Light Table** (dead ~2018). Chris Granger's vision of inline evaluation. Pioneered the concept of showing results next to code. Influenced VS Code's notebook rendering. Lesson: inline results are now table stakes.

**Eve** (dead 2018). Also Chris Granger. Attempted to reinvent programming with a relational model. Too radical a departure from existing workflows. Lesson: incremental improvement over existing paradigms (Jupyter) is more adoptable than revolutionary redesign.

**Hyperquery** (dead 2024). SQL notebook startup. Raised funding but failed to differentiate from Hex/Mode. Lesson: SQL-only notebooks are not a defensible category.

**Carbide** (dead ~2020). Alpha-stage reactive notebook. Never reached production quality. Lesson: reactive execution alone is not sufficient differentiation.

**Starboard** (dormant). Browser-based notebooks with a plugin architecture. Good technical foundation but no active development. Lesson: solo maintainer risk.

---

## 3. Reactive Execution Models

### Comparative Matrix

Six reactive systems were analyzed in depth. Each uses a different strategy for dependency extraction, staleness detection, and execution scheduling.

**Marimo (Python)**. Dependency extraction: Python `ast` module with `ScopedVisitor` that walks the AST to find references and definitions at each scope level. Builds a `DirectedGraph` where nodes are cells and edges are variable dependencies. Constraint: unique global names -- no two cells may define the same variable at module scope. This constraint eliminates ambiguity in the dependency graph at the cost of flexibility. Staleness: dirty-flag propagation through the graph. Execution: topological sort of dirty subgraph, sequential execution (Python GIL limits parallelism). Pyodide-compatible: yes, the entire engine runs in the browser. Error handling: cells that depend on errored cells are marked stale but not executed. UI integration: Marimo's UI elements (sliders, dropdowns) are reactive -- changing a slider value automatically re-executes dependent cells.

**Observable (JavaScript)**. Dependency extraction: Acorn JavaScript parser extracts variable references. Each cell has `_inputs` (dependencies) and `_outputs` (definitions) arrays, forming a doubly-linked dependency structure. Staleness: `_version` counter incremented on each cell change; downstream cells compare their last-seen version. Execution: topological sort with concurrent execution of independent cells (JavaScript is single-threaded but uses microtask scheduling). Generator cells: cells that yield values can run at up to 60fps, enabling animations and real-time data. Viewof pattern: `viewof x = ...` creates both a UI element and a reactive variable. File attachments: `FileAttachment("data.csv")` provides lazy-loading data access. The Observable runtime is open source and can be embedded in any web page.

**Pluto.jl (Julia)**. Dependency extraction: `ExpressionExplorer.jl` module that handles Julia-specific patterns including multiple dispatch via `FunctionNameSignaturePair`. Constraint: one expression per cell (more restrictive than Marimo). This enables precise dependency tracking but fragments code. Staleness: full re-execution of dependent subgraph. Execution: leverages Julia's compilation model -- first run is slow (JIT compilation) but subsequent runs are fast. Unique feature: package management is built into the notebook; `using Plots` triggers automatic installation. Bond.jl: reactive UI widgets similar to Marimo's approach. Pluto's model is the most theoretically clean but the one-expression constraint is limiting for real-world data science.

**Excel (Spreadsheet)**. Dependency extraction: formula-level parsing identifies cell references (A1, B2:C10, named ranges). `calcChain.xml` stores the dependency order. Dynamic dependencies via INDIRECT() and OFFSET() break static analysis. Multi-Threaded Recalculation (MTR): up to 1024 threads for parallel formula evaluation. Staleness: any cell edit marks all dependents as dirty. Execution: follows calcChain order, with MTR parallelizing independent chains. Excel is the world's most widely used reactive system (estimated 1.5B+ users) but operates at formula granularity, not cell granularity. Lambda functions (2021) added composable functions. XLOOKUP and dynamic arrays (2019) reduced the need for CSE formulas. Excel's reactive model is mature but not designed for computational notebooks.

**Livebook (Elixir)**. Dependency extraction: Elixir AST analysis at the section level (not individual cell level). Snapshot-based staleness: each section captures a snapshot of its output bindings; downstream sections compare against the snapshot. Unique feature: branching sections allow parallel execution paths from a shared parent state. This is the closest prior art to ContextKeeper's branch/compare feature. Execution: leverages Erlang/OTP for true parallel execution across sections. Smart Cells: no-code interfaces that generate Elixir code, similar to ContextKeeper's planned cell types. Livebook's section-level granularity (rather than cell-level) is coarser than Marimo but enables the branching model.

**IPyflow (Python, research prototype)**. Dependency extraction: hybrid approach combining runtime tracing (monitoring variable reads/writes during execution) with static AST analysis. This captures dependencies that static analysis alone misses (e.g., dictionary mutations, attribute access). Safety errors: Macke et al. (2021) found that 17.6% of sessions had safety errors -- cases where the system either missed a dependency or flagged a false dependency. Strengths: handles dynamic Python patterns better than pure static analysis. Weaknesses: runtime tracing overhead, safety error rate too high for production use. Lesson for ContextKeeper: pure runtime tracing is insufficient; typed contracts provide a more reliable mechanism for the cases where static analysis fails.

### Rex Test Suite Findings (Zheng et al. 2025)

The Rex test suite systematically evaluates reactive notebook systems on edge cases. Key finding: all three tested systems (Marimo, Pluto.jl, Observable) fail on simple mutations such as `my_list.append(42)`. The reason: static AST analysis sees `my_list.append(42)` as a reference to `my_list`, not a redefinition, so it does not trigger re-execution of cells that depend on `my_list`. This is not a bug but a fundamental limitation of static analysis for mutable data structures.

The Rex paper identifies four categories of failures: (1) in-place mutations, (2) aliased variables, (3) higher-order functions with side effects, (4) dynamic attribute access. Categories 1 and 2 are common in data science (pandas DataFrames are mutable, aliasing is frequent with `df2 = df`).

**Recommended approach for ContextKeeper**: Marimo-style static AST analysis as the default (works in Pyodide, zero overhead, handles 80%+ of real-world patterns) plus typed cell contracts as an explicit escape hatch for cases where AST analysis fails. Contracts declare input types and output schemas, making dependencies explicit rather than inferred. When a contract is present, the execution engine uses the contract rather than AST analysis for dependency resolution. This hybrid approach addresses the Rex failures without the overhead and safety errors of runtime tracing.

---

## 4. Pipeline and DAG Frameworks

### 13 Frameworks Analyzed

**Dagster**. Software-defined assets paradigm where each asset (table, model, file) is a Python function decorated with `@asset`. Dagstermill wraps Papermill to execute Jupyter notebooks as pipeline steps, but the notebook becomes a black box -- Dagster cannot see inside to individual cells. Type system: `DagsterType` with runtime type checking. Dual-mode execution: dev mode uses stubs and samples; production mode uses real data and infrastructure. Strengths: best-in-class developer experience, strong typing, excellent observability UI. Weaknesses: Dagstermill's notebook integration is shallow (whole-notebook granularity), heavy framework overhead. Pattern to adopt: dual-mode execution (dev stubs vs. production context).

**Hamilton** (function-name-as-node, Pyodide-compatible). Each Python function becomes a DAG node; the function name is the output name, and parameter names are input names (dependency declarations). This function-signature-as-DAG pattern is elegant and requires zero framework-specific decorators. Hamilton is the only pipeline framework explicitly tested and compatible with Pyodide, making it the primary candidate for ContextKeeper's browser-based pipeline execution. Strengths: minimal boilerplate, Pyodide-compatible, function-level granularity matches cell-level granularity, strong typing via Python type hints. Weaknesses: small community compared to Dagster/Airflow, naming convention can be restrictive. Pattern to adopt: function-signature-as-DAG maps directly to cell-level dependency declarations.

**Kedro**. Modular pipeline framework with a Data Catalog that provides typed, versioned access to datasets. `AbstractDataSet` base class with implementations for CSV, Parquet, SQL, S3, etc. Versioned datasets store each run's data with timestamps. Pipeline structure: nodes (functions) connected by named datasets. Strengths: Data Catalog is the best abstraction for dataset management, strong modularity, Kedro-Viz for pipeline visualization. Weaknesses: verbose boilerplate, opinionated project structure, limited real-time capabilities. Pattern to adopt: typed Data Catalog with versioned datasets for ContextKeeper's data management layer.

**Prefect**. Task-based workflow orchestration. Prefect 2.x uses `@task` and `@flow` decorators with a Python-native API. Strengths: Pythonic API, good observability, hybrid execution (local + cloud). Weaknesses: orchestration-focused (not notebook-integrated), Prefect Cloud required for full features.

**Airflow**. The most widely deployed workflow orchestrator. DAGs defined in Python files. Strengths: massive ecosystem, battle-tested at scale, huge community. Weaknesses: not designed for notebooks, DAG definition is cumbersome, scheduler overhead.

**Flyte**. Kubernetes-native workflow orchestrator. Type system built on protobuf. Strengths: strong typing, containerized execution, good for ML workflows. Weaknesses: Kubernetes dependency, complex setup, not notebook-integrated.

**Metaflow** (Netflix). ML-focused workflow framework. `@step` decorator defines pipeline steps. Artifact versioning tracks all intermediate results. Strengths: excellent artifact versioning, AWS/cloud integration, resume from failure. Weaknesses: Netflix-specific patterns, limited local execution.

**Ploomber**. Pipeline framework designed for Jupyter notebooks. Notebooks are pipeline tasks. Strengths: notebook-first design, good for notebook-to-production transition. Weaknesses: small community, limited features compared to Dagster/Prefect.

**Mage.ai** (notebook-like blocks). Pipeline blocks that look and feel like notebook cells. Each block is a file with a template structure (imports, function, test). Conditional blocks allow if/else routing in pipelines. Strengths: closest to notebook-like pipeline experience, block templates reduce boilerplate, conditional routing. Weaknesses: block-level granularity (not cell-level), limited reactive capabilities. Pattern to adopt: notebook-like block interface, conditional routing blocks.

**ZenML**. MLOps framework that abstracts pipeline execution across infrastructure. Strengths: infrastructure abstraction, experiment tracking integration. Weaknesses: abstraction overhead, small community.

**Luigi** (Spotify). Task-based pipeline framework. Strengths: simple model, file-system-based dependency resolution. Weaknesses: dated design, no type system, limited features.

**dbt**. SQL-only transformation framework. `ref()` function creates DAG dependencies between models. Strengths: dominant in analytics engineering, excellent SQL workflow, strong testing. Weaknesses: SQL-only, no Python execution. Pattern to adopt: `ref()` pattern for cross-cell dataset references.

**Kubeflow Pipelines**. Kubernetes-native ML pipelines. Components defined as containers. Strengths: full ML lifecycle on Kubernetes, containerized components. Weaknesses: Kubernetes required, complex setup, heavy infrastructure.

### Key Finding

Hamilton is the only framework explicitly Pyodide-compatible, making it the primary candidate for ContextKeeper's browser-based pipeline execution. The function-signature-as-DAG pattern maps naturally to cell-level dependency declarations where the cell's input parameters declare its dependencies and its return type declares its output schema. This pattern combined with Kedro's typed Data Catalog provides a comprehensive pipeline model that works both in-browser (via Pyodide + Hamilton) and server-side (via any orchestrator).

---

## 5. Cell Type Master Inventory (200+ Implementations, 78 Types, 8 Tiers)

*Updated April 2026 from 4-source master merge: cell-types-comprehensive.md, cell-types-inventory.md, cell-types-sql-widgets-extensibility.md, cell-types-platform-specializations.md. Total distinct cell implementations documented: 200+. Full details in research/cell-types-master.md.*

### Tier 1: Compute (8 types)

**Code cells** (Python, R, Julia, Bash, JavaScript, SQL, Scala, Rust-via-WASM). Every platform supports Python code cells. Multi-language support varies: Jupyter supports any language with a kernel (100+ kernels exist), Databricks supports Python/R/SQL/Scala, Observable supports only JavaScript, Marimo supports only Python, Livebook supports only Elixir. ContextKeeper targets Python as primary with R, Julia, and JavaScript as secondary.

**SQL cells** have expanded to **25+ distinct implementations** across three categories. Notebook-native: Hex (DAG-integrated with automatic CTE chaining, green/purple pill dual-mode output, VegaFusion warehouse pushdown), Databricks (Unity Catalog, `_sqldf` implicit variable since DBR 13.3+, `:param` markers since DBR 15.2+), Deepnote (JinjaSQL with `DeepnoteQueryPreview` for chaining, reactive since 2024), Datalore (JetBrains DataGrip drivers, three-tab output with Table/Visualize/Statistics), Observable (DuckDBClient with Apache Arrow results, `sql` tagged template literal), Livebook (Smart Cell backed by `kino_db` with Postgrex/MyXQL/Exqlite/Tds/ADBC adapters, rasterizable to Elixir code), Zeppelin (interpreter prefix system with three templating mechanisms), Mode (Liquid templating, datasets list), Count (canvas DAG with dynamic CTE compilation), Sigma (warehouse-native, `sigma_element()` references), Colab Enterprise (native SQL cells with IAM auth to BigQuery), Noteable (ceased Dec 2023, JinjaSQL with backslash meta commands). BI tools: Metabase (three variable types including field filters generating WHERE clauses, MBQL->HoneySQL pipeline), Redash (Query Results Data Source enabling `SELECT * FROM query_49588` cross-chaining via in-memory SQLite), Apache Superset (full Jinja2 with async Celery dispatch, sqlglot-based Row Level Security). Modern data stack: dbt (`ref()` DAG, Jinja2, materializations, `adapter.dispatch()` for cross-database), SQLMesh (per-model `dialect:` with SQLGlot transpilation, no `ref()` needed -- auto-dependency detection), Malloy (semantic source/query model with symmetric aggregate handling), PRQL (three-stage compilation to SQL), Evidence.dev (SQL in Markdown fences, static site generation), Rill Developer (YAML+SQL with embedded DuckDB OLAP), Holistics AML (`{{ #model_name }}` references), LookML (Liquid templating with PDTs), Lightdash (dbt manifest.json conversion). Also: Querybook (Pinterest, Jinja2 with `{{ latest_partition() }}`), PopSQL (multiplayer SQL), Azure Data Studio (single-connection binding, GitHub issue #5031), DBeaver (multi-mode execution with `-- @result_name` comments), Dataiku (single-connection binding, `${variable_name}` DSS variables).

ContextKeeper's SQL cell should combine Hex's DAG integration and CTE chaining with Deepnote's output profiling, Count's visual composition, and SQLMesh's per-cell dialect transpilation via SQLGlot.

**WASM cells** execute compiled languages (Rust, C, C++) in the browser via WebAssembly. Emerging capability, not widely implemented. Starboard had early WASM support. ContextKeeper can leverage Pyodide's WASM foundation to enable WASM cell execution.

### Tier 2: Display (9 types)

**Chart/visualization cells**: Plotly (interactive, 10M+ downloads/month, used by Databricks), Vega-Lite (grammar of graphics, used by Hex with VegaFusion server-side pre-aggregation, Deepnote, Count.co), Observable Plot (D3 successor, marks-based grammar with 20+ mark types), Altair (Python Vega-Lite wrapper), Matplotlib (static, dominant in academia), Seaborn (statistical visualization). BI tools add further variety: Metabase (custom React/SVG), Redash (Plotly.js + Leaflet), Superset (ECharts plugin architecture with legacy NVD3 and Deck.gl maps), Evidence.dev (ECharts with Svelte components), Rill (embedded DuckDB for sub-second latency). Key finding: Hex's chart cells return filtered DataFrames from visual selections, creating bidirectional data flow unique among notebook platforms. Marimo's `mo.ui.altair_chart()` and `mo.ui.plotly()` make charts simultaneously outputs AND reactive inputs. ContextKeeper should support Plotly as primary with Vega-Lite as secondary.

**Map cells**: Folium (Leaflet.js wrapper, static), Kepler.gl (Uber, GPU-accelerated millions of points), Deck.gl/pydeck (WebGL-powered with bidirectional communication), Mapbox, ipyleaflet (bidirectional sync with 10+ layer types), Observable's D3-geo/Plot.geo. Livebook MapLibre Smart Cell is the only true "map cell type" with a dedicated UI generating valid code (`Ml.new(center:)` -> `Ml.add_source()` -> `Ml.add_layer()`). Hex has a dedicated Map cell with point/text/area/heatmap layers. Evidence has `<USMap>` and `<PointMap>` components.

**Metric/KPI cells**: Hex Single Value cell (aggregation, comparison mode, sparkline, outputs Python variable), Deepnote Big Number block, Count Big Number visual, Evidence `<BigValue>` component, Mode Visual Explorer KPIs, Sigma KPI cards. Dedicated metric cells are common in BI tools but absent from data science notebooks.

**Image, Video, Audio cells**: Standard display types. Jupyter's `IPython.display` module handles all three. Observable has `FileAttachment` for media. Livebook `Kino.Input.audio()` and `Kino.Input.image()` support recording via mic/camera natively, with `Kino.Image.new(binary, :pixel)` accepting `Nx.Tensor`. Gradio `gr.Audio(sources=["microphone"], streaming=True)` and `gradio-webrtc` for ultra-low-latency. No traditional notebook platform has native recording cells.

**LaTeX/Math cells**: Jupyter uses MathJax, Observable uses KaTeX, Quarto supports both. ContextKeeper has a dedicated `latex` cell type with KaTeX. CoCalc provides the most complete LaTeX integration with full compilation, live preview, and error highlighting.

**Mermaid/Diagram cells**: Livebook kino_kroki Smart Cell supports 30+ diagram syntaxes (Graphviz, PlantUML, Mermaid, D2, BPMN, C4, DBML, Excalidraw, WaveDrom, WireViz, and more) via Kroki API -- rasterizable to code. ContextKeeper has a dedicated `mermaid` cell type. Observable has first-class `mermaid` and `dot` tagged template literals. JupyterLab 4.1+ renders Mermaid natively via `text/vnd.mermaid` MIME type. d2-widget provides `%%d2` magic. jupyterlab-drawio embeds full draw.io editor. **No platform gives diagrams an interactive cell type with visual editing.**

### Tier 3: Input/Widget (40+ types, 7 reactivity paradigms)

**Seven distinct reactivity paradigms** exist, each with different tradeoffs for a cell registry:

1. **One-way variable binding with DAG propagation** (Hex): 14+ input types, each produces a named pill. Static analysis infers dependencies. Run Button gates downstream execution. URL parameterization in published apps.
2. **Two-way reactive binding** (Marimo): 25+ `mo.ui` elements with generic `UIElement<S, T>` type system. `UIElementRegistry` tracks objects by `object_id`. Lens mechanism for hierarchical widgets. anywidget integration via `MarimoComm`.
3. **Generator-based reactive binding** (Observable): `viewof` protocol creates dual variables (DOM element + value). `Generators.input()` async generator. Any DOM element with `.value` and `input` events is compatible. Entirely client-side.
4. **Bond-based binding** (Pluto.jl): `@bind` with `AbstractPlutoDingetjes.jl` providing `initial_value`, `validate_value`, `transform_value`. WebSocket `bond_value` messages. One definition per variable enforced.
5. **Pull-based model** (Livebook Kino): `Kino.Input.read/1` reads on demand. Shared inputs (all users see changes) vs. per-user controls. Staleness detection via input hashes in `cell_snapshot`.
6. **Symmetric two-way binding via comm protocol** (ipywidgets): 40+ types. JSON over ZMQ/WebSockets. Delta compression with `hold_sync()`. `sync=True` traitlets. MIME type `application/vnd.jupyter.widget-view+json`. Foundation for ipyleaflet, bqplot, ipyvolume, ipydatagrid, k3d, ipysheet, nglview, ipycytoscape, pythreejs.
7. **Complete script re-execution** (Streamlit): Protocol Buffers (BackMsg/ForwardMsg). `st.form` gates reruns. Fragments enable partial re-execution.

Additional paradigms: Gradio event-driven callbacks with concurrency control, Panel param-based reactivity with Bokeh PATCH-DOC messages, Shiny for Python implicit dependency tracking with three-tier reactive system (sources/conductors/endpoints). Google Colab form cells use `# @param` comment annotations with static options only (no dynamic population).

Marimo's approach is recommended for ContextKeeper: widgets are reactive variables that trigger re-execution of dependent cells on change, with the richest widget library (25+ types including data_explorer, altair_chart with selection, microphone, chat interface).

### Tier 4: Data (6 types)

**Table/DataFrame cells**: The most complex cell type. Implementations: Jupyter's `pandas.DataFrame.to_html()` (basic), Positron's Data Explorer (sparkline histograms, millions of rows, Convert to Code), Hex's DataFrameRenderer (virtual scrolling, column statistics), Deepnote's table view (column profiling, null counts, type badges), Observable's `Inputs.table` (sortable, searchable), Glide Data Grid (React component, 1M+ rows, used by Streamlit). **Spreadsheet cells**: Mito (`mitosheet.sheet(df)`) auto-generates pandas code from edits (Handsontable-based), ipysheet for bidirectional widget linking, Streamlit `st.data_editor` returns modified DataFrames, Sigma operates as spreadsheet-over-SQL with LLM functions callable in cells. ContextKeeper should adopt the Glide Data Grid pattern with Positron-style profiling.

**Profile cells**: Automated data profiling -- column statistics, distributions, correlations, missing values. ydata-profiling (via `to_widgets()` ipywidgets or `to_notebook_iframe()`), D-Tale (`dtale.show(df)` launches Flask server), Lux (auto-generated visualizations augmenting pandas). Databricks "Data Profile" tab computed on-demand via Spark. No notebook has a dedicated profile cell type; profiling is always via library calls or output tabs.

**Schema cells**: Display and enforce data schemas. Great Expectations (schema validation), Pandera (pandas schema enforcement), dlt (auto-inferred schemas). Hex and Deepnote both provide sidebar schema browsers with tree navigation, search, and table preview (Hex integrates dbt metadata including execution dates, source freshness, test status; both cache 7 days). A dedicated schema cell that validates DataFrames against contracts is novel.

**Validation cells**: Run data quality checks. Great Expectations, Soda, dbt tests. Similar to schema cells but focused on business rules rather than structural contracts.

**Writeback cells**: Hex has a dedicated Writeback cell type (select DataFrame, target table, write mode, execution modes: manual/session/app/scheduled). Sigma has writeback via Input Tables (not raw SQL DML). **No other notebook has a dedicated write-back cell type** -- all others require manual SQL DDL/DML or Python connector code.

### Tier 5: AI (5 types, expanded with new findings)

**Prompt/LLM cells**: Only one platform has a true first-class AI cell type: Google Colab (launched November 2025, Gemini-powered, but NOT context-aware and NOT executable -- output must be copied to code cells). The `google.colab.ai` Python API provides programmatic access with streaming. ContextKeeper has a dedicated `prompt` cell type with per-cell model selector (5 Groq models), target language selector, voice input, and conversation mode. Jupyter AI `%%ai` magic provides the most flexible LLM integration with variable interpolation (`{variable_name}`, `{In[11]}`, `{Out[11]}`, `{Err[3]}`), format flags, and chain registration -- but is not a distinct cell type. Databricks `ai_query()` SQL function is the most production-ready: returns proper SQL column values enabling batch inference at scale with task-specific functions (`ai_extract`, `ai_classify`, `ai_translate`, `ai_summarize`, `ai_similarity`, `ai_parse_document`).

AI-augmented cell generation (not dedicated cell types): Hex Magic (full DAG + schema context via "Context Studio"), Databricks Assistant/Genie Code (three modes: Chat/Edit/Agent, slash commands, DatabricksIQ with Unity Catalog metadata), Deepnote Auto AI (autonomous generation with guardrails), Microsoft Fabric Copilot (MCP server tools, approval workflow requiring consent before execution), Marimo AI (three sidebar modes including Agent mode that edits/runs cells, `@variable` syntax for live data injection, `mo.ui.chat()` with reactive `chat.value`).

LLM orchestration tools with prompt node patterns: LangChain LCEL (Runnable with pipe composition), LangGraph (StateGraph with typed state and checkpointing), Vellum.ai (typed nodes, five tool types including MCP Server), Rivet (visual graph IDE with typed ports), CrewAI (role-based multi-agent), AutoGen (ConversableAgent, v0.4 actor model), n8n (hierarchical LangChain JS with `$fromAI()`), Dust.tt (sequential blocks with shared state). **Key gap: no notebook platform offers built-in prompt versioning or A/B testing.** W&B Weave, Humanloop, PromptLayer, and Langfuse provide prompt versioning as separate tools.

**Key gap across all platforms:** No existing prompt/LLM cell type has full DAG participation where the LLM's output is automatically typed, assigned to a variable, and available to downstream cells without manual intervention. This is the opportunity for ContextKeeper's agent cell design.

**Agent pipeline cells**: LangGraph (graph-based agent workflows), AutoGen (multi-agent conversations), CrewAI (role-based agents). None are notebook cell types -- they are standalone frameworks. ContextKeeper's Agent Cell as DAG node is CONFIRMED NOVEL.

**AI narrative cells**: AI-generated text explanations of data/results. Hex has "Explain" feature. ContextKeeper's planned AI narrative cell would generate publication-quality text from cell outputs.

**AI fix cells**: AI-powered error fixing. GitHub Copilot suggests fixes for errors. JupyterAI can explain errors. A dedicated cell type that catches errors and proposes fixes is not implemented anywhere.

**AI optimize cells**: AI-powered code optimization. Codium/CodiumAI suggests optimizations. A dedicated cell type that profiles and optimizes code is not implemented anywhere.

### Tier 6: Pipeline (6 types)

**Contract cells**: Define typed input/output schemas for cells. Closest prior art: dlt auto-infer (pipeline-level), Pandera (validation library), NBLyzer (Subotic 2022, abstract interpretation). A dedicated contract cell type with auto-inference is PARTIAL prior art.

**Branch cells**: Create parallel execution branches from a common state. Livebook's branching sections are the closest prior art. A notebook cell that creates a named branch with automatic state copying is novel in the notebook context.

**Comparison cells**: Side-by-side comparison of branch outputs with statistical testing. No prior art in notebooks. Closest: mlxtend's paired statistical tests, SageMaker shadow deployment comparison.

**Decision/Router cells**: Conditional routing in notebook execution. KNIME's IF Switch node, Mage.ai's conditional blocks, Airflow's BranchPythonOperator. In the notebook context, a dedicated decision cell type is novel.

**Merge cells**: Combine results from multiple branches. No prior art in notebooks. Git merge is the conceptual model.

**Approval/Gate cells**: Human-in-the-loop approval before pipeline continues. Closest equivalents: Livebook `Kino.interrupt!/2` (pauses evaluation, displays "Continue" button), Prefect `pause_flow_run`/`suspend_flow_run` (with `wait_for_input` accepting Pydantic BaseModel for form rendering), n8n Wait Nodes (resume on duration/webhook/form with approval URL), Marimo `mo.stop(condition, output)` (halts reactive propagation). Airflow has 13 trigger rules but no native human gate. In notebooks, this remains NOVEL -- no platform has a dedicated approval cell type.

### Tier 7: Agent (4 types)

**Autonomous agent cells** (CONFIRMED NOVEL): An agent with typed inputs, outputs, and tool declarations that participates in the notebook's reactive DAG. When upstream cells change, the agent re-executes with new inputs. No existing platform implements this -- LangGraph agents are standalone, not reactive DAG nodes.

**Tool-using agent cells**: Agents with access to notebook-defined tools (other cells, data, APIs). Extends the autonomous agent pattern with tool integration.

**Multi-agent orchestration cells**: Multiple agents collaborating on a task within a single cell. AutoGen's multi-agent conversations are the closest prior art, but not as notebook cell types.

**Tournament cells**: Multiple model/agent configurations compete on the same input; statistical testing selects the winner. PyCaret's `compare_models()` function is the closest prior art but operates at the function level, not the cell level.

### Tier 8: Infrastructure (10 types)

**Version history cells**: Cell-level version tracking. Jupyter has notebook-level checkpoints. Kishu (VLDB 2024) provides checkpoint/restore. Cell-level granularity is partially novel.

**Diff cells**: Visual diff of cell outputs across versions/branches. nbdime for notebook diffs, ReviewNB for GitHub PR notebook diffs. A dedicated diff cell type is novel.

**Test cells**: Dedicated test execution cells. nbval (pytest plugin, cell markers: `# NBVAL_CHECK_OUTPUT`, `# NBVAL_SKIP`, etc.), testbook (external test files with `@testbook` decorator and `tb.ref()` callable proxy), nbmake (top-to-bottom execution), nbgrader (structured taxonomy: Autograder Tests with point values, Autograded Answer with solution stubs, hidden test sections). ContextKeeper has a dedicated `test` cell type with pass/fail badge rendering.

**Benchmark cells**: Performance measurement cells. `%%timeit` magic in Jupyter. A dedicated cell type with statistical benchmarking (multiple runs, confidence intervals) is novel.

**Export cells**: Export pipeline to production format. Ploomber exports to Airflow/Kubernetes. A dedicated cell type for export configuration is novel.

**Connection cells**: Database/API connection configuration. Livebook's Smart Cells for connections (Postgrex, MyXQL, Exqlite, Tds, ADBC adapters with rasterizable generated code). Hex has connection tiles. A dedicated cell type with connection pooling and health monitoring is partially implemented.

**Environment/Config cells**: Runtime configuration (Python version, packages, environment variables). Livebook's Setup Cell uses `Mix.install/2` with global caching and Hex.pm search UI. Marimo embeds PEP 723 inline script metadata, auto-installed via uv in isolated sandboxes. A dedicated config cell type with validation is partially implemented.

**Scratch/Draft cells**: ContextKeeper has a dedicated `scratch` cell type (dashed border, excluded from Run All). Marimo has scratchpad cells -- ephemeral execution cells that don't persist. Unique debugging primitive.

### Extensibility Registry Findings (New from Master Merge)

Four platforms support true cell-type extensibility -- plus several additional models discovered:

1. **Livebook Smart Cells** (gold standard): `Kino.SmartCell` behaviour with 5 required + 3 optional callbacks. Rasterization model is the architectural breakthrough -- cells degrade gracefully to plain code. 30+ community smart cells on Hex.pm.
2. **ComfyUI NODE_CLASS_MAPPINGS** (most mature registry): `INPUT_TYPES`/`RETURN_TYPES`/`FUNCTION`/`CATEGORY` protocol. 4,000-10,000+ unique node types. V3 API adds async and type-safe IO classes. ComfyUI Manager indexes 2,000+ packages.
3. **Zeppelin interpreters** (original cell-type-as-plugin): 20+ built-in, extensible via Java `Interpreter` class with interpreter-setting.json registration.
4. **Starboard** (browser-based, dormant): Plugin cell types via `runtime.controls.registerPlugin()`.
5. **n8n custom nodes**: `INodeType` interface with declarative and programmatic styles. npm packaging.
6. **Node-RED**: Two-file registration (JS runtime + HTML editor). npm packages.
7. **Apache NiFi**: `AbstractProcessor` with `PropertyDescriptor`/`Relationship`. NAR archive packaging.
8. **Streamlit custom components**: iframe isolation with `declare_component()`. pip packages.
9. **Gradio custom components**: `gradio cc` CLI with Svelte frontend. preprocess/postprocess pattern.
10. **Panel ReactiveHTML**: No-build components via `_template` + `_scripts` with bidirectional param sync.
11. **nteract 2.0**: MCP server with 27 tools for AI agent notebook manipulation via Automerge CRDT.

**Jupyter's fixed three-type schema** (code, markdown, raw in nbformat v4.5) blocks the entire ecosystem. Issues #1937 and #4801 remain unresolved. JupyterLab extensions can add MIME renderers via `IRenderMimeRegistry` but cannot add new cell kinds.

Five architectural patterns for a universal cell registry: (1) Rasterization (Livebook -- cells degrade to code), (2) Typed-port graph (ComfyUI -- declarative I/O schemas), (3) Reactive variable binding (Marimo/Observable -- DAG from variable references), (4) MIME-based extension (JupyterLab -- backward-compatible output renderers), (5) Iframe isolation (Streamlit/Retool -- secure third-party sandboxing). **No platform combines all five.** The recommended foundation for ContextKeeper: ComfyUI's typed I/O declarations + Livebook's rasterization + SQLMesh's per-model dialect transpilation via SQLGlot.

---

## 6. Variable Explorer State of the Art

### Best-in-Class Per Capability

**Spyder** (editing depth). Spyder's Variable Explorer is the gold standard for variable editing. Features: inline scalar editing (click to edit numbers, strings, booleans), array heatmap visualization (NumPy arrays displayed as color-coded grids), CollectionsEditor for nested structures (dicts, lists, sets), DataFrame viewer with sorting/filtering, image viewer for NumPy arrays interpreted as images. Performance limit: approximately 500K elements before the UI becomes unresponsive. Spyder's architecture uses a separate `SpyderKernelComm` channel for variable inspection, avoiding IPython message queue contention.

**VS Code** (deprecated approach). VS Code's Jupyter extension used kernel-side silent execution (`execute_request` with `silent=True`) to inspect variables. SlickGrid provided virtual scrolling for DataFrames. Microsoft deprecated this approach in favor of Data Wrangler, a dedicated data transformation extension. Data Wrangler generates pandas code from UI operations (filter, sort, group, join). Lesson: variable exploration is evolving toward code generation, not just inspection.

**Positron** (protocol and scale). Positron's Data Explorer is the current state of the art. Built on the OpenRPC protocol (JSON-RPC 2.0), it separates the frontend viewer from the kernel-side data provider. Features: sparkline histograms in column headers (distribution at a glance), millions of rows via virtual scrolling and server-side pagination, "Convert to Code" generates dplyr (R), pandas (Python), or SQL from UI operations (filter, sort, group, join, mutate), column statistics (mean, median, std, null count, unique count) computed lazily on scroll. The OpenRPC protocol is clean, extensible, and language-agnostic -- the same viewer works for R data.frames and Python DataFrames.

**RStudio** (workspace management). RStudio's Environment pane shows all workspace objects with `object.size()` memory display. Histogram filter sliders for numeric columns. "View()" opens a dedicated data viewer. Workspace save/load persists the entire environment as .RData. Strengths: memory awareness (shows object sizes), workspace persistence. Weaknesses: limited profiling, no code generation, R-only.

**Deepnote** (inline profiling). Deepnote's variable explorer shows column-level distribution histograms, null counts as percentage bars, data-type badges (int64, float64, object, datetime), and quick statistics (min, max, mean) inline with the table view. This profiling-first approach surfaces data quality issues without explicit profiling calls. Strengths: data quality visibility, no-code profiling. Weaknesses: limited to display (no editing, no code generation).

**Hex** (DAG-aware variables). Hex's variable panel shows variables as pills with dependency information. Variables are tagged as "Query output" or "DataFrame" with visual indicators of their position in the DAG. Clicking a variable highlights its dependencies and dependents. Strengths: DAG awareness, dependency visualization. Weaknesses: limited editing, no profiling depth.

### Gaps No Explorer Fills

1. **Variable lineage tracking**: No explorer shows where a variable came from (which cell created it, what transformations were applied, what data sources contributed). Provenance is tracked at the notebook level (ProvBook, ISWC 2018) but not at the variable level.

2. **Drift detection across runs**: No explorer compares variable distributions across runs to detect data drift. Evidently AI and Great Expectations detect drift but are separate tools, not integrated into variable explorers.

3. **Distributed data inspection**: No explorer can inspect Dask DataFrames, Spark DataFrames, or Ray Datasets without calling `.compute()` or `.collect()`, which materializes the entire dataset. Inspecting distributed data in-place (schema, sample, partition statistics) without materialization is an unsolved UI problem.

4. **Cross-notebook variable comparison**: No explorer compares variables across notebooks. brain-plasma and shared kernels allow cross-notebook variable sharing but not comparison.

5. **Live updating during execution**: All explorers show variable state after cell execution completes. No explorer updates in real-time as a long-running cell executes (e.g., showing a DataFrame growing row-by-row during a data load).

6. **Natural language querying**: No explorer supports querying variables via natural language (e.g., "show me rows where revenue > 1M and region is APAC"). Hex's AI sidebar can generate such queries but not from within the variable explorer.

**Recommended for ContextKeeper**: Positron's OpenRPC protocol as the communication layer (clean, extensible, language-agnostic) + Spyder's editing depth (inline scalar editing, collection editors) + Deepnote's inline profiling (distribution histograms, null counts) + variable lineage tracking as a novel capability.

---

## 7. Experiment Tracking and Branch/Compare/Replace

### 9 Trackers Analyzed

**MLflow** (25M+ monthly PyPI downloads). The dominant open-source experiment tracker. Core abstractions: Experiments, Runs, Parameters, Metrics, Artifacts, Models. MLflow Tracking logs parameters and metrics. MLflow Models provides a standard packaging format. MLflow Model Registry manages model lifecycle (staging, production, archived). Strengths: universal adoption, simple API (`mlflow.log_param`, `mlflow.log_metric`), language-agnostic (Python, R, Java, REST), model registry, community-driven. Weaknesses: UI is basic (table of runs with metric columns, no built-in statistical comparison), no automatic logging for all frameworks, no statistical significance testing, self-hosted requires infrastructure. MLflow's parallel coordinates and scatter plots can visualize experiment comparisons but do not compute statistical tests.

**Weights & Biases (W&B)** (best UI, Bayesian HPO). Best-in-class experiment tracking UI with real-time dashboards. W&B Sweeps provides Bayesian hyperparameter optimization. W&B Tables for dataset versioning. W&B Reports for sharing analysis. Strengths: excellent visualization (custom charts, parallel coordinates, parameter importance), Bayesian HPO, real-time collaboration, artifact lineage. Weaknesses: proprietary SaaS (self-hosted is enterprise-only), expensive for large teams, no built-in statistical significance testing, vendor lock-in.

**Neptune** (1M+ data points/sec ingestion, acquired by OpenAI 2024). High-performance metadata store designed for large-scale experiments. Namespace-based organization (`run["params/lr"] = 0.001`). Strengths: highest ingestion rate (1M+ data points/sec), flexible metadata structure, good for large-scale HPO, strong comparison UI. Weaknesses: proprietary, acquired by OpenAI (future uncertain), no statistical testing.

**ClearML** (zero-code capture). Automatic logging with zero code changes -- just import ClearML and it captures parameters, metrics, plots, model files, git diff, installed packages, and hardware metrics. Strengths: zero-code capture is genuinely useful, includes pipeline and serving components, self-hosted option, open source. Weaknesses: less polished UI than W&B, documentation gaps, smaller community.

**Comet** (Python panels). Custom visualization panels written in Python. Strengths: Python panel extensibility, good API design, artifact management. Weaknesses: smaller community, fewer integrations than MLflow/W&B.

**Aim** (free, native statistical visualization). Open-source experiment tracker with built-in statistical comparisons. Native distribution visualizations. Aim UI is React-based with good performance. Strengths: free and open source, native stat viz is closest to ContextKeeper's vision, good local performance. Weaknesses: small community, limited cloud features, no Bayesian HPO.

**DVC** (Git-native). Data Version Control uses Git for code and DVC for data/models. `.dvc` files track data versions. DVC experiments branch Git for each experiment run. Strengths: Git-native (familiar workflow), data versioning, pipeline definition, integrates with existing Git infrastructure. Weaknesses: complexity (Git + DVC + remote storage), limited UI, no real-time tracking, no statistical testing.

**Sacred**. Automatic configuration capture with MongoDB backend. Observer pattern logs everything. Strengths: automatic capture, flexible storage backends, good for academic research. Weaknesses: limited UI (relies on Omniboard or Sacredboard), no active development, small community.

**Guild AI**. CLI-focused experiment management. Strengths: simple CLI, automatic resource tracking, no code changes required. Weaknesses: CLI-only (limited UI), small community.

### Key Gap Across All 9 Trackers

No tracker includes built-in statistical significance testing for experiment comparison. Users must export metrics to scipy, statsmodels, or mlxtend for statistical testing. This is the central gap ContextKeeper's Branch/Compare/Replace addresses.

### Statistical Tests for Branch/Compare/Replace

The following tests are recommended based on the statistical machine learning literature:

**Regression tasks**: Primary metrics: RMSE, MAE, R-squared, MAPE. Comparison test: paired t-test on per-sample squared errors (Dietterich 1998, "Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms"). The paired t-test compares two models' performance on the same test set, controlling for data variation. Assumption: normally distributed differences. When normality is violated, use Wilcoxon signed-rank test.

**Classification tasks**: Primary metrics: F1, AUC-ROC, precision, recall, balanced accuracy. Comparison test: McNemar's test (Demsar 2006, "Statistical Comparisons of Classifiers over Multiple Datasets"). McNemar's test compares two classifiers on the same test set by examining the 2x2 contingency table of agreements and disagreements. More powerful than paired t-test for classification because it directly tests prediction differences rather than metric differences. For multiple classifiers: Friedman test with Nemenyi post-hoc (Demsar 2006).

**LLM output evaluation**: DeepEval metrics: faithfulness (does the output use only provided context?), relevancy (does the output address the question?), coherence (is the output internally consistent?), bias (does the output show systematic bias?), toxicity. These metrics are computed by a judge LLM evaluating the target LLM's output. Statistical comparison: bootstrap confidence intervals on per-sample DeepEval scores.

**Any numeric metric**: Wilcoxon signed-rank test (Benavoli et al. 2017, "Time for a Change: a Tutorial for Comparing Multiple Classifiers Through Bayesian Analysis"). Non-parametric, makes no distributional assumptions. Recommended as the default test when the metric distribution is unknown.

**Time series forecasts**: Diebold-Mariano test (Diebold & Mariano 1995). Tests whether two forecasts have equal predictive accuracy. Handles autocorrelated forecast errors.

**Sequential testing**: For valid-at-any-sample-size comparison (no peeking problem). Based on the sequential probability ratio test (SPRT, Wald 1945). Allows checking results at any point during data collection without inflating Type I error. Essential for ContextKeeper's "live" branch comparison where users want to see results before all data is processed.

---

## 8. Novel Feature Validation (12 Features)

### Feature 1: Living Pipeline

**Verdict**: PARTIAL prior art.

**Prior art**: Deephaven Community Core provides live-updating tables that react to streaming data. Tables are defined as views over real-time data sources and automatically recalculate when data changes. Observable's generator cells can yield values at up to 60fps, creating continuously-updating displays. Apache Flink provides stateful stream processing. Kafka Streams enables real-time data transformations.

**Gap ContextKeeper fills**: No notebook platform has cells that continuously execute on streaming data with reactive dependency propagation. Deephaven's live tables are a BI/dashboard tool, not a notebook. Observable's generators are client-side only with no server-side data integration. A "living pipeline" where notebook cells maintain persistent state and react to external data changes (database updates, API webhooks, file system events) does not exist in any notebook.

### Feature 2: Branch/Compare/Replace

**Verdict**: PARTIAL prior art.

**Prior art**: mlxtend (Raschka 2018) provides paired statistical tests for model comparison (McNemar's, cochran_q, paired_ttest_5x2cv). SageMaker shadow deployment runs two models on production traffic and compares outputs. Livebook's branching sections create parallel execution paths. DVC experiments use Git branches for experiment tracking. PyCaret's compare_models() runs multiple algorithms on the same data.

**Gap ContextKeeper fills**: No platform combines branch creation (fork notebook state), parallel execution on the same data, automated statistical comparison (with configurable significance tests), and branch replacement (promote winner to main) in a single workflow. Each piece exists in isolation -- branching in Livebook, comparison in mlxtend, replacement in SageMaker -- but the unified workflow is novel.

### Feature 3: Tournament Cells

**Verdict**: PARTIAL prior art.

**Prior art**: PyCaret's `compare_models()` trains and evaluates multiple algorithms in a single call, returning a ranked table. H2O AutoML's leaderboard compares models automatically. Ray Tune provides distributed hyperparameter search with configurable schedulers.

**Gap ContextKeeper fills**: A dedicated cell type where users define multiple model configurations, the cell runs all configurations on the same data with cross-validation, applies statistical tests (not just metric ranking), and returns a validated winner with confidence intervals. PyCaret ranks by metric value without significance testing. Tournament cells add statistical rigor to model comparison.

### Feature 4: Cell Metrics + Drift Detection

**Verdict**: PARTIAL prior art.

**Prior art**: jupyterlab-execute-time extension displays cell execution duration. Jupyter's `%%time` and `%%timeit` magics measure cell performance. Evidently AI detects data drift and model drift with statistical tests (KS test, PSI, Wasserstein distance). Great Expectations validates data against expectations.

**Gap ContextKeeper fills**: No platform tracks cell-level metrics (execution time, memory usage, output shape, output distribution) across runs and automatically detects drift in these metrics. jupyterlab-execute-time shows current execution time but does not store history or detect trends. Evidently AI detects data drift but operates on DataFrames, not cell outputs, and is a separate tool. Integrated cell-level metric tracking with automatic drift detection is novel.

### Feature 5: Agent Cells as DAG Nodes

**Verdict**: CONFIRMED NOVEL.

**Strongest prior art**: LangGraph (LangChain) defines agent workflows as directed graphs with typed state. AutoGen (Microsoft) enables multi-agent conversations. CrewAI provides role-based agent orchestration. Amazon Bedrock Agents provides managed agent execution.

**Why none qualify**: All existing agent frameworks are standalone -- agents run as separate processes or services, not as nodes in a notebook's reactive dependency graph. LangGraph's graph is an agent-internal control flow graph, not a notebook execution DAG. When a notebook cell's output changes, no existing system can automatically re-trigger an agent that depends on that output. ContextKeeper's Agent Cell participates in the reactive DAG: it has typed inputs (from upstream cells), typed outputs (consumed by downstream cells), tool declarations (which cells/APIs it can call), and reacts to upstream changes like any other cell. This integration of autonomous agents into reactive notebook execution has no prior implementation.

### Feature 6: Decision/Router Cells

**Verdict**: PARTIAL prior art.

**Prior art**: KNIME's IF Switch node routes data based on boolean conditions. Mage.ai's conditional blocks enable if/else branching in pipelines. Airflow's BranchPythonOperator selects downstream tasks based on Python logic. Node-RED's Switch node routes messages based on property values.

**Gap ContextKeeper fills**: No notebook has a cell that conditionally routes execution to different downstream cells based on runtime evaluation. Pipeline frameworks (Airflow, Mage.ai) have conditional routing but at the pipeline/task level, not the cell level within a notebook. KNIME has it in a visual workflow but not in a computational notebook. A decision cell that evaluates a condition and selectively triggers downstream branches within a notebook is novel.

### Feature 7: Bidirectional Notebook-Canvas Sync

**Verdict**: PARTIAL prior art.

**Prior art**: Enso (formerly Luna) provides dual visual/textual representation where code and visual nodes stay synchronized. Blockly generates code from visual blocks. Node-RED has a code view alongside the visual flow. Count's SQL canvas shows queries as connected nodes.

**Gap ContextKeeper fills**: No platform maintains bidirectional sync between a linear notebook view and a spatial canvas view where the same cells exist in both representations. Enso's dual representation is for general-purpose programming, not notebooks. Count's canvas is SQL-only. The ability to work in whichever view is appropriate (linear for writing, canvas for architecture) with changes reflected in both is novel in the notebook context.

### Feature 8: Cell Contracts + Auto Schema Inference

**Verdict**: PARTIAL prior art.

**Prior art**: dlt (data load tool) auto-infers schemas from data sources and enforces them across pipeline runs. Pandera provides DataFrame schema validation with decorators. Great Expectations validates data against expectations. NBLyzer (Subotic et al. 2022, ECOOP) uses abstract interpretation to analyze notebook cell contracts, achieving 98.7% analysis completion under 1 second.

**Gap ContextKeeper fills**: No notebook has built-in cell-level contracts that declare input types and output schemas, with automatic schema inference from cell execution. dlt infers schemas at the pipeline level. Pandera requires manual schema definition. NBLyzer analyzed contracts but did not enforce them during execution. Cell contracts that auto-infer schemas from runtime execution and then enforce them on subsequent runs are novel.

### Feature 9: Transactional Undo

**Verdict**: PRIOR ART EXISTS.

**Prior art**: Kishu (VLDB 2024, Zheng et al.) provides session-level checkpoint and restore for Jupyter notebooks. Kishu intercepts kernel state at checkpoints, stores incremental diffs, and enables "time travel" to any previous state. The system handles Python objects, file system state, and database connections. Granularity: session-level (not cell-level), achieving sub-second restore times via incremental checkpointing.

**ContextKeeper nuance**: While Kishu provides checkpoint/restore, it does not provide transactional semantics (atomic commit/rollback of multi-cell operations). A true transactional undo that rolls back a sequence of cell executions atomically, including side effects, would extend beyond Kishu's capabilities. However, the core checkpoint/restore mechanism is well-established.

### Feature 10: Cross-Notebook Variables

**Verdict**: PRIOR ART EXISTS.

**Prior art**: brain-plasma provides shared-memory variables across Jupyter notebooks using Apache Plasma (Arrow's in-memory object store). Jupyter's shared kernel model allows multiple notebooks to connect to the same kernel, sharing all variables. Databricks' spark context is shared across notebooks in the same cluster. IPython's `%store` magic persists variables across sessions.

**ContextKeeper nuance**: While cross-notebook variable sharing exists, typed cross-notebook variable contracts (declaring what variables a notebook exports and imports, with schema validation) do not. This extends beyond simple sharing into a module-like system for notebooks.

### Feature 11: Cell-Level RBAC

**Verdict**: CONFIRMED NOVEL.

**Strongest prior art**: Google Sheets range protection allows specific cells/ranges to be locked to specific users/groups. Confluence page restrictions control who can edit specific pages. Jupyter has no access control below the notebook level. Databricks has notebook-level permissions through Unity Catalog.

**Why novel**: No computational notebook implements access control at the cell level. In collaborative data science, certain cells may contain proprietary models, sensitive data queries, or production deployment code that should be editable only by specific team members while remaining visible (or even invisible) to others. Google Sheets' range protection is the closest conceptual prior art but operates in a spreadsheet, not a computational notebook with code execution, dependency graphs, and reactive updates. Cell-Level RBAC must integrate with the reactive execution model -- when a protected cell's output is needed by a downstream cell, the system must handle permissions for automatic re-execution.

### Feature 12: Audit Log + Provenance

**Verdict**: PARTIAL prior art.

**Prior art**: ProvBook (ISWC 2018, Samuel & Konig) captures provenance information for Jupyter notebooks using the W3C PROV model. noWorkflow (Murta et al. 2015) captures function-level provenance automatically. Reprozip (Chirigati et al. 2016) packages execution environments for reproducibility. MLflow tracks experiment provenance (parameters, metrics, artifacts).

**Gap ContextKeeper fills**: No notebook provides a comprehensive audit log that records who edited which cell, when, what changed, what was executed, what the output was, and links this to the provenance graph. ProvBook captures provenance but not audit (who/when). noWorkflow captures execution provenance but not edit history. MLflow captures experiment provenance but not cell-level provenance. A unified audit + provenance system at cell granularity is novel.

---

## 9. Academic Foundations

### Chattopadhyay et al. 2020: "What's Wrong with Computational Notebooks?"

Survey of 156 data scientists (primarily at Microsoft) identifying 9 pain points with computational notebooks. Published at CHI 2020.

1. **Out-of-order execution / hidden state**: Users execute cells non-linearly, creating hidden dependencies and stale variables. ContextKeeper addresses this via reactive execution that enforces dependency-order execution.

2. **Difficulty managing long notebooks**: Notebooks grow to hundreds of cells. ContextKeeper addresses this with cell grouping, folding, and the bidirectional canvas view for spatial organization.

3. **Lack of code quality tools**: No linting, type checking, refactoring, or testing in notebooks. ContextKeeper addresses this with cell contracts (type checking), dedicated test cells, and integration with standard Python tooling.

4. **Notebook version control is painful**: JSON diffs are unreadable, merge conflicts are common. ContextKeeper addresses this with cell-level version history and reactive .py file storage (following Marimo's pattern).

5. **Difficulty deploying notebooks**: Notebooks do not map to production code. ContextKeeper addresses this with pipeline cells that export to production formats (Airflow, Kubernetes, standalone Python).

6. **Difficulty sharing and collaborating**: Notebooks are files, not collaborative documents. ContextKeeper addresses this with real-time collaboration (Yjs-based CRDT) and cell-level RBAC for granular sharing.

7. **Difficulty finding and reusing code**: No module system for notebooks. ContextKeeper addresses this with cross-notebook variables and a cell/notebook registry.

8. **Difficulty with data management**: No built-in data versioning or cataloging. ContextKeeper addresses this with Kedro-style typed Data Catalog integration.

9. **Difficulty debugging**: Limited debugging tools in notebooks. ContextKeeper addresses this with cell contracts (schema violations caught early), branch/compare (A/B debugging), and integrated debugging via CodeMirror.

### Lau et al. 2020: "The Design Space of Computational Notebooks"

10-dimension design space for notebooks. Published at VL/HCC 2020.

1. **Data flow model**: implicit (Jupyter) vs. reactive (Marimo) vs. dataflow (Observable). ContextKeeper: reactive with contracts.
2. **Execution model**: on-demand vs. reactive vs. continuous. ContextKeeper: reactive with living pipeline option.
3. **Programming paradigm**: imperative (Jupyter) vs. declarative (Observable) vs. mixed. ContextKeeper: imperative with declarative contracts.
4. **Collaboration model**: none vs. async vs. real-time. ContextKeeper: real-time (Yjs CRDT).
5. **Persistence model**: file (Jupyter .ipynb) vs. database vs. cloud. ContextKeeper: file (.py like Marimo) + database for metadata.
6. **Output model**: inline vs. separate pane vs. app. ContextKeeper: inline with optional app builder.
7. **Versioning model**: none vs. checkpoint vs. Git-native. ContextKeeper: Git-native (.py files) + cell-level history.
8. **Sharing model**: file export vs. URL vs. embedded. ContextKeeper: all three.
9. **Cell granularity**: code block vs. expression vs. function. ContextKeeper: code block with function-level contracts.
10. **Extensibility model**: none vs. plugins vs. cell types. ContextKeeper: 78 cell types with ComfyUI-style node registry.

### Pimentel et al. 2019/2021: Reproducibility Crisis

"A Large-Scale Study About Quality and Reproducibility of Jupyter Notebooks" (MSR 2019). Analyzed 1,453,085 Jupyter notebooks from GitHub. Key findings:

- Only 24.11% could be executed without errors.
- Only 4.03% produced the same results when re-executed.
- 36.5% of notebooks had at least one undefined variable.
- Average notebook: 18 cells, 86 lines of code.
- Most common imports: numpy, pandas, matplotlib, sklearn, os.

Follow-up (2021) analyzed notebook evolution and found that notebooks grow monotonically -- cells are added but rarely removed or refactored.

**ContextKeeper response**: Typed contracts + reactive execution address the root causes. Contracts catch undefined variables and type mismatches at cell boundaries. Reactive execution eliminates hidden state from out-of-order execution. Together, they address the two primary causes of non-reproducibility (stale state and implicit dependencies).

### Head et al. 2019: Code Gathering

"Managing Messes in Computational Notebooks" (CHI 2019). Introduces "code gathering" -- a tool that traces the dependencies of a selected variable and extracts a minimal, clean notebook containing only the cells needed to produce that variable. Uses program slicing (Weiser 1981) adapted for notebook cells.

**Relevance to ContextKeeper**: Code gathering is a precursor to branch/compare. The ability to trace a variable's dependency chain and extract it as a clean sub-notebook maps directly to creating a branch from a specific cell. ContextKeeper's branch/compare extends this concept by allowing two gathered sub-notebooks to be compared statistically.

### Rex (Zheng et al. 2025): Reactive Execution Failures

"Rex: A Systematic Evaluation of Reactive Execution in Notebooks." Systematic evaluation of Marimo, Pluto.jl, and Observable on edge cases. Key findings:

- All three systems fail on in-place mutations (`list.append()`, `dict.update()`, `df.iloc[0] = ...`).
- All three fail on aliased variables (`b = a; b.append(1)` does not trigger re-execution of cells depending on `a`).
- Observable handles more dynamic patterns than Marimo/Pluto due to JavaScript's event-driven model but still fails on shared mutable state.

**ContextKeeper response**: Typed contracts serve as an escape hatch. When a cell declares `@contract(inputs={"data": pd.DataFrame}, outputs={"result": pd.DataFrame, "schema": {"columns": ["a", "b", "c"]}})`, the execution engine uses the contract for dependency resolution rather than AST analysis. This makes mutations explicit: if a cell mutates a DataFrame, the contract declares it as an output, triggering downstream re-execution.

### Tanimoto 1990: Liveness Levels

"VIVA: A Visual Language for Image Processing." Defines four levels of liveness for programming environments:

- Level 1: Informative (code is displayed but not executable).
- Level 2: Significant (code can be executed on demand).
- Level 3: Responsive (changes propagate automatically -- reactive execution).
- Level 4: Live (continuous execution with real-time feedback).

Jupyter is Level 2 (on-demand execution). Marimo/Observable are Level 3 (reactive). Excel is Level 3. ContextKeeper targets Level 4 (continuous) via living pipelines that react to streaming data in real-time. No current notebook achieves Level 4.

### NBLyzer (Subotic et al. 2022): Abstract Interpretation for Notebooks

"Static Analysis of Data Science Code" (ECOOP 2022). NBLyzer uses abstract interpretation to analyze notebook cells, building a contract-like model of cell inputs and outputs without executing the cells. Key results:

- 98.7% of cells analyzed in under 1 second.
- Detected 13 categories of issues: undefined variables, type errors, unused imports, deprecated API calls.
- Abstract interpretation provides stronger guarantees than AST analysis alone because it models value flow, not just name flow.

**Relevance to ContextKeeper**: NBLyzer validates that static analysis of cell contracts is feasible at interactive speeds. ContextKeeper's auto-inference can use a similar abstract interpretation approach to infer contracts from cell code, then enforce those contracts during reactive execution.

---

## 10. Node Registry Architecture

### 7 Systems Analyzed

**ComfyUI** (Stable Diffusion UI, 20K+ custom nodes). The most relevant registry architecture for ContextKeeper. Each node is a Python class with `INPUT_TYPES` (class method returning typed input spec) and `RETURN_TYPES` (tuple of output types). Input spec includes required/optional fields with type annotations, default values, min/max constraints, and UI widget hints. The registry discovers nodes by scanning Python files in the `custom_nodes/` directory. ComfyUI Manager provides marketplace functionality for installing community nodes. Strengths: typed I/O is the right pattern, massive community (20K+ custom nodes), runtime type checking. Weaknesses: no versioning (breaking changes are common), no sandboxing (custom nodes execute arbitrary code), flat namespace (name collisions between packages).

**VS Code Extensions** (marketplace with semver). VS Code's extension model uses `package.json` for declaration, `contributes` key for UI integration points, and semantic versioning for compatibility. Extensions are distributed via a marketplace with ratings, download counts, and publisher verification. Activation events control when extensions load (lazy by default). Strengths: mature marketplace model, semver for compatibility, lazy loading, sandboxed extension host process. Weaknesses: extension API is complex, marketplace quality varies.

**Node-RED** (npm-based flow library). Node-RED nodes are npm packages with `node-red` keyword. Each node has an HTML file (editor UI) and a JS file (runtime behavior). The palette manager installs/removes nodes dynamically. Strengths: npm ecosystem for distribution, dynamic installation, standardized node structure. Weaknesses: JavaScript-only, limited typing, no formal contracts.

**Unreal Blueprints**. Visual scripting with typed pins (execution flow and data). Strong type system with automatic casting. Strengths: best-in-class type system for visual programming, real-time preview. Weaknesses: game-engine specific, complex implementation.

**Houdini VOPs** (Visual Operators). Node-based procedural generation. Each VOP has typed inputs/outputs with automatic type promotion. Strengths: mature node architecture (25+ years), excellent type system. Weaknesses: domain-specific (3D/VFX).

**TouchDesigner**. Real-time visual programming with typed operators (TOPs, CHOPs, SOPs, DATs, MATs). Strengths: real-time execution, strong categorization, mature architecture. Weaknesses: proprietary, domain-specific.

**Grasshopper** (Rhino 3D). Parametric design with typed components. Food4Rhino marketplace for community components. Strengths: strong typing, good marketplace model, parametric design excellence. Weaknesses: domain-specific (architecture/design).

### Key Patterns

1. **Typed I/O declarations**: ComfyUI's `INPUT_TYPES`/`RETURN_TYPES` is the right pattern. Each cell type declares its inputs and outputs with types, constraints, and UI hints.

2. **Marketplace distribution**: VS Code's marketplace model with semver, ratings, and publisher verification provides the right distribution pattern.

3. **npm-based packaging**: Node-RED's use of npm for node distribution provides a proven packaging model.

### Recommended for ContextKeeper

ComfyUI-style typed I/O declarations for cell type definitions + SQLite full-text search index for fast filtering of the 1,546-entry registry + lazy loading via dynamic `import()` to avoid loading all cell types at startup + category hierarchy with maximum 2 levels (deeper nesting creates navigation problems per VS Code and ComfyUI user research). Registry entries should include: unique ID, display name, category, subcategory, typed inputs, typed outputs, description, icon, author, version (semver), dependencies.

Performance target for 10K+ node registry: SQLite FTS5 index supports sub-millisecond search on 100K+ entries. Lazy loading via dynamic import ensures only rendered cell types load their implementation code. Category tree renders only visible nodes with virtual scrolling (react-window or similar).

---

## 11. AI Infrastructure and Model Selection

### Open-Weight Landscape (as of April 2026)

**Llama 4 Scout** (Meta, 17B active parameters / 109B total MoE, 10M token context window). Released March 2026. Mixture-of-Experts architecture with 16 experts, 1 active. The 10M token context window is the largest of any open-weight model, enabling entire codebases to be processed in a single prompt. 128 experts total, 4 active per token for the Maverick variant (400B). Competitive with GPT-4o on benchmarks.

**Llama 3.3 70B** (Meta, recommended 70B class). Dense transformer, 70B parameters, 128K context. Strong coding performance (HumanEval 80.5+). Available on Groq with free tier. The recommended default model for ContextKeeper's AI features due to balance of quality, speed (Groq inference), and cost (free tier).

**DeepSeek-R1** (DeepSeek, 671B MoE). Reasoning-focused model that matches OpenAI o1 on math and coding benchmarks. 128K context. Open weights under MIT license. Notable for reinforcement learning training approach.

**Qwen 3** (Alibaba, Apache 2.0). Family of models from 0.6B to 235B. Apache 2.0 license (most permissive of major open models). Strong multilingual performance. Qwen-Agent framework for tool use.

**GPT-OSS** (OpenAI, first open weights). OpenAI's first open-weight model release. Details pending at time of compilation.

### MCP (Model Context Protocol)

MCP has been accepted as a Linux Foundation standard for AI tool integration. MCP defines a protocol for AI models to interact with external tools, data sources, and services through a standardized interface. Three core primitives: Resources (data access), Tools (function execution), Prompts (reusable templates). Transport: stdio for local, SSE for remote. ContextKeeper should implement MCP server support so that any MCP-compatible AI model can interact with notebook cells, variables, and data.

### Groq Free Tier Models for ContextKeeper

| Model | Use Case | Context | Speed |
|---|---|---|---|
| llama-3.3-70b-versatile | Primary (code gen, analysis) | 128K | ~330 tok/s |
| llama-3.1-8b-instant | Fast tasks (narrative, cost est) | 128K | ~750 tok/s |
| compound-beta | Search-augmented tasks | 128K | Varies |
| meta-llama/llama-4-scout-17b | Long context tasks | 10M | ~400 tok/s |

### Model Routing Strategy

Different AI features require different model characteristics:

- **Code generation**: 70B class (llama-3.3-70b-versatile). Code quality scales strongly with model size. 70B models produce significantly fewer bugs than 8B models on HumanEval and MBPP benchmarks.
- **Narrative generation**: 8B class (llama-3.1-8b-instant). Text generation quality is adequate at 8B for data science narratives. Speed matters more than marginal quality improvement.
- **Agent orchestration**: 70B class. Tool use and multi-step reasoning require larger models. LangChain benchmarks show 70B models complete 2-3x more agent tasks than 8B.
- **Evaluation/Judge**: 70B class. LLM-as-judge accuracy correlates with model size (Zheng et al. 2023, "Judging LLM-as-a-Judge").
- **Cost estimation / simple classification**: 8B class. Low-complexity tasks where speed dominates.

---

## 12. Architecture Migration Path

### Current State

The monolith consists of:
- `data-lab.html`: 15,403 lines, single HTML file containing the entire notebook application.
- Supporting JS libraries: approximately 7,000 lines across multiple files.
- Modern TypeScript: 4,320 lines across 24 files in the React/TypeScript rewrite.

The monolith implements 228+ `NB.*` functions covering: cell CRUD operations, execution (Jupyter kernel communication), save/load (.ipynb, custom format), export (HTML, PDF, .py, .ipynb, Markdown, LaTeX, Reveal.js, RISE), rendering (CodeMirror 5, Markdown, LaTeX), toolbar and menus, variable inspector, keyboard shortcuts.

### Migration Completion Status

| Category | Complete | Partial | Missing Standard | Novel (not started) |
|---|---|---|---|---|
| Core notebook | 12 | 3 | 4 | 0 |
| Execution | 4 | 1 | 3 | 4 |
| Data / display | 6 | 1 | 4 | 6 |
| Collaboration | 2 | 0 | 2 | 2 |
| Pipeline | 2 | 1 | 1 | 2 |
| **Total** | **26** | **6** | **14** | **14** |

Overall: 55% of standard features complete, 5% of novel features started.

### Strangler Fig Pattern

The migration follows the strangler fig pattern (Fowler 2004) rather than a big-bang rewrite. The key principle: the old and new systems coexist, with Nginx reverse proxy routing requests to the appropriate backend during transition.

**Phase 1 (current)**: React shell with Zustand state management, CodeMirror 6 editor, Monaco integration. Jupyter Kernel Gateway for Python execution. New features built exclusively in the React app.

**Phase 2 (next)**: Migrate cell rendering pipeline from DOM manipulation to React components. Implement reactive execution engine (Marimo-style AST analysis). Add typed cell contracts with auto-inference. Target: 80% of standard features.

**Phase 3**: Pipeline integration (Hamilton for browser, Kedro Data Catalog pattern for persistence). Branch/compare/replace with statistical testing. Agent cells. Target: 100% of standard features, 50% of novel features.

**Phase 4**: Living pipelines, tournament cells, cell-level RBAC, audit log. ComfyUI-style node registry for cell type marketplace. Target: 100% of features.

### What to Preserve

- 228+ `NB.*` functions: well-tested CRUD and execution logic. Wrap in TypeScript adapters rather than rewriting.
- 8 export formats: .ipynb, HTML, PDF, .py, Markdown, LaTeX, Reveal.js, RISE. Critical for user workflows.
- .ipynb compatibility: ContextKeeper must read and write standard .ipynb files. Native format can be .py (Marimo-style) with .ipynb import/export.

### What to Rewrite

- Rendering pipeline: DOM manipulation to React component tree. DOM manipulation does not compose with React's virtual DOM and will cause state synchronization bugs.
- State management: Global variables to Zustand stores. 228 `NB.*` functions use global state; each needs to be migrated to a Zustand slice.
- Editor: Custom implementation to CodeMirror 6 (notebook cells) + Monaco (IDE mode). Both are well-maintained and extensible.

### What to Incrementally Migrate

- Kernel communication: Current WebSocket protocol to Jupyter Kernel Gateway protocol. Can be proxied during transition.
- Save/load: Current format to .py + metadata sidecar. Maintain .ipynb import/export throughout.
- Collaboration: Add Yjs-based CRDT layer on top of Zustand stores for real-time sync.

### Target Architecture

- **Frontend**: React 18 + TypeScript strict + Vite + Zustand + React Flow (canvas) + CodeMirror 6 (cells) + Monaco (IDE)
- **Backend**: FastAPI (Python) + SQLAlchemy + MySQL
- **Execution**: Jupyter Kernel Gateway (server-side Python) + Pyodide (browser-side Python) + Hamilton (browser-side pipelines)
- **AI**: Groq API (free tier) + MCP protocol + configurable model routing
- **Infrastructure**: Nginx (reverse proxy + static files) + CloudPanel + Let's Encrypt

---

## 13. Strategic Gaps and Opportunities

### Confirmed Novel Features (No Platform Has These)

**Agent Cells as composable DAG nodes**. The integration of autonomous AI agents into a notebook's reactive dependency graph is unprecedented. LangGraph, AutoGen, CrewAI, and Amazon Bedrock Agents all treat agents as standalone systems. ContextKeeper's agent cells participate in reactive execution: when upstream data changes, the agent re-executes with typed inputs and produces typed outputs consumed by downstream cells. This enables workflows like "load data -> clean data -> agent analyzes anomalies -> human reviews agent output -> agent generates report" where each step is a reactive cell.

**Cell-Level RBAC**. No notebook implements access control below the notebook level. In enterprise data science, this is a critical gap: a single notebook may contain public data exploration, proprietary feature engineering, and production deployment code. Cell-Level RBAC allows different team members to have read/write/execute permissions on specific cells, enabling collaborative workflows without exposing sensitive code. Implementation must integrate with reactive execution -- when a protected cell needs re-execution, the system must handle permission elevation or cached results.

### Best-in-Class Opportunity (Weak Implementations Exist)

**Branch/Compare/Replace with statistical testing**. Livebook has branching, mlxtend has statistical tests, SageMaker has shadow deployment. Unifying these into a single notebook workflow -- fork state, execute in parallel, compare with configurable statistical tests, promote winner -- fills a gap that every data scientist currently handles manually with ad-hoc scripts.

**Cell contracts with auto-inference**. dlt auto-infers pipeline schemas, Pandera validates DataFrames, NBLyzer analyzes contracts statically. A system that auto-infers cell contracts from execution, stores them as metadata, and enforces them on subsequent runs (catching regressions at cell boundaries) does not exist.

**Living pipeline (continuous execution)**. Deephaven has live tables, Observable has generators, Apache Flink has stream processing. A notebook where cells maintain persistent state and react to external data changes in real-time does not exist.

**Bidirectional notebook-canvas sync**. Enso has dual visual/textual representation for general programming. Count has a SQL canvas. A system where the same cells exist in both a linear notebook view and a spatial canvas view, with changes synchronized bidirectionally, does not exist for computational notebooks.

### Zero-Platform Cell Types

The following cell types exist on zero current platforms as dedicated cell types:

- Approval/gate cells (human-in-the-loop pipeline control)
- Decision/router cells (conditional execution routing in notebooks)
- Agent cells (autonomous agents as DAG nodes)
- Tournament cells (multi-model competition with statistical testing)
- Branch/compare cells (fork/compare/replace workflow)
- Merge cells (combine branch results)
- Benchmark cells (statistical performance measurement)
- Drift detection cells (automatic output distribution monitoring)

### Academic Open Problems ContextKeeper Can Address

**Reproducibility crisis** (4% reproduction rate, Pimentel 2019). Root causes: hidden state from out-of-order execution, implicit dependencies, stale variables. ContextKeeper's typed contracts make dependencies explicit; reactive execution eliminates hidden state. Together, these address the two primary non-reproducibility causes. Measurable target: >90% reproduction rate for ContextKeeper notebooks (vs. 4% for Jupyter).

**Hidden state problem** (Chattopadhyay 2020, pain point #1). Users execute cells out of order, creating invisible dependencies on stale variables. Reactive execution enforces dependency-order execution, eliminating hidden state by construction. Combined with contracts, this provides provable correctness guarantees for the dependency graph.

**Version control inadequacy** (Chattopadhyay 2020, pain point #4). Jupyter's .ipynb format (JSON with embedded outputs) produces unreadable diffs and frequent merge conflicts. ContextKeeper's .py native format (Marimo-style) is Git-friendly, with cell-level version history providing finer granularity than file-level Git commits.

**Exploration vs. explanation tension** (Rule et al. 2018, "Exploration and Explanation in Computational Notebooks"). Notebooks serve two conflicting purposes: exploration (messy, iterative, non-linear) and explanation (clean, linear, narrative). Branch/compare addresses this by allowing exploration in branches while maintaining a clean main notebook. The exploratory branches preserve the messy history; the main notebook receives only the promoted winner.

### Technical Risks and Mitigations

**Pyodide single-threaded execution**. Risk: Python execution in the browser is limited to a single thread (WebAssembly limitation). Long-running cells block the UI. Mitigation: run Pyodide in a Web Worker (dedicated thread), with message passing to the main thread for UI updates. Comlink library simplifies Worker communication. For truly heavy computation, fall back to Jupyter Kernel Gateway on the server.

**Reactive analysis misses mutations** (Rex 2025). Risk: static AST analysis cannot detect in-place mutations, leading to stale downstream cells. Mitigation: typed contracts explicitly declare outputs, overriding AST-inferred dependencies. The contract system handles the cases where AST analysis fails. User education: encourage immutable patterns (return new DataFrames rather than mutating in place).

**10K+ node registry performance**. Risk: the current registry has 1,546 entries and will grow. Rendering, searching, and filtering 10K+ entries must remain interactive. Mitigation: SQLite FTS5 index for sub-millisecond full-text search. Virtual scrolling for the registry UI (render only visible entries). Lazy loading via dynamic `import()` -- cell type implementations load only when the cell type is used. Category hierarchy limits browsing depth to 2 levels.

**Branch execution doubles compute**. Risk: branch/compare requires executing the same data through multiple model configurations, doubling (or more) compute costs. Mitigation: incremental comparison -- only re-execute cells that differ between branches. Cache shared prefix (cells before the branch point). For server-side execution, parallelize branch execution across workers. For browser-side (Pyodide), execute branches sequentially but cache aggressively.

**Collaborative editing conflicts with reactive execution**. Risk: when multiple users edit cells simultaneously, reactive execution must handle conflicting dependency graph changes. Mitigation: Yjs CRDT ensures eventual consistency for cell content. The reactive execution engine runs per-user (each user sees their own execution state) with explicit "publish" actions to share results. Cell-level RBAC prevents conflicting edits to the same cell.

**Jupyter Kernel Gateway scalability**. Risk: each user session requires a kernel process (approximately 100-200MB RAM). The 2GB Linode server supports approximately 10-15 concurrent sessions. Mitigation: Pyodide for browser-side execution reduces server load. Kernel pooling (pre-warmed kernels) reduces startup latency. Idle kernel culling (kill kernels after 30 minutes of inactivity) reclaims resources. Vertical scaling to a larger Linode instance for growth.

---

## References

Benavoli, A., Corani, G., Demsar, J., & Zaffalon, M. (2017). Time for a Change: a Tutorial for Comparing Multiple Classifiers Through Bayesian Analysis. *JMLR*, 18(1), 1--36.

Chattopadhyay, S., Prasad, I., Henley, A.Z., Sarber, A., & Myers, B.A. (2020). What's Wrong with Computational Notebooks? Pain Points, Needs, and Design Opportunities. *CHI 2020*.

Chirigati, F., Rampin, R., Shasha, D., & Freire, J. (2016). ReproZip: Computational Reproducibility With Ease. *SIGMOD 2016*.

Demsar, J. (2006). Statistical Comparisons of Classifiers over Multiple Datasets. *JMLR*, 7, 1--30.

Diebold, F.X. & Mariano, R.S. (1995). Comparing Predictive Accuracy. *Journal of Business & Economic Statistics*, 13(3), 253--263.

Dietterich, T.G. (1998). Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms. *Neural Computation*, 10(7), 1895--1923.

Head, A., Mangon-Smith, F., Hearst, M.A., & Hartmann, B. (2019). Managing Messes in Computational Notebooks. *CHI 2019*.

Lau, S., Drosos, I., Marber, J.M., & Deline, R. (2020). The Design Space of Computational Notebooks. *VL/HCC 2020*.

Macke, S., Gong, H., Lee, D.J., Head, A., Xin, D., & Parameswaran, A. (2021). Fine-Grained Lineage for Safer Notebook Interactions. *VLDB*, 14(6), 1093--1106.

Murta, L., Braganholo, V., Chirigati, F., Koop, D., & Freire, J. (2015). noWorkflow: Capturing and Analyzing Provenance of Scripts. *IPAW 2014*.

Pimentel, J.F., Murta, L., Braganholo, V., & Freire, J. (2019). A Large-Scale Study About Quality and Reproducibility of Jupyter Notebooks. *MSR 2019*.

Pimentel, J.F., Murta, L., Braganholo, V., & Freire, J. (2021). Understanding and Improving the Quality and Reproducibility of Jupyter Notebooks. *Empirical Software Engineering*, 26(4).

Raschka, S. (2018). MLxtend: Providing Machine Learning and Data Science Utilities and Extensions to Python's Scientific Computing Stack. *JOSS*, 3(24), 638.

Rule, A., Tabard, A., & Hollan, J.D. (2018). Exploration and Explanation in Computational Notebooks. *CHI 2018*.

Samuel, S. & Konig-Ries, B. (2018). ProvBook: Provenance-Based Semantic Enrichment of Interactive Notebooks for Reproducibility. *ISWC 2018*.

Subotic, P., Bonetta, D., & Besta, M. (2022). Static Analysis of Data Science Code. *ECOOP 2022*.

Tanimoto, S.L. (1990). VIVA: A Visual Language for Image Processing. *Journal of Visual Languages and Computing*, 1(2), 127--139.

Wald, A. (1945). Sequential Tests of Statistical Hypotheses. *Annals of Mathematical Statistics*, 16(2), 117--186.

Weiser, M. (1981). Program Slicing. *ICSE 1981*.

Zheng, L., et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. *NeurIPS 2023*.

Zheng, X., et al. (2025). Rex: A Systematic Evaluation of Reactive Execution in Notebooks. Preprint.

Zheng, Z., et al. (2024). Kishu: Time-Traveling for Computational Notebooks. *VLDB 2024*.
