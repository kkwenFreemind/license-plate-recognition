# License Plate Recognition System - 安裝腳本
# Windows PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "License Plate Recognition System" -ForegroundColor Cyan
Write-Host "安裝精靈" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 檢查 Python
Write-Host "`n[1/6] 檢查 Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python 未安裝" -ForegroundColor Red
    Write-Host "請先安裝 Python 3.8 或以上版本" -ForegroundColor Red
    exit 1
}

# 建立虛擬環境
Write-Host "`n[2/6] 建立虛擬環境..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "虛擬環境已存在" -ForegroundColor Yellow
    $recreate = Read-Host "是否重新建立? (y/n)"
    if ($recreate -eq 'y') {
        Remove-Item -Recurse -Force venv
        python -m venv venv
        Write-Host "✓ 虛擬環境重新建立完成" -ForegroundColor Green
    }
} else {
    python -m venv venv
    Write-Host "✓ 虛擬環境建立完成" -ForegroundColor Green
}

# 啟動虛擬環境
Write-Host "`n[3/6] 啟動虛擬環境..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "✓ 虛擬環境已啟動" -ForegroundColor Green

# 升級 pip
Write-Host "`n[4/6] 升級 pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "✓ pip 升級完成" -ForegroundColor Green

# 安裝依賴套件
Write-Host "`n[5/6] 安裝依賴套件..." -ForegroundColor Yellow
Write-Host "這可能需要幾分鐘時間..." -ForegroundColor Gray

pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 依賴套件安裝完成" -ForegroundColor Green
} else {
    Write-Host "✗ 部分套件安裝失敗" -ForegroundColor Red
    Write-Host "請查看上方錯誤訊息" -ForegroundColor Red
}

# 設定配置檔案
Write-Host "`n[6/6] 設定配置檔案..." -ForegroundColor Yellow

if (-not (Test-Path "config\config.yaml")) {
    Copy-Item "config\config.example.yaml" "config\config.yaml"
    Write-Host "✓ 已建立 config\config.yaml" -ForegroundColor Green
} else {
    Write-Host "config\config.yaml 已存在" -ForegroundColor Yellow
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ 已建立 .env" -ForegroundColor Green
} else {
    Write-Host ".env 已存在" -ForegroundColor Yellow
}

# 完成
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✓ 安裝完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`n接下來請執行:" -ForegroundColor Yellow
Write-Host "  1. 編輯 .env 填入資料庫密碼" -ForegroundColor White
Write-Host "     notepad .env" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. 編輯 config\config.yaml 設定攝影機" -ForegroundColor White
Write-Host "     notepad config\config.yaml" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. 初始化資料庫" -ForegroundColor White
Write-Host "     python database\init_db.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. 驗證安裝" -ForegroundColor White
Write-Host "     python tests\verify_installation.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. 執行系統" -ForegroundColor White
Write-Host "     python main.py" -ForegroundColor Gray
Write-Host ""
