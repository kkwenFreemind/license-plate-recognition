# 快速啟動腳本
# 自動啟動虛擬環境並執行程式

Write-Host "啟動車牌辨識系統..." -ForegroundColor Cyan

# 啟動虛擬環境
& .\venv\Scripts\Activate.ps1

# 執行主程式
python main.py
