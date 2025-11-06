@echo off
REM 執行資料庫遷移 - 新增截圖欄位
echo ========================================
echo 資料庫遷移: 新增車輛截圖功能
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
echo [+] 執行遷移腳本...
echo.
python database\migrate_add_snapshot.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 遷移成功完成！
    echo ========================================
    echo.
    echo 現在可以重新啟動 web_server.py
    echo 車牌辨識時會自動儲存車輛截圖
) else (
    echo.
    echo ========================================
    echo 遷移失敗！
    echo ========================================
    echo 請檢查錯誤訊息
)

echo.
pause
