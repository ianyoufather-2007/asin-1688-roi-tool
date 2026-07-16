$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $ProjectRoot
try {
    py -m pip install -e ".[browser,packaging]"
    py -m PyInstaller --noconfirm --clean --windowed `
      --name ASIN_1688_ROI `
      --paths src `
      --collect-all openpyxl `
      --collect-all xlsxwriter `
      src/asin_1688_roi/gui.py
    Write-Host "Build completed: dist/ASIN_1688_ROI/ASIN_1688_ROI.exe"
}
finally {
    Pop-Location
}
