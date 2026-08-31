#Requires -Version 5.1
<#
    Portable orchestrator demo launcher (Windows PowerShell / PowerShell 7).
    Mirrors scripts/demo.sh command for command.
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("up", "airflow", "dagster", "prefect", "kestra", "docs", "tour",
                 "status", "logs", "down", "clean", "help")]
    [string]$Command = "up",

    [switch]$NoWait
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

# Passed to native docker, so a plain array is unrolled into separate arguments.
$AllProfiles = @(
    "--profile", "airflow",
    "--profile", "airflow-run",
    "--profile", "dagster",
    "--profile", "dagster-run",
    "--profile", "docs",
    "--profile", "prefect",
    "--profile", "prefect-run",
    "--profile", "kestra",
    "--profile", "kestra-run",
    "--profile", "verify"
)

function Show-Help {
    @'
Usage: .\scripts\demo.ps1 <command> [-NoWait]

  up         Airflow + Dagster + dbt docs together (needs ~6 GB Docker RAM)
  airflow    Only Airflow            http://localhost:8080  (admin/admin)
  dagster    Only Dagster            http://localhost:3000
  prefect    Only Prefect            http://localhost:4200
  kestra     Only Kestra             http://localhost:8082
  docs       Only dbt docs           http://localhost:8081
  tour       Each orchestrator one at a time (the 8 GB RAM path)
  status     Show demo containers
  logs       Follow logs of running demo containers
  down       Stop every demo stack
  clean      Stop every stack and delete volumes and generated files

Options:
  -NoWait    In "tour", do not pause for Enter between tools

Every product keeps its own host port, so nothing is reused:
  Airflow 8080 | Dagster 3000 | dbt docs 8081 | Prefect 4200 | Kestra 8082
'@ | Write-Host
}

function Assert-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker is required. Install Docker Desktop, then rerun this script."
    }
    docker compose version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose v2 is required (docker compose)."
    }
}

function Invoke-Docker {
    param([Parameter(Mandatory)][string[]]$Arguments,
          [string]$FailureMessage = "docker command failed")

    & docker @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage (exit code $LASTEXITCODE)"
    }
}

function Stop-AllStacks {
    param([switch]$RemoveVolumes)

    $arguments = @("compose") + $AllProfiles + @("down", "--remove-orphans")
    if ($RemoveVolumes) { $arguments += "--volumes" }
    & docker @arguments | Out-Null
}

function Show-Urls([string]$Tool) {
    switch ($Tool) {
        "airflow" { Write-Host "Airflow:  http://localhost:8080  (admin/admin)"; break }
        "dagster" { Write-Host "Dagster:  http://localhost:3000"; break }
        "prefect" { Write-Host "Prefect:  http://localhost:4200"; break }
        "kestra"  { Write-Host "Kestra:   http://localhost:8082"; break }
        "docs"    { Write-Host "dbt Docs: http://localhost:8081"; break }
        "up" {
            Write-Host "Airflow:  http://localhost:8080  (admin/admin)"
            Write-Host "Dagster:  http://localhost:3000"
            Write-Host "dbt Docs: http://localhost:8081"
            break
        }
    }
}

# Compose starts each *-run service's dependencies and waits for their
# healthchecks, so the script never polls for readiness itself.
function Start-Stack([string]$Tool) {
    switch ($Tool) {
        "airflow" {
            Invoke-Docker -Arguments @("compose", "--profile", "airflow", "--profile", "airflow-run",
                "run", "--rm", "--build", "airflow-run") -FailureMessage "Airflow pipeline run failed"
            break
        }
        "dagster" {
            Invoke-Docker -Arguments @("compose", "--profile", "dagster", "--profile", "dagster-run",
                "run", "--rm", "--build", "dagster-run") -FailureMessage "Dagster pipeline run failed"
            break
        }
        "prefect" {
            Invoke-Docker -Arguments @("compose", "--profile", "prefect", "--profile", "prefect-run",
                "run", "--rm", "--build", "prefect-run") -FailureMessage "Prefect pipeline run failed"
            break
        }
        "kestra" {
            Invoke-Docker -Arguments @("compose", "--profile", "kestra", "--profile", "kestra-run",
                "run", "--rm", "--build", "kestra-run") -FailureMessage "Kestra pipeline run failed"
            break
        }
        "docs" {
            Invoke-Docker -Arguments @("compose", "--profile", "docs",
                "up", "--build", "--detach", "--wait", "--wait-timeout", "600",
                "dbt-docs") -FailureMessage "Failed to start dbt docs"
            break
        }
        default { throw "Unknown stack: $Tool" }
    }
}

function Wait-ForNextTool([string]$Tool) {
    if ($NoWait) { return }
    if (-not [Environment]::UserInteractive) {
        Write-Host "Not interactive; continuing without a pause after $Tool."
        return
    }
    Read-Host "Press Enter to stop $Tool and continue to the next tool" | Out-Null
}

if ($Command -eq "help") {
    Show-Help
    return
}

Push-Location $Root
try {
    Assert-Docker
    New-Item -ItemType Directory -Force -Path "data" | Out-Null

    switch ($Command) {
        "up" {
            Stop-AllStacks
            Invoke-Docker -Arguments @("compose", "--profile", "airflow", "--profile", "dagster",
                "--profile", "verify", "run", "--rm", "--build", "bootstrap") `
                -FailureMessage "Airflow/Dagster bootstrap run failed"
            Invoke-Docker -Arguments @("compose", "--profile", "docs",
                "up", "--build", "--detach", "--wait", "--wait-timeout", "600", "dbt-docs") `
                -FailureMessage "Failed to start dbt docs"
            Write-Host ""
            Show-Urls "up"
            Write-Host "Summary files are in .\data (each total is 612.00)."
            Write-Host "On an 8 GB machine use: .\scripts\demo.ps1 tour"
            break
        }
        { $_ -in @("airflow", "dagster", "prefect", "kestra", "docs") } {
            Stop-AllStacks
            Start-Stack $Command
            Write-Host ""
            Show-Urls $Command
            if ($Command -ne "docs") {
                Write-Host "Summary file: .\data\$Command-summary.json"
            }
            Write-Host "Stop it with: .\scripts\demo.ps1 down"
            break
        }
        "tour" {
            Stop-AllStacks
            foreach ($tool in @("airflow", "dagster", "prefect", "kestra")) {
                Write-Host ""
                Write-Host "=============================================="
                Write-Host " $tool"
                Write-Host "=============================================="
                Start-Stack $tool
                Write-Host ""
                Show-Urls $tool
                Wait-ForNextTool $tool
                Stop-AllStacks
            }
            Write-Host ""
            Write-Host "Tour finished. Only one stack ran at a time."
            Write-Host "Summary files left in .\data:"
            Write-Host "  airflow-summary.json  dagster-summary.json"
            Write-Host "  prefect-summary.json  kestra-summary.json"
            break
        }
        "status" {
            & docker @(@("compose") + $AllProfiles + @("ps"))
            break
        }
        "logs" {
            & docker @(@("compose") + $AllProfiles + @("logs", "--follow"))
            break
        }
        "down" {
            Stop-AllStacks
            Write-Host "All demo stacks stopped."
            break
        }
        "clean" {
            Stop-AllStacks -RemoveVolumes
            Remove-Item "data\*.duckdb", "data\*-summary.json", "data\dagster-revenue-*.json" `
                -Force -ErrorAction SilentlyContinue
            Write-Host "Removed containers, volumes, DuckDB files, and summaries."
            break
        }
    }
}
finally {
    Pop-Location
}
