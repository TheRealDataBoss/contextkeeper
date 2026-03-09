import chalk from 'chalk'
import ora from 'ora'
import { existsSync, readFileSync } from 'fs'
import { resolve, join } from 'path'
import { simpleGit } from 'simple-git'
import { tmpdir } from 'os'
import { mkdtempSync, rmSync } from 'fs'
import { exec } from 'child_process'
import { platform } from 'os'

function loadConfig(cwd) {
  const configPath = join(cwd, '.workbench')
  if (!existsSync(configPath)) return null
  return JSON.parse(readFileSync(configPath, 'utf8'))
}

function copyToClipboard(text) {
  return new Promise((resolve, reject) => {
    const os = platform()
    let cmd
    if (os === 'darwin') {
      cmd = 'pbcopy'
    } else if (os === 'win32') {
      cmd = 'clip'
    } else {
      cmd = 'xclip -selection clipboard'
    }
    const proc = exec(cmd, (err) => {
      if (err) reject(err)
      else resolve()
    })
    proc.stdin.write(text)
    proc.stdin.end()
  })
}

export async function generateBootstrap(options) {
  const cwd = resolve('.')
  const config = loadConfig(cwd)
  const bridgeRepo = options.bridge || config?.bridge_repo
  const projectName = options.project

  console.log(chalk.cyan('\n  workbench bootstrap\n'))

  if (!bridgeRepo) {
    console.log(chalk.red('  No bridge repo configured. Run workbench init or pass --bridge.'))
    process.exit(1)
  }

  // Verify the project exists in the bridge repo
  const spinner = ora('Verifying project in bridge repo...').start()
  const tmpDir = mkdtempSync(join(tmpdir(), 'workbench-'))

  try {
    const bridgeUrl = `https://github.com/${bridgeRepo}.git`
    const git = simpleGit()
    await git.clone(bridgeUrl, tmpDir, ['--depth', '1'])

    const projectDir = join(tmpDir, 'projects', projectName)
    if (!existsSync(projectDir)) {
      spinner.fail(`Project "${projectName}" not found in bridge repo.`)
      const projectsDir = join(tmpDir, 'projects')
      if (existsSync(projectsDir)) {
        const available = readFileSync
        const { readdirSync } = await import('fs')
        const projects = readdirSync(projectsDir, { withFileTypes: true })
          .filter(d => d.isDirectory())
          .map(d => d.name)
        if (projects.length > 0) {
          console.log(chalk.gray(`  Available projects: ${projects.join(', ')}`))
        }
      }
      process.exit(1)
    }

    const hasState = existsSync(join(projectDir, 'STATE_VECTOR.json'))
    const hasHandoff = existsSync(join(projectDir, 'HANDOFF.md'))

    if (!hasState) {
      spinner.fail(`No STATE_VECTOR.json found for ${projectName}`)
      process.exit(1)
    }

    spinner.succeed(`Project "${projectName}" verified`)

    // Build the bootstrap prompt with all URLs explicit
    const baseUrl = `https://raw.githubusercontent.com/${bridgeRepo}/main`
    const urls = [
      `${baseUrl}/PROFILE.md`,
      `${baseUrl}/projects/${projectName}/HANDOFF.md`,
      `${baseUrl}/projects/${projectName}/STATE_VECTOR.json`,
    ]

    const prompt = [
      `Fetch these URLs and bootstrap the ${projectName} project:`,
      ...urls,
    ].join('\n')

    console.log(chalk.white('\n  Paste this into any new AI chat:\n'))
    console.log(chalk.green('  ┌─────────────────────────────────────────────┐'))
    for (const line of prompt.split('\n')) {
      console.log(chalk.green('  │ ') + chalk.white(line))
    }
    console.log(chalk.green('  └─────────────────────────────────────────────┘'))
    console.log()

    if (options.clipboard) {
      try {
        await copyToClipboard(prompt)
        console.log(chalk.green('  Copied to clipboard!'))
      } catch {
        console.log(chalk.yellow('  Could not copy to clipboard. Copy manually from above.'))
      }
    }

    console.log()
  } finally {
    try { rmSync(tmpDir, { recursive: true, force: true }) } catch {}
  }
}
