@echo off
chcp 65001 >nul
cls
echo ========================================
echo 車牌辨識系統 - 快速啟動
echo ========================================
echo.

REM 檢查虛擬環境是否存在
if not exist "venv\Scripts\activate.bat" (
    echo [錯誤] 虛擬環境不存在！
    echo 請先執行: python -m venv venv
    echo.
    pause
    exit /b 1
)

echo [1/2] 啟動虛擬環境...
call venv\Scripts\activate.bat

echo [2/2] 執行系統...
echo.
echo ========================================
echo 系統運行中...
echo 按 Ctrl+C 停止系統
echo ========================================
echo.

python main.py

echo.
echo ========================================
echo 系統已停止
echo ========================================
pause
