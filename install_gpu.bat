@echo off
chcp 65001 >nul
cls
echo ========================================
echo 安裝 GPU 版本 PyTorch
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
echo [1/3] 卸載 CPU 版本 PyTorch...
pip uninstall torch torchvision -y

echo.
echo [2/3] 安裝 CUDA 11.8 版本...
echo 下載大小約 2.8 GB，請耐心等待...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

echo.
echo [3/3] 驗證 CUDA...
python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"

echo.
echo ========================================
echo 完成！
echo ========================================
echo.
echo 請確認：
echo   1. 顯示 "CUDA Available: True"
echo   2. 顯示您的 GPU 名稱
echo.
echo 如果 CUDA 可用，請修改 config.yaml：
echo   yolo.device: "cuda:0"
echo   modules.license_plate.gpu: true
echo.
pause
