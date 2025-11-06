@echo off
chcp 65001 >nul
cls
echo ========================================
echo 安裝系統依賴
echo ========================================
echo.

REM 檢查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 找不到 Python！
    echo 請先安裝 Python 3.8 或以上版本
    pause
    exit /b 1
)

echo [1/4] 建立虛擬環境...
if not exist "venv" (
    python -m venv venv
    echo 虛擬環境建立完成
) else (
    echo 虛擬環境已存在
)

echo.
echo [2/4] 啟動虛擬環境...
call venv\Scripts\activate.bat

echo.
echo [3/4] 升級 pip...
python -m pip install --upgrade pip

echo.
echo [4/4] 安裝依賴套件...
pip install -r requirements.txt

echo.
echo ========================================
echo 安裝完成！
echo ========================================
echo.
echo 下一步：
echo   1. 複製配置檔案: copy config\config.example.yaml config\config.yaml
echo   2. 複製環境變數: copy .env.example .env
echo   3. 編輯 .env 填入資料庫密碼
echo   4. 初始化資料庫: init_db.bat
echo   5. 執行系統: start.bat
echo.
pause
