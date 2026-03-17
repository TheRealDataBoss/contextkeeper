# GPT-Claude Orchestration Protocol
# contextkeeper.org development workflow
# Version: 2.0
# Last updated: 2026-03-17

## Roles

### GPT (Orchestrator)
- Owns the master task list, priority stack, and project state
- Decides what gets built next
- Writes scoped execution prompts for Claude
- Reviews Claude's output and decides next action
- Maintains DEFINITIVE-AUDIT.md and project roadmap
- Handles strategic decisions, naming, branding, copy, marketing language
- Never writes production code

### Claude (Executor)
- Receives a scoped execution prompt
- Builds exactly what is specified
- Reports results in HANDBACK format
- STOPS after handback. Does not suggest next steps.
- Does not scope future work unless explicitly asked
- Does not make strategic decisions about product direction

### Steven (Operator)
- Shuttles prompts between GPT and Claude
- Deploys to cPanel
- Tests in browser
- Provides screenshots for verification
- Makes final decisions on strategic questions

## The Execution Cycle

```
GPT writes execution prompt
       |
       v
Steven pastes into Claude
       |
       v
Claude executes, produces deliverables
       |
       v
Claude outputs HANDBACK block
       |
       v
Steven pastes HANDBACK into GPT
       |
       v
GPT updates state, writes next execution prompt
       |
       v
(repeat)
```

## Execution Prompt Format (GPT writes this)

GPT MUST include any files Claude will need with the execution prompt.
Claude should not have to search past chats, guess at file contents,
or re-audit the codebase. If Claude needs the current billing.php to
patch it, GPT includes billing.php. If Claude needs the schema, GPT
includes schema.sql. Steven uploads these as attachments alongside
the GPT prompt.

```
## TASK: [short title]
Sprint: [number]
Priority: [P0/P1/P2]

### Context
[1-3 sentences of relevant background]

### Specification
[Exactly what to build. File names, endpoints, behavior.]

### Acceptance Criteria
- [ ] criterion 1
- [ ] criterion 2

### Constraints
- [any technical constraints, e.g. "no composer dependencies"]
- [any file paths that must not change]

### Attached Files
- [filename] - [why Claude needs it]
- [filename] - [why Claude needs it]
(Steven uploads these alongside the prompt)

### Deliverable
[zip / files / specific output format expected]
```

## Handback Format (Claude writes this)

After completing an execution prompt, Claude outputs ONLY this block
and nothing else. No suggestions. No "next steps". No roadmap.

```
## HANDBACK

### Task
[1-line restatement of what was requested]

### Delivered
- file1.php (new) - [1-line description]
- file2.php (modified) - [what changed]

### Deployment
[zip name / extraction steps / SQL to run]

### Verification
- [endpoint or page]: [expected result] - PASS/FAIL/UNTESTED

### Issues
[any deviations from spec, blockers, or edge cases found]
[or "None"]

### GPT State Update
Paste this into GPT to sync state:

---
EXECUTION COMPLETE: [task title]
Files delivered: [count]
Sprint: [number]
Status: READY_TO_DEPLOY / DEPLOYED / BLOCKED
Blockers: [none / description]
New endpoints: [list or none]
New pages: [list or none]
DB changes: [migration name or none]
---
```

## When Claude CAN Go Beyond the Prompt

There are specific situations where Claude should use judgment:

1. **Bug found during execution** - Fix it and note in HANDBACK Issues
2. **Security vulnerability spotted** - Fix it and flag in Issues
3. **Spec is ambiguous** - Ask Steven before proceeding
4. **Spec is impossible** - Explain why in Issues, propose alternative
5. **Deployment verification** - Claude should curl live endpoints to verify

## When Claude Must NOT Go Beyond the Prompt

1. **Do not suggest the next task** - GPT decides priority
2. **Do not scope future sprints** - GPT owns the roadmap
3. **Do not propose product features** - GPT handles product strategy
4. **Do not ask "what's next?"** - End with the HANDBACK block
5. **Do not list remaining work** - GPT maintains that list

## Bidirectional Communication

GPT and Claude must stay in sync. They never talk directly - Steven
is the bridge. The protocol ensures no information is lost in transit.

### GPT -> Claude (via Steven)
GPT produces:
1. The execution prompt (text)
2. Any files Claude needs to do the work (Steven uploads these)
3. The current DEFINITIVE-AUDIT.md if state context is needed

GPT must anticipate what Claude needs. If the task involves modifying
an existing file, GPT tells Steven to do a fresh cPanel download of
that file and attach it. Claude should never have to search past
conversations to find file contents.

### Claude -> GPT (via Steven)
Claude produces:
1. The HANDBACK block (Steven pastes into GPT)
2. The deliverable zip (Steven deploys to cPanel)
3. Any updated file contents GPT needs to maintain state

The HANDBACK block contains a structured GPT State Update section
specifically designed so GPT can parse it and update its records
without Steven having to translate or summarize.

### Sync Failures
If Claude receives a prompt without needed files:
- Ask Steven to get them from cPanel before starting
- Do NOT attempt to reconstruct from memory or past chats
- Do NOT curl the live site as a substitute for source files

If GPT receives a HANDBACK that is unclear:
- Ask Steven to go back to Claude for clarification
- Do NOT guess at what was built

## Token Budget Awareness

The whole point of this protocol is token efficiency:
- GPT (cheap tokens) handles planning, scoping, state management
- Claude (expensive tokens) handles execution only
- Steven handles deployment and browser testing
- No model repeats work the other model already did

## State Files

| File | Location | Owner |
|------|----------|-------|
| DEFINITIVE-AUDIT.md | .contextkeeper/ on cPanel | GPT |
| STATE_VECTOR.json | projects/contextkeeper-site/ in workbench repo | GPT |
| HANDOFF.md | projects/contextkeeper-site/ in workbench repo | GPT |
| DEPLOY.md | Delivered with each sprint zip | Claude |

## Emergency Override

If Steven says "just do it" or "keep going" or "continue" without
a GPT execution prompt, Claude should:

1. State what it thinks the next logical task is
2. Ask Steven to confirm
3. Execute and produce HANDBACK as normal

This prevents Claude from silently burning tokens on the wrong task.
