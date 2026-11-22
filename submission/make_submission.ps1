# Builds the submission folder on the Desktop from this repository.
# Run from anywhere:
#   powershell -ExecutionPolicy Bypass -File submission\make_submission.ps1
# Add -WithSplits to also zip the generated client data (dataset\Cifar10, dataset\Cifar100).
param([switch]$WithSplits)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$out = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Fed-GDBD_Submission'

if (git status --porcelain --untracked-files=no) {
    Write-Warning 'You have uncommitted changes. 1_Source_Code only contains committed files.'
}
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
$dirs = '1_Source_Code','2_Dataset\split_scripts','3_Paper\Full_Version','4_Additional\Check_Reports'
foreach ($d in $dirs) { New-Item -ItemType Directory -Path (Join-Path $out $d) -Force | Out-Null }

Copy-Item submission\README.txt $out

# 1. Source code: only the code, run scripts, logs and the guides, taken from the
#    current commit (no paper, report, slides, .venv, caches or lock files)
$srcZip = Join-Path (Join-Path $out '1_Source_Code') 'Fed-GDBD-for-HtFL.zip'
$code = 'system','dataset','analysis','scripts','experiments','setup.bat','requirements.txt','LICENSE','.gitignore','README.md','REPRODUCTION.md','DATASET.md','PROTOCOL.md'
git archive --format=zip --prefix=Fed-GDBD-for-HtFL/ -o $srcZip HEAD -- @code
if ($LASTEXITCODE -ne 0) { throw 'git archive failed' }

# 2. Dataset
Copy-Item DATASET.md "$out\2_Dataset"
Copy-Item dataset\generate_Cifar10.py, dataset\generate_Cifar100.py, dataset\utils\dataset_utils.py "$out\2_Dataset\split_scripts"
foreach ($ds in 'Cifar10','Cifar100') {
    $cfg = "dataset\$ds\config.json"
    if (Test-Path $cfg) { Copy-Item $cfg "$out\2_Dataset\${ds}_config.json" }
    else { Write-Warning "$cfg not found. Run the generator once (see DATASET.md)." }
    if ($WithSplits) {
        if ((Test-Path "dataset\$ds\train") -and (Test-Path "dataset\$ds\test")) {
            Write-Host "Zipping $ds split (this can take a few minutes)..."
            Compress-Archive -Path "dataset\$ds\train","dataset\$ds\test",$cfg -DestinationPath "$out\2_Dataset\${ds}_split.zip"
        } else { Write-Warning "dataset\$ds\train or test not found, split not included." }
    }
}

# 3. Paper
Copy-Item docs\paper\Fed-GDBD_Paper_Draft.pdf "$out\3_Paper\Fed-GDBD_Paper.pdf"
Copy-Item docs\paper\Fed-GDBD_Paper_LaTeX.zip "$out\3_Paper"
Copy-Item docs\paper\full\Fed-GDBD_Paper_Full.pdf "$out\3_Paper\Full_Version"
Copy-Item docs\paper\full\Fed-GDBD_Paper_Full_LaTeX.zip "$out\3_Paper\Full_Version"

# 4. Additional documents
Copy-Item docs\report\Fed-GDBD_Project_Report.pdf, docs\report\Fed-GDBD_Project_Report_SoftCopy.pdf, docs\report\Fed-GDBD_Project_Report_SoftCopy.docx "$out\4_Additional"
Copy-Item docs\presentation\*.pptx "$out\4_Additional"

Write-Host ''
Write-Host "Done: $out"
Get-ChildItem $out -Recurse -File | ForEach-Object {
    '{0,10:N1} MB  {1}' -f ($_.Length / 1MB), $_.FullName.Substring($out.Length + 1)
}
$total = (Get-ChildItem $out -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
Write-Host ('Total: {0:N1} MB' -f $total)
Write-Host 'Put the plagiarism and AI-check reports into 4_Additional\Check_Reports, then zip the folder.'
