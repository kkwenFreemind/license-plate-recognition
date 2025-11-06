@echo off
chcp 65001 >nul
cls
echo ========================================
echo 車牌辨識系統 - 網頁展示模式
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

echo [1/3] 啟動虛擬環境...
call venv\Scripts\activate.bat

echo [2/3] 安裝網頁套件 (如果需要)...
pip install -q flask flask-socketio python-socketio eventlet

echo [3/3] 啟動網頁伺服器...
echo.
echo ========================================
echo 網頁伺服器啟動中...
echo 請在瀏覽器開啟: http://localhost:5000
echo 按 Ctrl+C 停止伺服器
echo ========================================
echo.

python web_server.py

echo.
echo ========================================
echo 伺服器已停止
echo ========================================
pause
