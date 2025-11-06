@echo off
chcp 65001 >nul
echo ========================================
echo    互動式圍籬區域選取工具
echo ========================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [錯誤] 找不到虛擬環境
    echo 請先執行 install.bat 安裝相依套件
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo [提示] 正在啟動圍籬選取工具...
echo.
echo 操作說明：
echo   • 左鍵點擊：選取圍籬多邊形的頂點
echo   • 右鍵點擊：完成選取（至少需要3個點）
echo   • 按 R 鍵：重置所有點，重新選取
echo   • 按 S 鍵：儲存當前圍籬配置
echo   • 按 ESC 鍵：取消並退出
echo.
echo ========================================
echo.

python create_fence.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [錯誤] 工具執行失敗
    pause
    exit /b 1
)

echo.
echo ========================================
echo.
echo [完成] 圍籬配置已更新
echo.
set /p restart="是否要重新啟動 Web 伺服器？(Y/N): "
if /i "%restart%"=="Y" (
    echo.
    echo [提示] 正在重啟伺服器...
    call start_web.bat
) else (
    echo.
    echo [提示] 請手動執行 start_web.bat 重啟伺服器
)

pause
