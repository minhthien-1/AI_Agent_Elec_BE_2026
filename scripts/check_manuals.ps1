$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ManualRoot = Join-Path $ProjectRoot 'data\manuals'

$relativePaths = @(
    'files\manuals\washing_machines\M001_samsung_WA14CG5886BDSV_manual_vi.pdf',
    'files\manuals\refrigerators\M002_lg_LFD58BLMA_manual_vi.pdf',
    'files\manuals\refrigerators\M003_lg_F51EG_manual_vi.pdf',
    'files\manuals\refrigerators\M004_lg_LTB26SVM_manual_vi.pdf',
    'files\manuals\air_conditioners\M005_lg_IDC09M1N_manual_vi.pdf',
    'files\manuals\freezers\M006_lg_LOF16BGM_manual_vi.pdf',
    'files\manuals\refrigerators\M007_lg_LFD61BLGA_quick_setup_vi.pdf',
    'files\manuals\refrigerators\M008_lg_GN-D392BLA_manual_vi.pdf',
    'files\manuals\washing_machines\M009_lg_FB1209D5W_manual_vi.pdf',
    'files\technical_guides\G001_panasonic_fridge_usage_guide.pdf',
    'files\warranty\W001_panasonic_warranty_period_2026.pdf',
    'files\warranty\W002_panasonic_warranty_terms.pdf',
    'files\technical_guides\T001_toshiba_washer_noise.pdf',
    'files\technical_guides\T002_toshiba_washer_maintenance.pdf',
    'files\technical_guides\T003_toshiba_fridge_noise.pdf',
    'files\technical_guides\T004_toshiba_fridge_maintenance.pdf',
    'files\technical_guides\T005_toshiba_fridge_not_working.pdf',
    'files\technical_guides\T006_toshiba_ac_normal_behaviors.pdf',
    'files\technical_guides\T007_toshiba_ac_maintenance.pdf',
    'files\technical_guides\T008_ariston_water_heater_maintenance.pdf',
    'files\technical_guides\T009_ariston_water_heater_not_heating.pdf',
    'files\technical_guides\T010_ariston_water_heater_overheating.pdf',
    'files\technical_guides\T011_ariston_instant_heater_safety.pdf',
    'files\technical_guides\T012_ariston_water_heater_common_faults.pdf',
    'files\technical_guides\T013_ariston_solar_heater_maintenance.pdf',
    'files\safety\S001_evn_home_electrical_overload.pdf',
    'files\safety\S002_evn_home_electrical_safety.pdf',
    'files\safety\S003_evn_warning_signs_electrical_danger.pdf',
    'files\safety\S004_evn_electrical_safety_away_from_home.pdf',
    'files\safety\S005_evn_safe_electricity_responsibility.pdf'
)

$results = foreach ($relativePath in $relativePaths) {
    $fullPath = Join-Path $ManualRoot $relativePath

    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        [PSCustomObject]@{
            Status = 'MISSING'
            SizeKB = 0
            RelativePath = $relativePath
            Note = 'Chua tai hoac luu sai ten/thu muc'
        }
        continue
    }

    $item = Get-Item -LiteralPath $fullPath
    $stream = [System.IO.File]::OpenRead($fullPath)
    try {
        $buffer = New-Object byte[] 5
        $bytesRead = $stream.Read($buffer, 0, 5)
        $signature = [System.Text.Encoding]::ASCII.GetString($buffer, 0, $bytesRead)
    }
    finally {
        $stream.Dispose()
    }

    if ($signature -ne '%PDF-') {
        [PSCustomObject]@{
            Status = 'NOT_PDF'
            SizeKB = [math]::Round($item.Length / 1KB, 1)
            RelativePath = $relativePath
            Note = 'File khong co chu ky PDF; kiem tra file tai xuong'
        }
    }
    elseif ($item.Length -lt 10240) {
        [PSCustomObject]@{
            Status = 'REVIEW_SMALL'
            SizeKB = [math]::Round($item.Length / 1KB, 1)
            RelativePath = $relativePath
            Note = 'PDF nho hon 10 KB; mo file kiem tra noi dung'
        }
    }
    else {
        [PSCustomObject]@{
            Status = 'PDF_OK'
            SizeKB = [math]::Round($item.Length / 1KB, 1)
            RelativePath = $relativePath
            Note = 'PDF signature OK; van can mo file va review model/noi dung'
        }
    }
}

$results | Format-Table -AutoSize -Wrap

$present = @($results | Where-Object { $_.Status -ne 'MISSING' }).Count
$validPdf = @($results | Where-Object { $_.Status -in @('PDF_OK', 'REVIEW_SMALL') }).Count
$missing = @($results | Where-Object { $_.Status -eq 'MISSING' }).Count
$notPdf = @($results | Where-Object { $_.Status -eq 'NOT_PDF' }).Count

Write-Host ""
Write-Host "Expected files: $($relativePaths.Count)"
Write-Host "Files present:  $present"
Write-Host "PDF signature:  $validPdf"
Write-Host "Missing:        $missing"
Write-Host "Not PDF:        $notPdf"
Write-Host ""
Write-Host 'IMPORTANT: PDF signature check does not validate title, brand/model, language, completeness, or safety.'
