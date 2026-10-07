param(
    [string]$Requirements = 'requirements.resolved.txt',
    [string]$OutputDirectory = 'docs/security/evidence'
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$packages = @()
$failures = @()
foreach ($line in Get-Content -LiteralPath $Requirements) {
    if ($line -notmatch '^([A-Za-z0-9_.-]+)==([^\s;]+)$') { continue }
    $packageName = $Matches[1]
    $packageVersion = $Matches[2]
    try {
        $packageInfo = Invoke-RestMethod -Uri "https://pypi.org/pypi/$packageName/$packageVersion/json" -TimeoutSec 30
        $packages += [ordered]@{ name = $packageName; version = $packageVersion; vulnerabilities = @($packageInfo.vulnerabilities) }
    } catch {
        $failures += $packageName
    }
}
$report = [ordered]@{
    generated_at = [DateTime]::UtcNow.ToString('o')
    source = 'https://pypi.org/pypi/{package}/{version}/json'
    tool = 'scripts/audit_dependencies.ps1 (PyPI release advisory API; TLS verified by PowerShell)'
    requirements_sha256 = (Get-FileHash -LiteralPath $Requirements -Algorithm SHA256).Hash.ToLower()
    dependencies = $packages
    failed_queries = $failures
    limitation = 'Known advisories published by PyPI; no guarantee of completeness or standardized severity. All unresolved advisories block release pending triage.'
}
$report | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $OutputDirectory 'sca-pypi.json')
$components = @($packages | ForEach-Object {
    [ordered]@{ type = 'library'; name = $_.name; version = $_.version; purl = "pkg:pypi/$($_.name)@$($_.version)"; 'bom-ref' = "pkg:pypi/$($_.name)@$($_.version)" }
})
$bom = [ordered]@{ bomFormat = 'CycloneDX'; specVersion = '1.5'; version = 1; metadata = @{ timestamp = $report.generated_at }; components = $components }
$bom | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $OutputDirectory 'sbom.cdx.json')
$affected = @($packages | Where-Object { $_.vulnerabilities.Count -gt 0 })
Write-Output "Queried=$($packages.Count) affected=$($affected.Count) failed=$($failures.Count)"
if ($failures.Count -gt 0) { exit 2 }
if ($affected.Count -gt 0) { exit 1 }
