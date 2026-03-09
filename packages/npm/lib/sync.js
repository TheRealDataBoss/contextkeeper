import chalk from 'chalk'
import ora from 'ora'
import { existsSync, readFileSync, mkdirSync, copyFileSync } from 'fs'
import { resolve, join } from 'path'
import { simpleGit } from 'simple-git'
import { tmpdir } from 'os'
import { mkdtempSync, rmSync } from 'fs'
import Ajv from 'ajv'
import addFormats from 'ajv-formats'
import { fileURLToPath } from 'url'
import { dirname } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

function loadConfig(cwd) {
  const configPath = join(cwd, '.workbench')
  if (!existsSync(configPath)) {
    return null
  }
  return JSON.parse(readFileSync(configPath, 'utf8'))
}

function loadSchema() {
  const schemaPath = resolve(__dirname, '..', '..', '..', 'protocol', 'workbench.schema.json')
  if (existsSync(schemaPath)) {
    return JSON.parse(readFileSync(schemaPath, 'utf8'))
  }
  // Fallback: check relative to home dir
  const homeFallback = join(process.env.HOME || process.env.USERPROFILE, '.workbench', 'src', 'protocol', 'workbench.schema.json')
  if (existsSync(homeFallback)) {
    return JSON.parse(readFileSync(homeFallback, 'utf8'))
  }
  return null
}

export async function syncProject(options) {
  const cwd = resolve('.')
  const config = loadConfig(cwd)

  console.log(chalk.cyan('\n  workbench sync\n'))

  if (!config && !options.bridge) {
    console.log(chalk.red('  No .workbench config found. Run workbench init first, or pass --bridge.'))
    process.exit(1)
  }

  const bridgeRepo = options.bridge || config.bridge_repo
  const projectName = config?.project_name || ''
  const stateVectorRel = config?.state_vector_path || 'handoff/STATE_VECTOR.json'
  const handoffRel = config?.handoff_path || 'docs/HANDOFF.md'

  if (!bridgeRepo) {
    console.log(chalk.red('  No bridge repo configured. Run workbench init or pass --bridge.'))
    process.exit(1)
  }

  if (!projectName) {
    console.log(chalk.red('  No project_name in .workbench config.'))
    process.exit(1)
  }

  // Read and validate STATE_VECTOR.json
  const stateVectorPath = join(cwd, stateVectorRel)
  if (!existsSync(stateVectorPath)) {
    console.log(chalk.red(`  STATE_VECTOR.json not found at ${stateVectorPath}`))
    process.exit(1)
  }

  const spinner = ora('Validating STATE_VECTOR.json...').start()
  const stateVector = JSON.parse(readFileSync(stateVectorPath, 'utf8'))

  const schema = loadSchema()
  if (schema) {
    const ajv = new Ajv({ allErrors: true })
    addFormats(ajv)
    const validate = ajv.compile(schema)
    const valid = validate(stateVector)
    if (!valid) {
      spinner.fail('STATE_VECTOR.json validation failed:')
      for (const err of validate.errors) {
        console.log(chalk.red(`    ${err.instancePath || '/'}: ${err.message}`))
      }
      process.exit(1)
    }
  }
  spinner.succeed('STATE_VECTOR.json is valid')

  if (options.dryRun) {
    console.log(chalk.yellow('\n  Dry run — would sync:'))
    console.log(chalk.white(`    ${stateVectorRel} → projects/${projectName}/STATE_VECTOR.json`))
    if (existsSync(join(cwd, handoffRel))) {
      console.log(chalk.white(`    ${handoffRel} → projects/${projectName}/HANDOFF.md`))
    }
    console.log()
    return
  }

  // Clone bridge repo
  const cloneSpinner = ora('Cloning bridge repo...').start()
  const tmpDir = mkdtempSync(join(tmpdir(), 'workbench-'))

  try {
    const bridgeUrl = `https://github.com/${bridgeRepo}.git`
    const git = simpleGit()
    await git.clone(bridgeUrl, tmpDir, ['--depth', '1'])
    cloneSpinner.succeed('Bridge repo cloned')

    // Copy files
    const targetDir = join(tmpDir, 'projects', projectName)
    mkdirSync(targetDir, { recursive: true })

    copyFileSync(stateVectorPath, join(targetDir, 'STATE_VECTOR.json'))
    console.log(chalk.green(`  Copied: STATE_VECTOR.json`))

    const handoffPath = join(cwd, handoffRel)
    if (existsSync(handoffPath)) {
      copyFileSync(handoffPath, join(targetDir, 'HANDOFF.md'))
      console.log(chalk.green(`  Copied: HANDOFF.md`))
    }

    const nextTaskPath = join(cwd, 'docs', 'NEXT_TASK.md')
    if (existsSync(nextTaskPath)) {
      copyFileSync(nextTaskPath, join(targetDir, 'NEXT_TASK.md'))
      console.log(chalk.green(`  Copied: NEXT_TASK.md`))
    }

    // Commit and push
    const pushSpinner = ora('Pushing to bridge repo...').start()
    const bridgeGit = simpleGit(tmpDir)
    await bridgeGit.add('.')

    const status = await bridgeGit.status()
    if (status.files.length === 0) {
      pushSpinner.info('No changes to push')
      return
    }

    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 16) + ' UTC'
    const commitMsg = `chore(workbench): sync ${projectName} -- ${timestamp}`
    await bridgeGit.commit(commitMsg)
    await bridgeGit.push('origin', 'main')

    const log = await bridgeGit.log({ maxCount: 1 })
    const sha = log.latest.hash.substring(0, 7)

    pushSpinner.succeed(`Pushed: ${chalk.bold(sha)}`)
    console.log(chalk.green(`\n  Sync complete for ${chalk.bold(projectName)}`))
    console.log(chalk.gray(`  ${commitMsg}\n`))
  } finally {
    try { rmSync(tmpDir, { recursive: true, force: true }) } catch {}
  }
}
