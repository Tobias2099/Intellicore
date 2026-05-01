Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Checking IntelliCore workspace scaffold..."

$requiredPaths = @(
    "apps/visual-stats/package.json",
    "services/control-plane/src/intellicore_control/cli.py",
    "services/training/src/intellicore_training/rewards.py",
    "sim/gem5-intellicore/CMakeLists.txt",
    "infra/db/migrations/001_initial_schema.sql",
    "packages/contracts/schemas/telemetry-event.schema.json"
)

foreach ($path in $requiredPaths) {
    if (-not (Test-Path $path)) {
        throw "Missing required path: $path"
    }
}

Write-Host "Workspace scaffold looks complete."
