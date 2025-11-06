@echo off
chcp 65001 >nul
echo ========================================
echo   網頁展示伺服器 (除錯模式)
echo ========================================
echo.

echo [1/3] 啟動虛擬環境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 虛擬環境啟動失敗！
    pause
    exit /b 1
)
echo ✓ 虛擬環境已啟動
echo.

echo [2/3] 檢查 Flask 套件...
python -c "import flask; import flask_socketio; print('✓ Flask 套件已安裝')" 2>nul
if errorlevel 1 (
    echo ⚠ Flask 套件未安裝，正在安裝...
    pip install flask flask-socketio python-socketio eventlet
)
echo.

echo [3/3] 啟動網頁伺服器...
echo.
echo ========================================
echo   伺服器位址: http://localhost:5000
echo   按 Ctrl+C 停止伺服器
echo ========================================
echo.

python web_server.py

pause
