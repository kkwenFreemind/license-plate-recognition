@echo off
chcp 65001 >nul
cls
echo ========================================
echo 初始化資料庫
echo ========================================
echo.

REM 檢查虛擬環境
if not exist "venv\Scripts\activate.bat" (
    echo [錯誤] 虛擬環境不存在！
    echo 請先執行: install.bat
    pause
    exit /b 1
)

REM 檢查配置檔案
if not exist "config\config.yaml" (
    echo [錯誤] config.yaml 不存在！
    echo 請執行: copy config\config.example.yaml config\config.yaml
    pause
    exit /b 1
)

if not exist ".env" (
    echo [錯誤] .env 不存在！
    echo 請執行: copy .env.example .env
    echo 然後編輯 .env 填入資料庫密碼
    pause
    exit /b 1
)

echo [1/2] 啟動虛擬環境...
call venv\Scripts\activate.bat

echo.
echo [2/2] 初始化資料庫...
python database\init_db.py

echo.
pause
