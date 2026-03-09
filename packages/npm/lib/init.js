import chalk from 'chalk'
import ora from 'ora'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs'
import { basename, resolve, join } from 'path'
import { createRequire } from 'module'

const PROJECT_TYPE_SIGNALS = [
  { file: 'manage.py',        type: 'web_app',           label: 'Django web app' },
  { file: 'next.config.js',   type: 'web_app',           label: 'Next.js web app' },
  { file: 'next.config.mjs',  type: 'web_app',           label: 'Next.js web app' },
  { file: 'vite.config.ts',   type: 'web_app',           label: 'Vite web app' },
  { file: 'vite.config.js',   type: 'web_app',           label: 'Vite web app' },
  { file: 'Cargo.toml',       type: 'cli_tool',          label: 'Rust project' },
  { file: 'setup.py',         type: 'library',           label: 'Python library' },
  { file: 'pyproject.toml',   type: 'library',           label: 'Python project' },
  { file: 'requirements.txt', type: 'ml_pipeline',       label: 'Python ML pipeline' },
  { file: 'package.json',     type: 'web_app',           label: 'Node.js project' },
]

function detectProjectType(dir) {
  for (const signal of PROJECT_TYPE_SIGNALS) {
    if (existsSync(join(dir, signal.file))) {
      return { type: signal.type, label: signal.label, file: signal.file }
    }
  }
  // Check for notebooks
  const files = []
  try {
    const { readdirSync } = await import('fs')
  } catch {}
  return { type: 'other', label: 'unknown project type', file: null }
}

function detectGates(projectType) {
  const gates = {
    web_app:           ['npm test', 'npm run build', 'git status'],
    ml_pipeline:       ['python -m pytest', 'git status'],
    research_notebook: ['jupyter nbconvert --execute --to notebook', 'git status'],
    data_pipeline:     ['python -m pytest', 'git status'],
    mobile_app:        ['npm test', 'npm run build', 'git status'],
    cli_tool:          ['npm test', 'npm run build', 'git status'],
    library:           ['npm test', 'npm run build', 'git status'],
    course_module:     ['jupyter nbconvert --execute --to notebook', 'git status'],
    other:             ['git status'],
  }
  return gates[projectType] || ['git status']
}

export async function initProject(options) {
  const cwd = resolve('.')
  const projectName = options.project || basename(cwd)

  console.log(chalk.cyan('\n  workbench init\n'))

  // Detect project type
  const spinner = ora('Detecting project type...').start()
  const detected = detectProjectType(cwd)
  spinner.succeed(`Detected: ${chalk.bold(detected.label)}${detected.file ? ` (found ${detected.file})` : ''}`)

  const projectType = options.type || detected.type

  // Prompt for bridge repo if not provided
  let bridgeRepo = options.bridge || null
  if (!bridgeRepo) {
    const Enquirer = (await import('enquirer')).default
    const response = await new Enquirer().prompt({
      type: 'input',
      name: 'bridge',
      message: 'Bridge repo (e.g. yourname/workbench):',
      initial: '',
    })
    bridgeRepo = response.bridge || null
  }

  // Create directories
  const handoffDir = join(cwd, 'handoff')
  const docsDir = join(cwd, 'docs')

  if (!existsSync(handoffDir)) mkdirSync(handoffDir, { recursive: true })
  if (!existsSync(docsDir)) mkdirSync(docsDir, { recursive: true })

  // Generate STATE_VECTOR.json
  const stateVector = {
    schema_version: 'workbench-v1.0',
    project: projectName,
    project_type: projectType,
    local_path: cwd,
    state_machine_status: 'IDLE',
    active_task_id: null,
    active_task_title: null,
    current_blocker: null,
    last_verified_state: 'Initial project setup',
    gates: detectGates(projectType),
    last_updated: new Date().toISOString().split('T')[0],
    repo: bridgeRepo ? `https://github.com/${bridgeRepo}` : 'local only',
    branch: 'main',
    repo_head_sha: null,
    effective_verified_sha: null,
  }

  const stateVectorPath = join(handoffDir, 'STATE_VECTOR.json')
  writeFileSync(stateVectorPath, JSON.stringify(stateVector, null, 2) + '\n', 'utf8')
  console.log(chalk.green(`  Created: ${stateVectorPath}`))

  // Generate HANDOFF.md
  const handoff = `# ${projectName} — Project Handoff
schema_version: workbench-v1.0

## What It Is
[FILL IN: Describe this project in one paragraph.]

## Where It Is
- Local: ${cwd}
- GitHub: ${stateVector.repo}
- Branch: main

## Current Status
State machine: IDLE. No active task.

## Active Blocker
None

## Non-Negotiables
- [FILL IN: List project invariants]

## Gates
${stateVector.gates.map(g => `- ${g}`).join('\n')}

## Environment Setup
[FILL IN: Steps to run from a clean clone]

## Next Action
[FILL IN: First task to work on]
`

  const handoffPath = join(docsDir, 'HANDOFF.md')
  writeFileSync(handoffPath, handoff, 'utf8')
  console.log(chalk.green(`  Created: ${handoffPath}`))

  // Write .workbench config
  const config = {
    bridge_repo: bridgeRepo,
    project_name: projectName,
    state_vector_path: 'handoff/STATE_VECTOR.json',
    handoff_path: 'docs/HANDOFF.md',
  }
  const configPath = join(cwd, '.workbench')
  writeFileSync(configPath, JSON.stringify(config, null, 2) + '\n', 'utf8')
  console.log(chalk.green(`  Created: ${configPath}`))

  console.log(chalk.cyan('\n  Next steps:'))
  console.log(chalk.white('  1. Fill in the [FILL IN] sections in docs/HANDOFF.md'))
  console.log(chalk.white('  2. Review handoff/STATE_VECTOR.json'))
  console.log(chalk.white(`  3. Run: ${chalk.bold('workbench sync')} to push to your bridge repo`))
  console.log()
}
