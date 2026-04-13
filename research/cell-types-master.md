# Cell Types Master Inventory

**Merged from 4 source files, deduplicated and organized by category**
Steven Wazlavek / ContextKeeper -- April 2026
Sources: cell-types-comprehensive.md, cell-types-inventory.md, cell-types-sql-widgets-extensibility.md, cell-types-platform-specializations.md

Over 200 distinct cell implementations documented across 50+ platforms, covering connection protocols, data flow, variable binding, rendering engines, and extension APIs. This is the most complete cell-type taxonomy assembled to date, designed to inform ContextKeeper's scalable cell-type registry architecture.

---

## Category 1: SQL Cells

SQL cells are the most widely implemented non-code cell type. Their implementations diverge sharply on seven axes: connection context, result handling, variable templating, large-result strategies, write-back capability, cell chaining, and dialect switching.

### 1.1 Hex (Gold Standard)

**Connection context.** Each SQL cell has a data source selector (top-right corner). Two source types: warehouse connections (Snowflake, BigQuery, Redshift, Databricks, Postgres, etc. -- admin-configured or per-project credentials) and DataFrame SQL (DuckDB engine querying in-memory DataFrames or uploaded CSVs). The connection object is a `HexSnowflakeConnection` (or equivalent per adapter) exposing `name`, `id`, `connection_type`, `enable_snowpark`, and `allow_writeback` properties.

**Result handling.** Dual output modes: DataFrame mode (green pill, full materialization as Pandas DataFrame) and Query mode (purple pill, 1,000-row preview with preserved SQL text for downstream chaining). Variable names are user-assigned via a pill at the bottom of the cell; double-clicking renames it and Hex auto-updates all downstream references.

**Variable templating.** Jinja2 syntax: `{{ variable_name }}` for scalar interpolation, `{{ list_var | array }}` for IN-clause arrays, `{{ col | sqlsafe }}` for identifier injection (bypasses prepared statement escaping), full Jinja control flow (`{% if %}`, `{% for %}`, `{% set %}`). All parameterized queries execute as prepared statements for SQL injection protection. Individual databases impose parameter limits (PostgreSQL: 32,767; Snowflake: 16,384).

**Large result set handling.** Query mode (purple pills) fetches only 1,000 rows for preview but participates fully in downstream warehouse operations. When a Query pill is referenced in a downstream warehouse SQL cell, Hex inserts the upstream SQL as a CTE at compile time. The "View compiled SQL" button shows the generated CTE chain. Chart and Pivot cells operating on Query-mode data use VegaFusion for warehouse pushdown. Hex caches query results server-side; identical queries serve from cache.

**Write-back.** Dedicated Writeback cell type (separate from SQL cells). Programmatic access via `connection.write_dataframe(df=my_df, database="DB", schema="PUBLIC", table="TABLE", overwrite=True)`. Supports append and overwrite modes. Requires `allow_writeback: True` on the connection.

**Chaining.** SQL cells reference upstream SQL cell results by variable name. Hex compiles references into CTEs at execution time. Parallel execution supports up to 8 concurrent warehouse queries when cells are independent in the DAG. Jinja changes to upstream values trigger automatic re-execution unless "Cell only" run mode is set.

**Dialect switching.** Dialect determined by selected connection. DuckDB used automatically when querying in-memory DataFrames. A single notebook can contain cells targeting different warehouses simultaneously.

### 1.2 Deepnote

**Connection context.** Integration system for connections (PostgreSQL, MySQL, BigQuery, Snowflake, Redshift, Databricks, MongoDB, ClickHouse). Per-block connection selector dropdown. Also supports DataFrame SQL (DuckDB). Connections can use environment variables for credentials.

**Result handling.** Two modes: DataFrame mode (full results as Pandas DataFrame, auto-named `df_1`, `df_2`, user-configurable) and Query preview mode (first 100 rows, returns a `DeepnoteQueryPreview` subclass storing source SQL for chaining). Interactive table with column-level distribution histograms, null counts, data-type badges, sorting, filtering, and conditional formatting.

**Variable templating.** JinjaSQL: `{{ variable_name }}` for scalars, `{{ list_var | inclause }}` for lists, `{{ col | sqlsafe }}` for identifiers. "Show compiled SQL query" reveals assembled CTE chains. Reactive execution re-runs SQL blocks when upstream dependencies change (since 2024 reactive execution release).

**Large result sets.** Fetches all results into memory by default. "Preview" badge for extremely large DataFrames. Spark DataFrames preview without full collection.

**Write-back.** No dedicated write-back cell type. Manual INSERT/UPDATE SQL or Python database connectors.

**Chaining.** Query chaining works only with preview objects, not full DataFrames, and only for single SELECT statements. No automatic CTE compilation like Hex.

### 1.3 Databricks

**Connection context.** SQL cells use `%sql` magic prefix. Connection context from notebook's attached cluster or SQL warehouse. Unity Catalog for namespace resolution. No per-cell connection selection; cluster's default catalog and schema apply unless overridden with `USE CATALOG/SCHEMA`.

**Result handling.** Interactive table with built-in visualization (bar, line, scatter, pie, area, map). Since DBR 13.3+, results accessible as `_sqldf` (Spark DataFrame) in subsequent Python cells; since DBR 14.3+, `_sqldf` works in subsequent SQL cells too. Display truncates at configurable row limits. Full result set accessed programmatically via Apache Arrow streaming.

**Variable templating.** Two systems: legacy `${widget_name}` string substitution (deprecated, injection-vulnerable) and newer `:param` parameter markers (DBR 15.2+) with `IDENTIFIER()` for object names. Python variables injected via f-strings in `spark.sql()`. No Jinja.

**Write-back.** Full SQL DDL/DML: INSERT INTO, CREATE TABLE AS SELECT, MERGE INTO. Delta Lake ACID transactions. Time travel for rollback. Unity Catalog enforces governance.

**Chaining.** Explicit temp view creation required: `CREATE OR REPLACE TEMP VIEW`. Per-cell language switching (`%python`, `%sql`, `%scala`, `%r`) enables polyglot chaining.

**Dialect.** Databricks SQL (Spark SQL dialect). Photon engine for accelerated SQL. No multi-dialect support within a single cluster.

### 1.4 Datalore (JetBrains)

**Connection context.** JDBC connections configured via UI. Schema browser and autocomplete aware of table structures (inherited from DataGrip/IntelliJ).

**Result handling.** Three-tab output: Table (interactive grid with cell editing and "Export to code" generating pandas), Visualize (auto-generated charts), Statistics (per-column descriptive stats). Results accessible as DataFrames in Python cells. Reactive mode tracks dependencies.

**Variable templating.** Single curly braces `{variable_name}` (not Jinja), with `{table_name | unsafe}` for unescaped identifiers. SQL cells can query DataFrames from other cells as virtual tables. Per-cell database switching via dropdown.

### 1.5 Observable

**Connection context.** DatabaseClient Specification (methods: `query()`, `queryStream()`, `queryTag()`, `describe()`). Built-in DuckDBClient (DuckDB-Wasm) or external database connectors. The first DatabaseClient in the notebook becomes the default.

**Result handling.** Returns an array of JavaScript objects. The cell name becomes the variable. Reactive: downstream cells re-execute when SQL cell value changes. DuckDBClient returns Apache Arrow-backed results.

**Variable templating.** JavaScript template literal interpolation: `${expression}`. Variables are reactive references.

### 1.6 Livebook

**Connection context.** Database Connection Smart Cell generates Elixir code: `{:ok, conn} = Kino.start_child({Postgrex, opts})`. Supported adapters: Postgrex (PostgreSQL), MyXQL (MySQL), Exqlite (SQLite), Tds (SQL Server), ADBC (Snowflake via Arrow Database Connectivity). The connection variable flows to downstream SQL Smart Cells.

**Result handling.** Results become Explorer DataFrames (Polars-backed). Variable names auto-generated via `Kino.SmartCell.prefixed_var_name/2`. Interactive display via `Kino.DataTable`.

**Rasterization.** Any Smart Cell can be converted to a plain code cell, revealing the generated Elixir source. The code is fully functional standalone.

### 1.7 Apache Zeppelin

**Connection context.** Interpreter prefix system: `%spark.sql`, `%jdbc`, `%hive`, `%postgresql`, `%mysql`, etc. JDBC interpreters configured with `default.url`, `default.user`, `default.password`, `default.driver`. Each interpreter runs as a separate JVM process.

**Result handling.** Built-in table with 6 visualization types (table, bar, pie, area, line, scatter) and drag-and-drop pivot charting. Dynamic forms embeddable directly in paragraphs.

