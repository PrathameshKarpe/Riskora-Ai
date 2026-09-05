$env:DATABASE_URL = "postgresql+psycopg://riskora:riskora@localhost:5433/riskora"
$env:ENVIRONMENT  = "development"

$venv = Join-Path $PSScriptRoot ".." ".venv\Scripts"
$pytest = Join-Path $venv "pytest.exe"

Write-Host ""
Write-Host "================================================================"
Write-Host "UNIT TESTS (Phase 1-3, no database)"
Write-Host "================================================================"
& $pytest tests/test_features.py tests/test_inference.py tests/test_risk_engine.py tests/test_rag.py tests/test_agents.py -v --tb=short
$unit_exit = $LASTEXITCODE

Write-Host ""
Write-Host "================================================================"
Write-Host "WORKFLOW / DEMO-SCENARIO TESTS (no database)"
Write-Host "================================================================"
& $pytest tests/test_workflow.py tests/test_demo_scenarios.py -v --tb=short
$workflow_exit = $LASTEXITCODE

Write-Host ""
Write-Host "================================================================"
Write-Host "API TESTS (SQLite, TestClient)"
Write-Host "================================================================"
& $pytest apps/api/tests/test_api.py -v --tb=short
$api_exit = $LASTEXITCODE

Write-Host ""
Write-Host "================================================================"
Write-Host "POSTGRESQL INTEGRATION TESTS"
Write-Host "================================================================"
& $pytest tests/test_pg_integration.py -v --tb=short
$pg_exit = $LASTEXITCODE

Write-Host ""
Write-Host "================================================================"
Write-Host "RESULTS"
Write-Host "================================================================"
Write-Host "Unit tests:          exit $unit_exit"
Write-Host "Workflow tests:      exit $workflow_exit"
Write-Host "API tests (SQLite):  exit $api_exit"
Write-Host "PG integration:      exit $pg_exit"

if (($unit_exit -eq 0) -and ($workflow_exit -eq 0) -and ($api_exit -eq 0) -and ($pg_exit -eq 0)) {
    Write-Host "ALL SUITES PASSED"
    exit 0
} else {
    Write-Host "ONE OR MORE SUITES FAILED"
    exit 1
}
