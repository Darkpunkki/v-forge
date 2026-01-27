$ErrorActionPreference = "Stop"

# Repo root (this file is in <repo>\scripts\)
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$TasksPath  = "C:\Apps\vibeforge_skeleton\docs\forge\ideas\IDEA-0003-vibeforge-is-pivoting\latest\tasks.md"
$PickScript = Join-Path $RepoRoot "scripts\ralph_pick.py"
$PromptFile = Join-Path $RepoRoot "scripts\prompts\ralph_task.md"

$MaxIterations = 100

for ($i = 1; $i -le $MaxIterations; $i++) {

  $taskYaml = python $PickScript $TasksPath

  if ($taskYaml -match "RALPH_DONE") {
    Write-Host "RALPH_DONE: no eligible tasks left."
    break
  }

  # Base prompt template (optional)
  if (Test-Path $PromptFile) {
    $base = Get-Content $PromptFile -Raw
  } else {
    $base = @"
RALPH_MODE: true

Complete exactly ONE task described below (YAML).

Rules:
- Use acceptance_criteria as the definition of done.
- Respect dependencies.
- Prefer editing only target_files unless truly necessary.
- Run verification commands from AGENTS.md (or standard build/test for this repo).
- Update ralph_state.yaml:
  - append task id to done if successful
  - else set blocked[task_id] = short reason + next step
- End with: RALPH_STATUS: done|blocked TASK-###
"@
  }

  $fullPrompt = $base + "`n`nTASK:`n" + $taskYaml + "`n"

  # Non-interactive run; '-' reads prompt from stdin.
  $fullPrompt | codex exec --full-auto -

  git diff --stat
}

if ($i -gt $MaxIterations) {
  Write-Host "Stopped: reached MaxIterations=$MaxIterations"
}
