@echo off
chcp 65001 >nul
cls
echo ========================================
echo 驗證系統安裝
echo ========================================
echo.

REM 檢查虛擬環境
if not exist "venv\Scripts\activate.bat" (
    echo [錯誤] 虛擬環境不存在！
    echo 請先執行: install.bat
    pause
    exit /b 1
)

echo 啟動虛擬環境...
call venv\Scripts\activate.bat

echo.
echo 執行驗證...
python tests\verify_installation.py

echo.
pause