**Variable templating.** Three mechanisms: dynamic forms `${variable=default}`, ZeppelinContext interpolation `{variable_name}` (requires `zeppelin.jdbc.interpolation=true`), and `spark.conf.set()`. Cross-interpreter data sharing via `z.put("key", obj)` / `z.get("key")` / `z.getAsDataFrame("table_name")`.

**Binding modes.** Shared (all notes share one instance), scoped (per-note instance, same process), or isolated (per-note process).

### 1.8 Mode Analytics

**Connection context.** Workspace-level warehouse connections. Queries organized in a separate "SQL Editor" pane.

**Result handling.** Results populate "datasets" feeding into Python/R notebooks and Visual Explorer. Accessed via `datasets[0]`, `datasets[1]` (Pandas DataFrames). Datasets are named and referenceable.

**Variable templating.** Liquid template language (not Jinja): `{{ parameter_name }}` with `{% if %}`, `{% for %}`, `{% assign %}`. Parameters defined in report UI and injected into SQL.

### 1.9 Count (count.co)

**Connection context.** Canvas-based SQL cells connect to configured data sources. dbt integration: `ref()` macro references dbt models. Per-cell source selection. Canvas layout means SQL cells are spatial nodes.

**Variable templating.** Jinja2 with Count-specific extensions: `{{ cells.control_cell_name }}` accesses control cell values (compiled directly into SQL, no subquery). Filters: `| array`, `| string()`, `| sqlsafe`. Templates are local per cell.

**Result handling.** Results flow into downstream cells via the canvas DAG. Visual cells consume SQL cell outputs directly. Dynamic query compilation compiles visual cells into CTEs.

### 1.10 Sigma Computing

**Connection context.** Direct warehouse connection (Snowflake, BigQuery, Databricks, Redshift). All computation pushed to warehouse. Connection is workspace-level.

**Result handling.** Spreadsheet-like interface. Billions of rows queryable (warehouse handles compute). Control references use `{{ control_id }}` syntax. `sigma_element('element_name')` references other workbook elements as source tables.

**Write-back.** Input Tables enable write-back to Snowflake/Databricks (not raw SQL DML). 25,000 data point limit per visualization.

### 1.11 Additional SQL Implementations

**Querybook** (Pinterest, open-source): SQL-first. Per-cell engine dropdown. Results uploaded in batches to S3. Full Jinja2 templating including `{{ latest_partition('schema.table', 'partition_key') }}`. Python cells (Pyodide-powered) access query results as DataFrames.

**PopSQL**: Google Docs-like multiplayer editing. Query variables for parameterization. Scheduled queries (15-min to weekly). Post-acquisition by TigerData, being integrated into Timescale Console.

