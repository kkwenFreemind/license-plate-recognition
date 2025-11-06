@echo off
REM 修正資料庫時區問題

echo ========================================
echo 資料庫時區修正工具
echo ========================================
echo.

REM 切換到專案目錄
cd /d "%~dp0.."

REM 啟動虛擬環境並執行腳本
call venv\Scripts\activate.bat
python database\fix_timezone.py

echo.
pause
