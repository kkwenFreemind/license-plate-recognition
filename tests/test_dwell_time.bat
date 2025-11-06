@echo off
REM 停留時間功能測試腳本
echo ========================================
echo 電子圍籬停留時間功能測試
echo ========================================
echo.

REM 檢查虛擬環境
if exist venv\Scripts\activate.bat (
    echo [+] 啟動虛擬環境...
    call venv\Scripts\activate.bat
) else (
    echo [!] 警告: 未找到虛擬環境
)

echo.
echo [+] 執行測試...
echo.
python tests\test_dwell_time.py

echo.
echo ========================================
echo 測試完成
echo ========================================
pause
