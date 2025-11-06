@echo off
REM 啟動停留時間偵測範例
echo ========================================
echo 停留時間偵測範例
echo ========================================
echo.
echo 此範例將展示：
echo - 物件進入禁區後的停留時間追蹤
echo - 達到 3 秒後觸發警報
echo - 即時顯示停留時間和進度條
echo.
echo 請確保：
echo 1. 已安裝所有依賴套件
echo 2. 攝影機已連接或準備好測試影片
echo 3. YOLOv8 模型檔案 (yolov8n.pt) 已下載
echo.
pause

REM 檢查虛擬環境
if exist venv\Scripts\activate.bat (
    echo [+] 啟動虛擬環境...
    call venv\Scripts\activate.bat
) else (
    echo [!] 警告: 未找到虛擬環境
)

echo.
echo [+] 啟動範例程式...
echo [!] 按 'q' 可結束程式
echo.
python examples\dwell_time_example.py

echo.
echo ========================================
echo 程式已結束
echo ========================================
pause