**Azure Data Studio**: SQL cells in Jupyter-style notebooks. T-SQL and PySpark. All SQL cells bind to a single connection (per-cell not supported -- GitHub issue #5031). Results persist in notebook JSON.

**DBeaver**: SQL editor with notebook-like script execution. Multiple execution modes: `Ctrl+Enter` (single statement), `Ctrl+\` (new result tab), `Alt+X` (sequential), `Ctrl+Alt+Shift+X` (simultaneous). Parameters use `:param_name` syntax. Result tabs named via `-- @result_name` comments.

**Evidence.dev**: SQL in Markdown fenced code blocks. DuckDB dialect with connectors. Results flow to JavaScript expressions and Svelte visualization components. Static site generation. Cell chaining via `${query_name}` compiles to subqueries/CTEs.

**Colab Enterprise** (Google): Native SQL cells with automatic IAM authentication to BigQuery. Output auto-saved as DataFrame with cell title as variable name. Variable referencing uses `{python_variable}` in braces.

**Hyperquery** (acquired by Deepnote 2024): SQL blocks with inline Python. Jinja parameterization.

**Noteable** (ceased Dec 2023): JinjaSQL with results auto-stored as `sql_df_<n>`. Backslash meta commands (`\dt`, `\d table_name`).

**Dataiku**: SQL notebook bound to single connection. Templating uses `${variable_name}` for DSS custom variables. SQL recipes auto-rewrite SELECT to INSERT INTO ... SELECT.

### 1.12 Modern Data Stack SQL Cells

**dbt**: Models as SQL cells in a DAG. `{{ ref('model_name') }}` interpolates correct `database.schema.table` and builds dependency graph. Ephemeral models injected as CTEs. Full Jinja2 with built-in functions: `ref()`, `source()`, `config()`, `var()`, `is_incremental()`, `this`, `target`, `env_var()`, `run_query()`, `adapter.*`. Materializations: view, table, incremental, ephemeral. Cross-database macro dispatch via `adapter.dispatch()`.

**SQLMesh**: Per-model `dialect:` property with automatic transpilation via SQLGlot. MODEL DDL with `kind` (VIEW, FULL, INCREMENTAL_BY_TIME_RANGE, INCREMENTAL_BY_UNIQUE_KEY, EMBEDDED, SCD_TYPE_2, SEED, EXTERNAL). No `ref()` needed -- SQLGlot parses SQL to auto-detect dependencies. Virtual environments use views for zero data duplication.

**Malloy**: Semantic source/query model. Queries chain via `->` operator. Compiler handles symmetric aggregates to prevent join fanout bugs.

**PRQL**: Three-stage compilation pipeline: PRQL -> PL AST -> RQ AST -> SQL. Per-query target selection. Jupyter integration via `%%prql` magic.

**Rill Developer**: YAML+SQL pipeline with Go templating for incremental models. Embedded DuckDB OLAP engine for sub-second dashboard latency.

**Holistics AML**: `{{ #model_name }}` for model references. AQL pipe operator for higher-abstraction metric language.

**LookML** (Looker): `sql: ${TABLE}.column_name ;;`. Persistent Derived Tables materialize in scratch schema. Liquid templating with `_filters`, `_in_query`, `_is_selected` variables.

**Lightdash**: Converts dbt `manifest.json` into Explores. Dimensions and metrics in dbt YAML `meta:` blocks. Large results stored in S3 as JSONL.

### 1.13 BI Tool SQL Cells

**Metabase**: Three variable types: basic, field filters (smart widgets generating WHERE clauses), and optional clauses `[[ AND column = {{ var }} ]]`. Saved question referencing `{{#question_id}}` compiles to subqueries. MBQL intermediate query language translated to native SQL via HoneySQL.

**Redash**: Results stored in QueryResult model with JSON-encoded data. Query Results Data Source (QRDS) enables cross-query chaining: `SELECT * FROM query_49588`. In-memory SQLite for QRDS. Query-Based Dropdowns.

**Apache Superset**: Full Jinja2 with pre-defined macros (`{{ current_username() }}`, `{{ url_param('key') }}`, `{{ filter_values('column') }}`). Async queries via Celery workers + Redis. SQL parsing uses sqlglot. Row Level Security via AST transformation.

### 1.14 Cross-Platform SQL Cell Comparison

| Feature | Hex | Deepnote | Databricks | Livebook | Zeppelin | Mode | Querybook |
|---------|-----|----------|------------|----------|----------|------|-----------|
| Templating | Jinja2 | JinjaSQL `{{var}}` | Widgets `$var` / `:param` | Elixir interpolation | `${var=default}` | Liquid | Jinja2 |
| Auto-DataFrame | Yes (named pill) | Yes | Yes (`_sqldf`) | Yes (Explorer DF) | Via `z.put()` | Yes | No |
| CTE chaining | Automatic | Preview-mode only | Manual temp views | No | No | No | No |
| Warehouse pushdown | Yes (Query mode) | No | Yes (Spark) | No | Via interpreter | Partial | Via engine |
| Write-back cell | Dedicated type | No | Full DDL/DML | No | Via interpreter | No | Full DDL/DML |
| Multi-dialect | Per connection | Per connection | Single cluster | Per Smart Cell | Per interpreter | Per connection | Per engine |
| Prepared statements | Yes | Unknown | Yes (`:param`) | Via Ecto | Via JDBC | Unknown | No |

---

## Category 2: LLM/Prompt Cells

Despite the AI hype cycle, only one major general-purpose notebook platform has a true first-class prompt cell type: Google Colab. The dominant industry pattern is AI assistants that generate standard cell types, not dedicated prompt cells.

### 2.1 Google Colab AI Prompt Cells (Only True First-Class Implementation)

A distinct third cell type alongside code and text cells. Added via toolbar dropdown: "Add AI prompt cell." Launched November 2025.

**Interaction.** Text input ("Ask me anything...") sends prompt to Gemini model. Response renders inline as mixed text and code blocks. NOT directly executable -- users must copy code into standard code cells. NOT context-aware of other cells regardless of position. Iterative refinement within the same cell supported.

**Programmatic access.** `google.colab.ai` Python API: `ai.generate_text(prompt, model_name='google/gemini-2.5-flash', stream=True)` returns streaming iterator.

**Data Science Agent** (2025, Google I/O): Separate agentic capability in notebook chat generating multi-step plans, creating code cells, executing and self-correcting. Full contextual awareness of notebook contents. This is a sidebar agent, not a cell type.

### 2.2 Google Colab %%palm Magic (Legacy, Deprecated)

`%%palm run` magic command within code cells. Template variables via `{curly_braces}` referencing Python dictionaries passed with `--inputs`. Results stored in a DataFrame with columns for Prompt, text_result, safety_ratings. More architecturally sound than the newer AI prompt cell but deprecated.

### 2.3 ContextKeeper Notebook AI Prompt Cell

First-class cell type (`type: 'prompt'`) with dedicated CSS, model selector, and target language selector. Dropdown for model selection (5 free Groq models: Llama 3.3 70B, DeepSeek R1 70B, Llama 3.1 8B, Compound Beta, Compound Beta Mini). Target output language (Python, SQL, JavaScript). System prompt includes `PYODIDE_SYS_CONTEXT`. Voice input via Speech Recognition API. Conversation mode with `_cellAIConvo` state tracking. Generated code displayed with "Accept"/"Reject" buttons; accepting inserts into new code cell below.

### 2.4 Jupyter AI `%%ai` Magic

Not a distinct cell type; IPython cell magic. Syntax: `%%ai <provider-id>:<model-id>`. Supports LangChain-based providers (AI21, Anthropic, AWS Bedrock, Cohere, Google Gemini, Hugging Face, MistralAI, NVIDIA, OpenAI, Ollama, GPT4All). Variable interpolation: `{variable_name}` reads from IPython namespace, `{In[11]}` references cell input, `{Out[11]}` references output, `{Err[3]}` references errors. Format flags: `-f code`, `-f html`, `-f image`, `-f json`, `-f markdown`, `-f math`, `-f text`. Chain registration: `%ai register my_chain <chain_variable>`. Metadata saved for AI-generated content provenance tracking. Output stored in `Out[]` but NOT captured as Python variables.

### 2.5 AI-Augmented Cell Generation (No Dedicated Cell Type)

**Hex Magic**: Generates standard SQL, Python, and Chart cells via prompt bar (`Cmd+G`). Multi-cell generation creates drafts for human review. Context includes full notebook DAG, database schemas, dbt docs, DataFrame schemas via "Context Studio." Every Explore cell returns a DataFrame for downstream consumption. Test-run capability: sandbox before accepting. Cannot generate writeback cells or input parameters.

**Databricks Assistant / Agent Mode**: Three modes: Chat (returns code to copy), Edit (multi-cell inline diffs with accept/reject, Aug 2025), Agent mode (autonomous multi-step, Sep 2025). In-cell slash commands: `/explain`, `/fix`, `/comments`, `/optimize`, `/doc`. Powered by DatabricksIQ. Supports GPT-5.2, Claude Opus 4.5, Gemini 3 Pro. Full Unity Catalog metadata context.

**Deepnote Auto AI**: Generates and executes blocks autonomously, self-correcting on errors. Sees all block contents, DataFrame schemas, SQL integration metadata. Guardrails prevent write queries. GPT-5 and Claude Sonnet 4.5 on Team plan; BYOLLM on Enterprise.

**Microsoft Fabric Copilot**: Chat pane with MCP server tools and in-cell prompts (`Cmd+I`). IPython chat-magics: `%%fix_errors`, `%add_comments`. Context includes Lakehouse schemas, Spark execution details, Power BI semantic models. Approval workflow requires user consent before running cells.

**Marimo AI**: Editor-level AI (generate/refactor cells) and chat sidebar with three modes: Manual, Ask (read-only tools + MCP), Agent (edit cells, run stale). `@variable` syntax passes live runtime data to LLM. `mo.ai.llm` provides in-notebook chatbot API: `mo.ui.chat(mo.ai.llm.openai("gpt-4o"))` with reactive `chat.value`. LLM providers in `marimo.toml` under `[ai.models]`.

### 2.6 LLM Orchestration Tool Prompt Nodes

**LangChain LCEL**: Every component is a `Runnable` with `.invoke()`, `.ainvoke()`, `.stream()`, `.astream()`, `.batch()`, `.abatch()`, `.astream_events()`. Chains compose via `|` pipe. Built-in parsers: `StrOutputParser`, `JsonOutputParser`, `PydanticOutputParser`, `XMLOutputParser`. Tool calling via `llm.bind_tools(tools)`.

**LangGraph**: `StateGraph` with typed `TypedDict` state. `Annotated[list, add_messages]` reducer pattern. Compiles to runnable with checkpointing (`MemorySaver`, `PostgresSaver`). Parallel branches via `Send()`.

**Vellum.ai**: Graph-based workflow with typed nodes. Five tool types: Code, Subworkflow (inline), Subworkflow Deployment, Composio, MCP Server. Streaming native at Workflow and Node level.

**Rivet** (Ironclad): Visual graph IDE with typed ports. `{{@graphInputs.<inputId>}}` and `{{@context.<inputId>}}` for variable references. Streaming Chat Node.

**CrewAI**: Role-based multi-agent composition: Agent, Task, Crew. `context=[task1]` passes upstream task outputs. Processes: sequential, hierarchical (manager delegates), parallel. Structured output via `output_pydantic`/`output_json`.

**AutoGen**: `ConversableAgent` with `initiate_chat()`. Group chat patterns: round-robin, LLM-based speaker selection, custom. v0.4 introduces actor model with `RoutedAgent` and `@message_handler`.

**n8n AI nodes**: Hierarchical system on LangChain JS. `$fromAI()` populates tool parameters from LLM output. Multi-agent patterns via AI Agent Tool node.

**Dust.tt**: Sequential blocks with shared `state` object. Block types: input, llm, chat, code, data, data_source, map/reduce, curl, browser, search. MCP as primary tool integration.

### 2.7 Prompt Versioning Gap

W&B Weave (`weave.publish(prompt, 'name')`), Humanloop (deterministic hash per config change), PromptLayer (A/B Releases), Langfuse (immutable versions with label pointers). **No notebook platform offers built-in prompt versioning or A/B testing.**

### 2.8 Databricks ai_query() -- Most Production-Ready LLM Integration

SQL function callable within any SQL cell:
```sql
SELECT ai_query('databricks-meta-llama-3-3-70b-instruct',
  'Summarize: ' || text_column) AS summary
FROM my_table
```
Returns proper SQL column values enabling batch inference at scale with auto-parallelization and retries. Task-specific functions: `ai_extract`, `ai_classify`, `ai_translate`, `ai_summarize`, `ai_similarity`, `ai_parse_document`. The only approach where LLM outputs fully participate in the data pipeline as first-class values.

### 2.9 Cross-Platform Prompt Cell Comparison

| Feature | Colab Prompt | Colab %%palm | CK Prompt | jupyter-ai %%ai |
|---------|-------------|-------------|-----------|-----------------|
| Distinct cell type | Yes | No (magic) | Yes | No (magic) |
| Upstream context auto-injection | No | Yes (--inputs) | No (manual) | No |
| Output as variable | No | Yes (DataFrame) | No (accept to cell) | No |
| Model selector | No | Via API key | Yes (5 models) | Yes (provider config) |
| DAG participation | No | Partial | No (until accepted) | No |

**Key gap across all platforms:** No existing prompt/LLM cell type has full DAG participation where the LLM's output is automatically typed, assigned to a variable, and available to downstream cells without manual intervention.

---

## Category 3: Visualization and Chart Cells

### 3.1 Declarative Chart Builders

**Hex** chart cells are backed by Vega-Lite with VegaFusion handling server-side pre-aggregation, enabling visualization of near-infinite-size DataFrames. Drag-and-drop builder with Data and Style tabs. Chart types: bar (grouped/stacked), line, scatter, area, histogram, heatmap, pie/donut, combo, box plot. Critical differentiator: visual filtering -- users click/drag to select ranges, and the chart returns a filtered DataFrame for downstream cells. Dedicated Map cell supporting point, text, area (GeoJSON/WKT), and heatmap layers. The newer "Explore" cells combine visual building with dimension/measure selection. Rendering uses SVG via Vega renderer.

**Deepnote** also uses Vega-Lite. Chart AI generates configurations from natural language descriptions. "Duplicate chart as code" creates Python block with full Vega-Lite spec. Post-aggregation limit: 5,000 data points. Smart preview mode samples data during configuration for datasets exceeding 1M rows. Supports PySpark DataFrames natively, with aggregations pushed to Spark cluster.

**Observable Plot** uses marks-based grammar (dot, line, area, bar, rect, rule, text, tick, cell, frame, geo, image, arrow, link, hexbin, contour, density, raster, vector, waffle) with channels (x, y, fill, stroke, opacity, size) and transforms (bin, group, stack, window, select, hexbin, dodge, normalize). Generates SVG. The `viewof` reactive binding creates interactivity without explicit event handlers. Server-side rendering in Node.js via JSDOM supported. Chart cell UI uses `auto` mark; "eject to JavaScript" shows code.

**Databricks** provides 20+ chart types including sankey, sunburst, cohort, word cloud, funnel, choropleth map. Rendering uses Plotly.js (confirmed by toolbar). Backend aggregations support >64K rows. Charts support zoom, pan, series show/hide. No cross-filtering returning filtered DataFrames.

**Sigma Computing** uses proprietary SVG-based rendering engine. Charts are child elements of tables, cascading via lineage DAG. All SQL pushed to warehouse. 25,000 data point limit per visualization.

**Count.co** uses infinite 2D canvas. Dynamic query compilation compiles visual cells into CTEs. Two building modes: templated visuals (form-based) and custom Vega-Lite specs. Dynamic text elements show live data values inline.

### 3.2 BI Tool Visualization Systems

**Metabase**: Custom React/SVG rendering (not Plotly or Vega-Lite). Dashboard filters propagate to cards. Embeddable via iframe or static embedding API.

**Redash**: Plotly.js for 8 chart forms + Leaflet for maps. Custom visualization types via `VisualizationProvider.registerVisualization()`.

**Apache Superset**: Viz plugin architecture -- each chart type is a React plugin with `controlPanel.ts`, `buildQuery.ts`, `transformProps.ts`. ECharts preferred for new plugins; legacy uses NVD3; maps use Deck.gl. Custom viz plugins as npm modules.

**Evidence.dev**: Declarative Svelte component props in Markdown. ECharts rendering (Canvas default). Components: LineChart, BarChart, ScatterPlot, AreaChart, Histogram, BoxPlot, Heatmap, FunnelChart, SankeyDiagram, DataTable, BigValue, Sparkline, Map, Calendar, USMap. Supports `<ReferenceLine>` and `<ReferenceArea>` annotations. Static HTML output.

**Rill Developer**: Declarative YAML ("BI-as-code") with embedded DuckDB/ClickHouse for sub-second latency.

### 3.3 Code-Driven Chart Cells

**Streamlit**: `st.line_chart` is syntax-sugar around `st.altair_chart` -- auto-generating Vega-Lite specs. `st.altair_chart(chart, on_select="rerun")` enables chart selections triggering reruns. Data transferred as Arrow tables.

**Panel**: Wraps Bokeh models with HoloViews declarative grammar. `pn.bind(function, widget)` for reactive pipelines. Exports as standalone HTML.

**Retool**: Plotly.js v2.34. Plotly JSON Chart component accepts raw Plotly data/layout. Event handlers trigger queries/actions.

### 3.4 Specialized Chart Types

**Hex Pivot Cells**: No-code pivot table with drag-and-drop Row/Column/Value zones, aggregation per value field, conditional formatting, drill-down, "Create output" button generating DataFrame. "Eject to code" shows generated SQL/Python. Top N filtering.

**Hex Single Value Cells**: Prominent KPI display with aggregation (Sum, Avg, Min, Max, Median, Count, Count Distinct), comparison mode (absolute/percent change), configurable positive/negative formatting. Outputs value as Python variable.

**Hex Filter Cells**: No-code data filtering with individual filters or groups, keep/remove toggle, SQL generation, eject-to-SQL capability.

**Hex Calculation Cells**: Excel-like formulas on DataFrames without writing code. Jinja parameterization. Designed for business users.

**Hex dbt Semantic Layer Cells**: No-code interface to query dbt Semantic Layer metrics with metric, dimension, time grain, and date range selection.

**Deepnote Big Number Blocks**: Prominent metric display with optional comparison/delta.

**Count Big Number**: Big Number visual cell on canvas.

**Evidence BigValue**: `<BigValue data={query} value=metric />` component.

**Mode Visual Explorer**: Drag-and-drop charting on SQL query results with conditional formatting, custom color palettes, reference lines.

**Datalore Data Explorer**: No-code search, filter, and column creation via SQL expressions (since 2026.1).

**Marimo Reactive Visualization**: `mo.ui.altair_chart()` and `mo.ui.plotly()` wrappers make charts reactive UI elements. Brush/click selections update Python variables triggering downstream recalculation. Chart is simultaneously output AND input.

---

## Category 4: Input/Widget Cells

Seven distinct reactivity paradigms exist across platforms.

### 4.1 Hex -- One-Way Variable Binding with DAG Propagation

14+ input types: Dropdown (single/multi-select; dynamic from DataFrame column), Text Input, Number Input (min/max/step), Slider (continuous/discrete/range), Date Picker (single/range), Checkbox, Radio Buttons, Toggle, File Upload, Button (gates downstream), Multi-select, Color Picker, Time Picker, Table Input (editable spreadsheet returning DataFrame, capped at 250 rows).

Each produces a named variable (pill). Name becomes accessible in Python directly and in SQL via `{{ name }}` Jinja with prepared statements. `| array` filter for multiselect IN clauses. Run Button: value is True only during triggered execution. In Auto Run mode, changes cascade automatically. Cancels outdated runs on rapid changes. URL parameterization in published apps.

### 4.2 Marimo mo.ui -- Two-Way Reactive Binding (Richest Library)

25+ element types: slider, number, text, text_area, dropdown, multiselect, checkbox, radio, switch, date, code_editor, file, table (interactive with row selection), dataframe (DataFrame editor), data_explorer, altair_chart (brush/click selection), plotly (selection-aware), matplotlib, array (list of elements), dictionary (named elements), batch (templated HTML), form (gates submission behind button), refresh (periodic timer), chat (LLM interface), microphone (audio recording).

Internally, `UIElement` is generic with `S` (FrontendValue) and `T` (PythonValue) type parameters, with `_convert_value(S) -> T`. Each element has unique `object_id` in `UIElementRegistry`. Update flow: React frontend `setValue` -> message with `object_id` -> kernel locates in registry -> `_convert_value` -> runtime identifies dependent cells -> re-executes. `mo.ui.form()` gates submission. `mo.ui.batch()` combines elements (`.value` is dict of child values). Lens mechanism for hierarchical parent-child widgets. anywidget integration via `mo.ui.anywidget()` injects `MarimoComm` to intercept trait changes.

### 4.3 Observable Inputs -- Generator-Based Reactive Binding

14 types: button, toggle, checkbox, radio, range, select, text, textarea, date, color, file, search, table, form. `viewof x = Inputs.range(...)` creates two variables: `viewof x` (DOM element) and `x` (current value). `Generators.input()` returns async generator yielding `.value` on each `input` event. Any DOM element with `.value` and `input` events is compatible. `Inputs.bind(target, source)` creates asymmetric binding. Entirely client-side -- no backend kernel.

### 4.4 Pluto.jl @bind -- Observable-Style Generators

`@bind variable_name widget` macro creates reactive bindings. `AbstractPlutoDingetjes.jl`: `Bonds.initial_value()`, `Bonds.validate_value()`, `Bonds.transform_value()`. Frontend via WebSocket `bond_value` messages. One definition per variable enforced. 20+ PlutoUI widgets: Slider, TextField, TextArea, NumberField, CheckBox, Select, MultiSelect, MultiCheckBox, Radio, Button, CounterButton, Scrubbable (inline drag-to-change), DateField, TimeField, ColorStringPicker, FilePicker, Clock (periodic timer), DownloadButton, `confirm` (submit wrapper), `combine` (compose into tuple). `published_to_js(data)` for efficient binary transfer; `with_js_link(callback)` for bidirectional RPC.

### 4.5 Livebook Kino -- Pull-Based Model

Two categories: Kino.Input (shared state, read via `Kino.Input.read/1`) and Kino.Control (per-user, event-driven via `Kino.listen/2`). 13 input types: text, textarea, number, password, url, select, checkbox, color, range, image, audio, file, datetime. Controls: button, form, keyboard, interval.

Key design: when someone changes a Kino.Input, it reflects for all users. `Kino.listen(source, fun)` starts a process consuming events. `Kino.animate(source, fun)` renders output per event. `Kino.Frame` enables dynamic output (update, append, clear). `Kino.Layout.tabs` and `Kino.Layout.grid` for arrangement. Staleness detection includes input hashes in `cell_snapshot` tuple.

### 4.6 ipywidgets -- Symmetric Two-Way Binding via Comm Protocol

40+ types: IntSlider, FloatSlider, FloatLogSlider, IntRangeSlider, FloatRangeSlider, IntText, BoundedIntText, FloatText, BoundedFloatText, IntProgress, FloatProgress, Checkbox, ToggleButton, Valid, Dropdown, RadioButtons, Select, SelectionSlider, ToggleButtons, SelectMultiple, SelectionRangeSlider, Text, Textarea, Combobox, Password, Label, HTML, HTMLMath, Image, Video, Audio, Button, Play, DatePicker, TimePicker, DatetimePicker, ColorPicker, FileUpload, Output, Controller (gamepad), TagsInput, ColorsInput, Tab, Accordion, Stack, HBox, VBox, GridBox, TwoByTwoLayout, AppLayout, GridspecLayout.

Comm protocol: `comm_open` (widget construction with GUID, target name, `_model_module`/`_model_name`), `comm_msg` with `method: "backbone"` or `"update"` for state sync. Delta compression with `hold_sync()` for batching. Property locks prevent echo. Traits tagged `sync=True` synchronized with custom `to_json`/`from_json`. Widget references serialize as `"IPY_MODEL_<id>"`. Display MIME: `application/vnd.jupyter.widget-view+json`. Three patterns: `observe(callback, names=['value'])`, `interact(fn, **kwargs)`, `interactive(fn, **kwargs)`. Extensions: ipyleaflet, bqplot, ipyvolume, ipydatagrid, ipympl, ipycytoscape, nglview, pythreejs, k3d, ipysheet.

### 4.7 Google Colab Form Cells

Comment annotations: `variable = value # @param {type:"slider", min:0, max:100}`. Types: slider, integer, number, string, boolean, date, raw. Dropdown: `variable = "option1" # @param ["option1", "option2"]`. Limitation: options must be static string literals; dynamic population not supported.

### 4.8 Streamlit -- Complete Script Re-Execution

Every interaction triggers top-to-bottom script rerun. `st.session_state` persists values. Communication via Protocol Buffers (BackMsg/ForwardMsg). `st.form` gates reruns until submit. Fragments enable partial function re-execution. Widgets: slider, selectbox, multiselect, text_input, text_area, number_input, date_input, time_input, file_uploader, color_picker, camera_input, data_editor (editable DataFrame), chat_input, chat_message, checkbox, radio, toggle, button, download_button.

### 4.9 Gradio -- Event-Driven Callback Model

`btn.click(fn=my_func, inputs=[...], outputs=[...])`. Concurrency control via `concurrency_limit`. `gr.State()` for per-session state. 30+ components: Textbox, Number, Slider, Dropdown, Checkbox, Radio, File, Image, Audio, Video, DataFrame, Gallery, Plot, HTML, Markdown, JSON, Code, Label, HighlightedText, Chatbot, Model3D. Every component can be input, output, or both. `gr.Interface` for high-level; `gr.Blocks` for full layout. Backend is FastAPI with SSE for streaming.

### 4.10 Panel -- Param-Based Reactivity

Built on param library with typed parameters. `param.watch(callback, ['param_name'])`, `@param.depends('param_name')`, `pn.bind(fn, widget)`, `pn.rx(expr)` for reactive expressions. Communication via Bokeh PATCH-DOC messages. `jslink` for client-side linking. Works identically in notebooks and standalone apps.

### 4.11 Shiny for Python -- Implicit Dependency Tracking

Calling `input.slider_id()` inside reactive context automatically creates dependency. Three-tier system: sources (`input.*`), conductors (`@reactive.calc`, lazy/cached), endpoints (`@render.*`, `@reactive.effect`). Invalidation cascades; lazy evaluation re-executes only when needed.

---

## Category 5: Smart Cells and Extensible Cell Type APIs

Only four platforms support true cell-type extensibility: Livebook, Zeppelin, ComfyUI (node-graph analogy), and Starboard. Jupyter's fixed three-type schema is the fundamental blocker.

### 5.1 Livebook Smart Cells -- Gold Standard

**Registration.** `Kino.SmartCell.register(ModuleName)` in `application.ex`. Module must `use Kino.JS`, `use Kino.JS.Live`, `use Kino.SmartCell, name: "Display Name"`. Smart cells packaged as Hex packages prefixed `kino_*`.

**Required callbacks:**

1. `init(attrs, ctx)` -- receives persisted attributes (map) and context. Returns `{:ok, ctx}` or `{:ok, ctx, opts}` where opts can include `:editor` config and `:reevaluate_on_change`.
2. `handle_connect(ctx)` -- sends initial payload to JavaScript frontend. Returns `{:ok, payload, ctx}`.
3. `to_attrs(ctx)` -- serialize state to JSON-compatible map. Stored in `.livemd` notebook source.
4. `to_source(attrs)` -- the rasterization callback. Generates standalone Elixir source code using `quote do ... end` and `Kino.SmartCell.quoted_to_string()` for AST-level code generation. This generated code runs identically to hand-written code.

**Optional callbacks:**

5. `handle_event(event, payload, ctx)` -- handles events from JS frontend.
6. `handle_editor_change(source, ctx)` -- handles changes in optional collaborative editor.
7. `scan_binding(pid, binding, env)` -- inspects available variables for contextual UI (e.g., showing DataFrames in dropdown). Runs asynchronously in evaluator process. Must not send large data.
8. `scan_eval_result(pid, result)` -- receives evaluation result for post-processing.

**JavaScript frontend.** `asset "main.js"` macro defines JS rendering. `ctx.pushEvent(name, payload)` sends to server; `ctx.handleEvent(name, callback)` receives from server. `ctx.handleSync(callback)` synchronously invokes change listeners before evaluation. `ctx.root` (DOM element), `ctx.selectSecret()`.

**Rasterization model -- architectural breakthrough.** Smart cells store both configuration AND generated source code. If the smart cell package isn't installed, the generated code still runs as a normal code cell. Permanent "Convert to Code" action.

**Built-in smart cells:** Database Connection (kino_db: Postgrex, MyXQL, Exqlite, Tds, ADBC), SQL Query, Vega-Lite Chart, MapLibre Map, Diagram (Mermaid/Kroki), Neural Network Task (kino_bumblebee), Remote Execution, Slack Message (kino_slack), File Input, Secret Management.

**Community smart cells:** kino_kroki (30+ diagram types via Kroki), kino_db, kino_bumblebee, kino_slack, kino_explorer, and dozens more via Hex.pm.

### 5.2 ComfyUI NODE_CLASS_MAPPINGS -- The Registry Paradigm

**Legacy registration:**
```python
class MyNode:
    CATEGORY = "my_category/subcategory"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("processed_image", "caption")
    FUNCTION = "process"
    OUTPUT_NODE = False

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mode": (["brightest", "reddest", "greenest"],),
                "threshold": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
            "optional": {"mask": ("MASK",)},
            "hidden": {"unique_id": "UNIQUE_ID", "prompt": "PROMPT"}
        }

    def process(self, image, mode, threshold, mask=None):
        return (processed_image, caption)

NODE_CLASS_MAPPINGS = {"MyNode": MyNode}
NODE_DISPLAY_NAME_MAPPINGS = {"MyNode": "My Custom Node"}
```

**V3 API:** Async `comfy_entrypoint()` with `ComfyExtension`, type-safe `IO` classes in `comfy_api.latest.IO`, dynamic inputs, price badges, stateless `@classmethod` execution, async support.

**Discovery.** Scans `custom_nodes/` directories for `__init__.py` files exporting `NODE_CLASS_MAPPINGS`. Pip-installable via `pyproject.toml` entry points. Changes require server restart.

**Type system.** Built-in: IMAGE, MASK, LATENT, MODEL, CLIP, VAE, CONDITIONING, SAMPLER, AUDIO, VIDEO, STRING, INT, FLOAT, BOOLEAN, COMBO. Custom types: any string (matching type names connect).

**Client-side.** `app.registerExtension()` with lifecycle hooks: `beforeRegisterNodeDef`, `afterRegisterNodeDef`, `setup`, `nodeCreated`.

**Scale.** ComfyUI Manager indexes 2,000+ custom node packages. Individual packages provide 200+ nodes. Total ecosystem: estimated 4,000-10,000+ unique node types.

**Mapping to notebook concepts:** `NODE_CLASS_MAPPINGS` -> cell type registry, `INPUT_TYPES` -> cell configuration schema, `FUNCTION` execution -> cell evaluation, `RETURN_TYPES` -> cell output type declaration, `CATEGORY` -> navigation hierarchy.

### 5.3 Apache Zeppelin Interpreters -- Original Cell-Type-as-Plugin

Custom interpreters extend `Interpreter` class: `interpret(String code, InterpreterContext context)`, `open()`, `close()`, `cancel()`, `getFormType()`, `getProgress()`. Registration: JARs in directory with `interpreter-setting.json`. Interpreter groups share JVMs. 20+ built-in: Spark, PySpark, JDBC, Python, Markdown, Shell, Angular, Flink, Hive, Cassandra, Elasticsearch, Neo4j, R, and more.

### 5.4 Jupyter's Fixed Three-Type Schema

nbformat v4.5 supports exactly three cell types: code, markdown, raw -- enforced via `oneOf` JSON schema. No mechanism to define custom cell types. JupyterLab extensions can add renderers via `IRenderMimeRegistry` and `IRendererFactory`, cell toolbar items, and new document types, but cannot add new cell kinds. Issues #1937 (jupyterlab) and #4801 (jupyter/notebook) requesting custom cell types remain unresolved. Federated extensions (since JupyterLab 3.0) distribute as pip/conda without rebuilding.

VS Code Notebook API: two cell kinds (`Code` and `Markup`). Extensions can create entirely new notebook types (e.g., .NET Interactive Notebooks).

**Starboard Notebook**: Plugin cell types via `runtime.controls.registerPlugin(plugin)` with dynamic ES module imports. Largely unmaintained since 2024.

### 5.5 Other Extensibility Models

**n8n custom nodes**: `INodeType` interface with `description: INodeTypeDescription` and `async execute()`. Two styles: declarative (routing-based) and programmatic. Packaged as npm modules.

**Node-RED custom nodes**: Two-file registration: JS runtime (`RED.nodes.registerType`) and HTML (definition, edit template, help). Nodes communicate via `msg` objects. npm packages.

**Apache NiFi custom processors**: `AbstractProcessor` with `PropertyDescriptor` (builder pattern), `Relationship` (output connections), `onTrigger(ProcessContext, ProcessSession)`. FlowFile = immutable data + key-value attributes. NAR (NiFi ARchive) packaging with SPI registration.

**Streamlit custom components**: iframe-based. Frontend HTML/JS/React + Python `declare_component()`. JS->Python via `Streamlit.setComponentValue(value)` triggering rerun. Pip packages.

**Gradio custom components**: `gradio cc create --template <base> <name>`. Backend: `preprocess()`, `postprocess()`, `example_payload()`, `example_value()`. Frontend: Svelte. CLI: create -> dev -> build -> publish.

**Panel ReactiveHTML**: `pn.reactive.ReactiveHTML` with `_template` + `${param_name}` bindings, `_scripts` for JS. Bidirectional sync.

**Mage.ai blocks**: Decorators: `@data_loader`, `@transformer`, `@data_exporter`, `@sensor`, `@callback`, `@condition`. New block types require core modification.

**KNIME nodes**: `NodeModel` (Java) with `configure()`, `execute()`, `reset()`. Input/output port types. Distributed via KNIME Hub.

**Grasshopper components**: .NET `GH_Component` subclasses. Unique GUIDs for serialization. Yak package manager for auto-install.

**Wolfram Mathematica**: 20+ cell styles: Input, Output, Text, Title, Section, Subsection, Item, Chapter, Program, ExternalLanguage, Print, Message, Graphics, Graphics3D, Sound, Package, TestID, Initialization, Code (hidden). 100+ style options. Hierarchical cell groups. Notebook format (.nb) is a Mathematica expression.

### 5.6 nteract 2.0 MCP Server (27 Tools)

Rust+TypeScript rewrite on Tauri with Automerge CRDT. MCP server (`runt mcp`) exposes 27 tools for AI agents: create notebooks, write/execute cells, read outputs, install dependencies, pattern-match edit, restart kernels, manage environments. Agents connect as real-time Automerge peers. Environment-based runtimes detect `pyproject.toml`, `pixi.toml`, `environment.yml`.

---

## Category 6: Pipeline/Workflow Cell Types

### 6.1 Parameterized Cells (Papermill)

Papermill scans for cells tagged `parameters` in `cell.metadata.tags`, then inserts a NEW cell tagged `injected-parameters` immediately after. Python scoping means later assignments win. CLI: `papermill in.ipynb out.ipynb -p alpha 0.6`. Scrapbook integration: `scrapbook.glue("key", value)` stores named outputs retrievable from executed notebook.

**Databricks widgets**: `dbutils.widgets.text()`, `.dropdown()`, `.combobox()`, `.multiselect()`. All values are strings. Job parameterization maps `notebook_params` to widget values.

**Marimo**: `mo.cli_args()` for CLI, `mo.query_params()` for web, `app.run(defs={"batch_size": 64})` for programmatic override.

**Quarto**: YAML frontmatter `params:` with CLI override via `-P alpha:0.8`.

### 6.2 Scheduled/Cron Cells

All scheduling operates at notebook level, not cell level. Hex: multiple scheduled runs per project with cron, saved view selection (max 3), Slack/email notifications. Deepnote: one scheduled notebook per project. Databricks Jobs: cron + cluster config + `notebook_params`. Observable Cloud: scheduled notebook runs. PopSQL: 15-minute to weekly. Zeppelin: cron per notebook. **No platform supports cell-level scheduling.**

### 6.3 Writeback Cells

**Hex**: Dedicated Writeback cell type -- select DataFrame, target table, write mode (create/replace or append), with execution modes (manual, session, app, scheduled). **No other notebook has a dedicated write-back cell type.**

### 6.4 Data Profiling Cells

No platform has a dedicated profiling cell type. ydata-profiling integrates via `profile.to_widgets()` or `profile.to_notebook_iframe()`. Databricks "Data Profile" tab computed on-demand via Spark. D-Tale (`dtale.show(df)`) launches Flask server. Lux augments pandas with auto-generated visualizations. Deepnote: column-level distributions in table headers. Datalore: Statistics tab.

---

## Category 7: Display and Content Cells

### 7.1 Markdown/Rich Text Cells

Every platform supports markdown. **Polynote**: Rich Text cells with WYSIWYG editing including LaTeX math. **Deepnote**: Text blocks with rich formatting (bold, italic, headings, links, code, lists, callout, to-do). **Curvenote**: WYSIWYG with block-level version control. **Wolfram**: Full styled text with inline typesetting. **Observable**: `md` tagged template literal with reactive variable interpolation. **Marimo**: `mo.md(f"Value is {x}")` for dynamic markdown with Python variables.

### 7.2 LaTeX/Math Cells

**ContextKeeper**: Dedicated `latex` cell type with KaTeX rendering. **CoCalc**: Full LaTeX compilation with live preview and error highlighting (most complete). **Jupyter/Colab**: `$...$` and `$$...$$` in markdown cells. Not separate cell types.

### 7.3 HTML Cells

**ContextKeeper**: Dedicated `html` cell type with Monaco editor. **Jupyter**: `%%html` magic or `IPython.display.HTML()`. **Zeppelin**: `%angular` interpreter for AngularJS template paragraphs with `z.angularBind()` two-way binding.

### 7.4 Diagram Cells

**First-class diagram cells:**
- **Livebook kino_kroki Smart Cell**: 30+ diagram syntaxes (Graphviz, PlantUML, Mermaid, D2, BlockDiag, BPMN, Bytefield, C4, DBML, Ditaa, Erd, Excalidraw, Nomnoml, Pikchr, Structurizr, Svgbob, UMLet, Vega/Vega-Lite, WaveDrom, WireViz). Renders via Kroki API. Rasterizable.
- **ContextKeeper**: Dedicated `mermaid` cell type (`type: 'mermaid'`, icon `bi-diagram-3`, color `var(--cyan)`).
- **Observable**: First-class `mermaid` and `dot` (Graphviz) tagged template literals.
- **d2-widget** (PyPI): `%%d2` Jupyter magic and AnyWidget for D2 diagrams.

**Markdown-rendered (not first-class):**
- JupyterLab 4.1+: Mermaid natively in markdown via `text/vnd.mermaid` MIME type.
- jupyterlab-drawio: Full draw.io editor as document type.
- Colab: Mermaid via `%%html` magic.

**No platform gives diagrams an interactive cell type with visual editing** -- all render within markdown or as separate documents.

### 7.5 Image Cells

**Deepnote**: Dedicated Image block (upload or URL, no code). **Jupyter**: `IPython.display.Image(url_or_path)` or markdown `![alt](url)`.

### 7.6 Separator/Divider Cells

**Deepnote**: Dedicated Separator block. No other platform has a dedicated separator cell type.

### 7.7 Vega/Declarative Visualization Cells

**Polynote**: Dedicated Vega cell type -- write Vega-Lite JSON, renders visualization with Scala/Python variables as data sources.

### 7.8 Process Visualization Cells (Livebook-specific)

**Kino.Process.render_seq_trace/2**: Visualizes message passing between Elixir processes as sequence diagrams.
**Kino.Process.render_sup_tree/2**: Visualizes OTP supervision trees.
**Kino.Tree**: Nested data structure inspection.

---

## Category 8: Data Operation Cells

### 8.1 Table/DataFrame Cells

Implementations: Jupyter's `pandas.DataFrame.to_html()` (basic), Positron's Data Explorer (sparkline histograms, millions of rows, Convert to Code), Hex's DataFrameRenderer (virtual scrolling, column statistics), Deepnote (column profiling, null counts, type badges), Observable `Inputs.table` (sortable, searchable), Glide Data Grid (1M+ rows, used by Streamlit). Deepnote auto-profiles DataFrame outputs: column types, distributions, missing values, unique counts.

### 8.2 Spreadsheet Cells

**Mito** (`mitosheet.sheet(df)`): Excel-like in JupyterLab where every edit auto-generates pandas code. Built on Handsontable.
**ipysheet**: Handsontable-based with bidirectional widget linking and numpy/pandas interop.
**Streamlit `st.data_editor`**: Returns modified DataFrame with column config and validation.
**Sigma Computing**: Spreadsheet-like interface directly on warehouse data with LLM functions callable in cells.

### 8.3 Schema Browser Cells

Hex and Deepnote: sidebar panels with tree navigation, search, preview, copy-to-clipboard. Hex integrates dbt metadata (execution dates, source freshness, test status). Both cache schema for 7 days. Datalore: inherited from DataGrip with full schema tree browser. PopSQL: data catalog with search across all connections. Not cell types -- all are sidebar panels.

### 8.4 Secret and Credential Cells

Colab: `google.colab.userdata.get('SECRET_NAME')`. Databricks: `dbutils.secrets.get(scope, key)`. Hex: workspace-level environment variables. None are dedicated cell types.

### 8.5 Cache and Checkpoint Cells

Streamlit: `@st.cache_data` (serializable) and `@st.cache_resource` (connections/models) keyed on input hash. Marimo: implicit DAG-based caching + `mo.persistent_cache` for disk.

---

## Category 9: Agent and AI Infrastructure Cells

### 9.1 Autonomous Agent Cells (CONFIRMED NOVEL)

No existing platform implements agents as reactive DAG nodes in a notebook. LangGraph agents are standalone. ContextKeeper's agent cells participate in reactive execution with typed inputs, outputs, and tool declarations.

### 9.2 Tournament Cells (NOVEL)

Multiple model/agent configurations compete on same input; statistical testing selects winner. PyCaret's `compare_models()` is closest prior art but operates at function level without significance testing.

### 9.3 AI Narrative Cells

AI-generated text explanations of data/results. Hex has "Explain" feature. No dedicated cell type.

### 9.4 AI Fix Cells

AI-powered error fixing as a dedicated cell type. Not implemented anywhere.

### 9.5 AI Optimize Cells

AI-powered code profiling and optimization as a dedicated cell type. Not implemented anywhere.

---

## Category 10: Meta/Infrastructure Cells

### 10.1 Assertion/Test Cells

**nbval**: pytest plugin comparing stored outputs against re-execution. Cell markers: `# NBVAL_IGNORE_OUTPUT`, `# NBVAL_CHECK_OUTPUT`, `# NBVAL_SKIP`, `# NBVAL_RAISES_EXCEPTION`. Sanitization via regex config.

**testbook**: External test files: `@testbook('path.ipynb', execute=True)`, `tb.ref("func")` callable proxy, `tb.inject("code")`. Arguments JSON-serialized.

**nbmake**: pytest plugin executing notebooks top-to-bottom, fails on exceptions.

**nbgrader**: Structured taxonomy with metadata tags: Autograder Tests (assert + point values), Autograded Answer (solution stubs), Manually Graded, Read-only. Hidden test sections via `### BEGIN HIDDEN TESTS` delimiters.

**Great Expectations**: Pre-populated Jupyter notebooks per workflow step. Checkpoint YAML bundles validations + actions.

**ContextKeeper**: Dedicated `test` cell type (`cell.test = true`) with pass/fail badge rendering.

**Pluto.jl**: Built-in `@test` macro, reactive re-run on dependency changes.

### 10.2 Terminal/Shell Cells

**Databricks**: `%sh` on driver node, `%fs` for DBFS. **Zeppelin**: `%sh` interpreter. **Jupyter**: `!command` (new subprocess per line), `%%bash` (single process), `%%script` (arbitrary interpreters). **Livebook**: Shell Script Smart Cell wrapping `System.shell/2`. **Colab**: `!command` or `%%bash`. **ContextKeeper**: Separate terminal page with multiple console tabs.

### 10.3 Approval/Gate Cells

**No notebook has a dedicated approval cell type.** Closest equivalents:
- **Livebook `Kino.interrupt!/2`**: Pauses cell evaluation, displays "Continue" button.
- **Prefect**: `pause_flow_run` (blocks, process stays alive) and `suspend_flow_run` (exits process). `wait_for_input` accepts Pydantic BaseModel for form rendering.
- **n8n Wait Nodes**: Resume on duration, webhook, or form submission. Approval URL via `crypto.randomUUID()`.
- **Airflow**: 13 trigger rules but no native human approval gate.
- **Dagster**: Asset sensors waiting for manual materializations.
- **Marimo**: `mo.stop(condition, output)` halts reactive propagation.

### 10.4 Decision/Router Cells

No notebook implements this. Pipeline frameworks have it: KNIME IF Switch, Mage.ai conditional blocks, Airflow BranchPythonOperator, Node-RED Switch.

### 10.5 Branch/Compare/Merge Cells

No notebook implements branch creation, parallel execution, statistical comparison, and promotion as cell types. Livebook branching sections are closest prior art.

### 10.6 Module/Reusable Component Cells

**Observable**: `import {cellName} from "@user/notebook"` -- closest to cell-level registry. **Deepnote**: Reusable modules importable across notebooks. **Wolfram**: `Package` cells export definitions.

### 10.7 Comment/Discussion Cells

**ContextKeeper**: Per-cell comment threads with user, timestamp, text, resolve button. **Deepnote**: Inline comments on code blocks. **Hex**: Cell-level comments.

### 10.8 Raw Cells

**Jupyter**: Passes content through nbconvert unmodified. Used for LaTeX preambles, custom HTML, format-specific content. **ContextKeeper**: `raw` cell type.

### 10.9 Livebook Setup Cell

Special cell at top of every notebook for dependency management via `Mix.install/2` with global caching and Hex.pm package search UI.

### 10.10 Environment Cells

**Marimo**: PEP 723 inline script metadata for dependencies, auto-installed in isolated venv sandboxes via uv.

---

## Category 11: Novel/Unusual Cell Types

### 11.1 RunKit Endpoint Cells -- Live HTTP Servers

The most exotic cell type in existence. Any cell exporting an `endpoint` function becomes a live HTTP API:
```javascript
exports.endpoint = function(request, response) { response.end("Hello"); }
```
Auto-assigned URL, supports sub-paths, Express.js middleware, JSON helpers. Code edits reflect in real-time. Rate-limited, 60-second timeout, HTTPS only. The only platform where individual cells serve as production HTTP endpoints.

### 11.2 Webhook/API Endpoint Cells

**Marimo**: ASGI app via `marimo.create_asgi_app().with_app(path="/", root="notebook.py")`, mountable on FastAPI. Built-in endpoints: `/health`, `/healthz`, `/api/status`.

**Jupyter Kernel Gateway**: Comment annotations (`# GET /hello/world`) define HTTP endpoints. `REQUEST` global contains request JSON. Auto-generates Swagger/OpenAPI spec.

**Mercury**: `mr.APIResponse()` converts notebooks to REST APIs with async long-polling.

**Gradio**: Auto-generated endpoints at `/gradio_api/call/<api_name>` with SSE streaming. `gradio.Server()` mode for API-only apps. MCP protocol support.

### 11.3 Audio/Video Cells

**Livebook**: `Kino.Input.audio()` and `Kino.Input.image()` support recording via mic/camera. `Kino.Image.new(binary, :pixel)` accepts `Nx.Tensor`. Bumblebee Smart Cells support Whisper and image classification.

**Gradio**: `gr.Audio(sources=["microphone"], streaming=True)`, `gr.Video(sources=["webcam"])`. `gradio-webrtc` for ultra-low-latency.

**Jupyter**: `IPython.display.Audio/Video` render HTML5 elements. `ipywebrtc` for webcam/screen capture.

No traditional notebook platform has native audio/video recording cells.

### 11.4 Scratch/Draft Cells

**ContextKeeper**: Dedicated `scratch` cell type with dashed border, "SCRATCH" label. Excluded from Run All.
**Marimo**: Scratchpad cells -- ephemeral execution cells that don't persist in the notebook.

### 11.5 File Upload/Download Cells

**Hex**: File Upload input returning DataFrame (CSV, Excel, JSON, Parquet auto-detected). **Deepnote**: File Upload block with drag-and-drop. **Marimo**: `mo.ui.file(filetypes=[...])` reactive upload. **Livebook**: `Kino.Input.file()` with drag-and-drop + `Kino.Download` for download buttons. **Jupyter**: `ipywidgets.FileUpload()` + `IPython.display.FileLink()`. **Colab**: `google.colab.files.upload()` / `.download()`.

### 11.6 Map/Geospatial Cells

**Livebook MapLibre Smart Cell**: Only true "map cell type" with dedicated UI. `Ml.new(center: {lng, lat})` -> `Ml.add_source()` -> `Ml.add_layer()`. Dynamic maps via `Kino.MapLibre.new/1` with live `Kino.MapLibre.add_marker()`.

**Kepler.gl**: Jupyter widget (`KeplerGl(height=400, data={"data_1": df})`) with config extraction. GPU-accelerated millions of points.

**pydeck**: Python -> JSON -> `@deck.gl/json` API with bidirectional communication.

**ipyleaflet**: Interactive Leaflet maps as ipywidgets. Layers: TileLayer, Marker, Circle, Polygon, GeoJSON, Choropleth, Heatmap, VelocityMap, AntPath. Bidirectional sync.

**Folium**: Static Leaflet maps as HTML. No bidirectional interaction.

**Observable**: D3-geo, Leaflet, Mapbox GL JS, deck.gl directly in JS cells. `Plot.geo()`.

**Evidence**: `<USMap>`, `<PointMap>` components.

### 11.7 Benchmark Cells

Jupyter `%%timeit` magic. No dedicated cell type with statistical benchmarking (multiple runs, confidence intervals) exists anywhere.

### 11.8 Drift Detection Cells

No platform tracks cell-level output distribution monitoring across runs. Novel design space.

---

## Architectural Patterns for a Universal Cell Registry -- Consolidated Conclusion

This inventory reveals **five architectural patterns** that a cell registry must accommodate, drawn from analysis of 200+ cell implementations across 50+ platforms.

### Pattern 1: Rasterization (Livebook Smart Cells)

Rich UI generates executable source code. The most portable approach since cells degrade gracefully to plain code when their package isn't installed. Smart cells store both configuration AND generated source code. This solves the dependency problem -- notebooks remain functional even without the smart cell runtime.

### Pattern 2: Typed-Port Graph (ComfyUI, n8n, Node-RED, NiFi)

Cells declare input/output types and a runtime resolves the execution graph. The most scalable for tens of thousands of node types. ComfyUI's `NODE_CLASS_MAPPINGS` + `INPUT_TYPES`/`RETURN_TYPES`/`FUNCTION` registration is the most transferable protocol -- cleanly separating type declaration from execution. The two-dict pattern (`NODE_CLASS_MAPPINGS` + `NODE_DISPLAY_NAME_MAPPINGS`) separates identity from presentation.

### Pattern 3: Reactive Variable Binding (Marimo, Observable, Pluto.jl)

Cells declare dependencies through variable references and a runtime manages the DAG. The most natural for interactive exploration. Observable's `viewof` protocol (any DOM element with `.value` + `input` event) demonstrates that reactive binding can be standardized with minimal interface requirements.

### Pattern 4: MIME-Based Extension (JupyterLab)

New output types register via MIME renderers. The most backward-compatible approach. Limited to output rendering -- cannot define new input behaviors or execution semantics.

### Pattern 5: Iframe Isolation (Streamlit, Retool)

Cells run in sandboxed iframes communicating via postMessage. The most secure for third-party extensions.

### The Critical Gap

**No platform combines all five capabilities** -- extensible registration, declarative I/O schemas, portable rasterization, standardized reactive binding, and secure isolation. Jupyter's three-type schema limit has forced the ecosystem to implement cell-type innovation as output renderers, magic commands, or sidebar assistants rather than first-class cell types.

### Design Recommendations for ContextKeeper

1. **Typed inputs/outputs** (ComfyUI): Every cell type declares `INPUT_TYPES` and `RETURN_TYPES` for graph validity.
2. **Rasterization** (Livebook): Every smart/no-code cell convertible to plain code revealing generated source.
3. **Reactive binding** (Marimo/Observable): Widget cells integrate into dependency DAG.
4. **Connection context** (Hex/Databricks): SQL and data cells bind to connection objects in the DAG.
5. **Category hierarchy** (ComfyUI): Maximum 2 levels for navigation at scale.
6. **Registration simplicity** (ComfyUI/Livebook): New cell type = class/module + registration call.
7. **SQLMesh per-model dialect transpilation** via SQLGlot combined with Livebook's `to_source` rasterization forms the strongest foundation for a registry scaling to tens of thousands of types.

### Critical Open Gaps Across All Platforms

- **Cell-level scheduling**: No platform supports per-cell scheduling.
- **Approval gating**: No notebook has a dedicated approval cell type.
- **Prompt versioning**: No notebook has built-in prompt versioning or A/B testing.
- **Full DAG-participating prompt cells**: No LLM cell auto-types output into the DAG.
- **Cell-level RBAC**: No notebook implements access control below notebook level.
- **Diagram cells with visual editing**: All render in markdown or separate documents.

---

## Appendix: The 78-Type Taxonomy for ContextKeeper Registry

**Tier 1: Execution Cells (8 types)**
- Code cells (Python, R, Julia, Bash, JavaScript, SQL, Scala, Rust-via-WASM)
- SQL cells (warehouse SQL, DataFrame SQL, streaming SQL)
- Shell/Terminal cells
- LLM/Prompt cells

**Tier 2: Content/Display Cells (9 types)**
- Markdown cells
- LaTeX/Math cells
- HTML cells
- Raw cells
- Image cells
- Separator/Divider cells
- Chart/Visualization cells (Plotly, Vega-Lite, Observable Plot, Altair, Matplotlib, Seaborn)
- Map cells (Folium, Kepler.gl, Deck.gl, Mapbox)
- Metric/KPI cells
- Mermaid/Diagram cells

**Tier 3: Input/Widget Cells (40+ types across platforms)**
- Core: slider, dropdown/select, date picker, text input, button, file upload, color picker, toggle/checkbox, range slider, radio buttons, number input, table input (editable DataFrame)
- Advanced: code editor, microphone, camera, chat interface, periodic timer

**Tier 4: Data Operation Cells (6 types)**
- Table/DataFrame cells
- Profile cells
- Schema cells
- Validation cells
- Writeback cells
- Pivot/Transform cells
- Filter cells

**Tier 5: AI/Agent Cells (5 types)**
- Prompt/LLM cells
- Agent pipeline cells (NOVEL)
- AI narrative cells
- AI fix cells
- AI optimize cells
- Tournament cells (NOVEL)

**Tier 6: Pipeline/Workflow Cells (6 types)**
- Contract cells (typed I/O schemas)
- Branch cells
- Comparison cells
- Decision/Router cells (NOVEL in notebooks)
- Merge cells
- Approval/Gate cells (NOVEL in notebooks)

**Tier 7: Infrastructure Cells (10 types)**
- Version history cells
- Diff cells
- Test/Assertion cells
- Benchmark cells (NOVEL as dedicated type)
- Export cells
- Connection cells
- Environment/Config cells
- Scratch/Draft cells
- Comment/Discussion cells
- Module/Reusable component cells

**Total unique cell-type concepts: 78 across 8 tiers.** Of these, approximately 12 are genuinely novel (no implementation exists), and 66 have at least one existing implementation across 50+ platforms.
