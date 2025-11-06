"""
網頁版互動式圍籬選取工具
使用方法：python create_fence_web.py
然後開啟瀏覽器: http://localhost:5001
"""

from flask import Flask, render_template_string, request, jsonify
import cv2
import yaml
import base64
import numpy as np
from pathlib import Path
import threading
import time

app = Flask(__name__)

# 全域變數
current_frame = None
config = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>電子圍籬區域選取工具</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 20px;
        }
        
        .canvas-section {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .canvas-wrapper {
            position: relative;
            display: inline-block;
            border: 3px solid #667eea;
            border-radius: 8px;
            overflow: hidden;
        }
        
        #fenceCanvas {
            display: block;
            cursor: crosshair;
            max-width: 100%;
        }
        
        .control-panel {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .section {
            margin-bottom: 25px;
        }
        
        .section h3 {
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .instructions {
            background: #f8f9ff;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .instructions p {
            color: #333;
            line-height: 1.6;
            margin-bottom: 8px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            color: #333;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-group small {
            color: #666;
            font-size: 12px;
        }
        
        .button-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 20px;
        }
        
        .btn {
            padding: 12px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
        }
        
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        
        .btn-danger {
            background: #ff4757;
            color: white;
            grid-column: span 2;
        }
        
        .btn-danger:hover {
            background: #ff3838;
        }
        
        .btn-success {
            background: #2ecc71;
            color: white;
            grid-column: span 2;
        }
        
        .btn-success:hover {
            background: #27ae60;
        }
        
        .stats {
            background: #f8f9ff;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stats h4 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .stats p {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        
        .alert {
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 15px;
            display: none;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeeba;
        }
        
        @media (max-width: 1200px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 電子圍籬區域選取工具</h1>
            <p>在影像上點擊選取圍籬區域</p>
        </div>
        
        <div class="main-content">
            <div class="canvas-section">
                <div class="canvas-wrapper">
                    <canvas id="fenceCanvas"></canvas>
                </div>
            </div>
            
            <div class="control-panel">
                <div class="section">
                    <h3>📋 操作說明</h3>
                    <div class="instructions">
                        <p>🖱️ <strong>左鍵點擊</strong>：選取頂點</p>
                        <p>✅ <strong>右鍵點擊</strong>：完成選取</p>
                        <p>🔄 <strong>重置按鈕</strong>：清除所有點</p>
                    </div>
                </div>
                
                <div class="section">
                    <div class="stats">
                        <h4>已選取點數</h4>
                        <p id="pointCount">0</p>
                    </div>
                </div>
                
                <div class="alert alert-warning" id="alertBox"></div>
                
                <div class="section">
                    <h3>⚙️ 圍籬設定</h3>
                    <div class="form-group">
                        <label for="fenceId">圍籬 ID *</label>
                        <input type="text" id="fenceId" placeholder="例如: fence_001" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="fenceName">圍籬名稱 *</label>
                        <input type="text" id="fenceName" placeholder="例如: 人員禁入區" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="targetClasses">目標類型</label>
                        <input type="text" id="targetClasses" placeholder="例如: person,car (用逗號分隔)">
                        <small>留空表示偵測所有類型</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="minConfidence">最小信心度 (0.0-1.0)</label>
                        <input type="number" id="minConfidence" min="0" max="1" step="0.1" value="0.6">
                    </div>
                </div>
                
                <div class="button-group">
                    <button class="btn btn-secondary" onclick="resetPoints()">🔄 重置</button>
                    <button class="btn btn-primary" onclick="completeSelection()">✅ 完成</button>
                    <button class="btn btn-success" onclick="saveFence()">💾 儲存配置</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const canvas = document.getElementById('fenceCanvas');
        const ctx = canvas.getContext('2d');
        let points = [];
        let completed = false;
        let imageData = null;
        
        // 載入影像
        fetch('/get_frame')
            .then(response => response.json())
            .then(data => {
                const img = new Image();
                img.onload = function() {
                    // 設定 canvas 大小為影像大小
                    const maxWidth = 900;
                    const scale = Math.min(1, maxWidth / img.width);
                    canvas.width = img.width * scale;
                    canvas.height = img.height * scale;
                    
                    // 儲存縮放比例
                    canvas.dataset.scale = scale;
                    canvas.dataset.originalWidth = img.width;
                    canvas.dataset.originalHeight = img.height;
                    
                    // 繪製影像
                    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                };
                img.src = 'data:image/jpeg;base64,' + data.frame;
            })
            .catch(error => {
                showAlert('無法載入影像: ' + error, 'error');
            });
        
        // 滑鼠事件
        canvas.addEventListener('click', function(e) {
            if (completed) {
                showAlert('已完成選取，請點擊「儲存配置」或「重置」', 'warning');
                return;
            }
            
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            points.push({x, y});
            updatePointCount();
            drawFence();
        });
        
        canvas.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            completeSelection();
        });
        
        canvas.addEventListener('mousemove', function(e) {
            if (completed || points.length === 0) return;
            
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            // 重繪
            ctx.putImageData(imageData, 0, 0);
            drawFence();
            
            // 繪製預覽線
            ctx.strokeStyle = '#ffff00';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(points[points.length - 1].x, points[points.length - 1].y);
            ctx.lineTo(x, y);
            ctx.stroke();
        });
        
        function drawFence() {
            if (points.length === 0) return;
            
            // 繪製點
            points.forEach((point, i) => {
                ctx.fillStyle = '#00ff00';
                ctx.beginPath();
                ctx.arc(point.x, point.y, 5, 0, Math.PI * 2);
                ctx.fill();
                
                // 繪製編號
                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 14px Arial';
                ctx.fillText(i + 1, point.x + 10, point.y - 10);
            });
            
            // 繪製線
            if (points.length > 1) {
                ctx.strokeStyle = '#00ff00';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(points[0].x, points[0].y);
                for (let i = 1; i < points.length; i++) {
                    ctx.lineTo(points[i].x, points[i].y);
                }
                ctx.stroke();
            }
            
            // 如果已完成，繪製多邊形
            if (completed && points.length >= 3) {
                // 填充
                ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
                ctx.beginPath();
                ctx.moveTo(points[0].x, points[0].y);
                for (let i = 1; i < points.length; i++) {
                    ctx.lineTo(points[i].x, points[i].y);
                }
                ctx.closePath();
                ctx.fill();
                
                // 邊框
                ctx.strokeStyle = '#ff0000';
                ctx.lineWidth = 3;
                ctx.stroke();
                
                // 顯示完成標籤
                ctx.fillStyle = '#00ff00';
                ctx.font = 'bold 24px Arial';
                ctx.fillText('✓ COMPLETED', 10, 30);
            }
        }
        
        function resetPoints() {
            points = [];
            completed = false;
            if (imageData) {
                ctx.putImageData(imageData, 0, 0);
            }
            updatePointCount();
            hideAlert();
        }
        
        function completeSelection() {
            if (points.length < 3) {
                showAlert('至少需要 3 個點才能形成圍籬區域', 'warning');
                return;
            }
            
            completed = true;
            ctx.putImageData(imageData, 0, 0);
            drawFence();
            showAlert(`✓ 圍籬定義完成！共 ${points.length} 個點`, 'success');
        }
        
        function saveFence() {
            if (!completed) {
                showAlert('請先完成圍籬選取（右鍵點擊完成）', 'warning');
                return;
            }
            
            const fenceId = document.getElementById('fenceId').value.trim();
            const fenceName = document.getElementById('fenceName').value.trim();
            const targetClassesStr = document.getElementById('targetClasses').value.trim();
            const minConfidence = parseFloat(document.getElementById('minConfidence').value);
            
            if (!fenceId || !fenceName) {
                showAlert('請填寫圍籬 ID 和名稱', 'error');
                return;
            }
            
            const targetClasses = targetClassesStr ? targetClassesStr.split(',').map(s => s.trim()).filter(s => s) : [];
            
            // 轉換座標到原始影像尺寸
            const scale = parseFloat(canvas.dataset.scale);
            const originalPoints = points.map(p => [
                Math.round(p.x / scale),
                Math.round(p.y / scale)
            ]);
            
            const fenceData = {
                id: fenceId,
                name: fenceName,
                points: originalPoints,
                target_classes: targetClasses,
                min_confidence: minConfidence
            };
            
            // 發送到後端儲存
            fetch('/save_fence', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(fenceData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('✓ 配置已儲存！請重新啟動 web_server.py', 'success');
                    setTimeout(() => {
                        resetPoints();
                    }, 3000);
                } else {
                    showAlert('儲存失敗: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showAlert('儲存失敗: ' + error, 'error');
            });
        }
        
        function updatePointCount() {
            document.getElementById('pointCount').textContent = points.length;
        }
        
        function showAlert(message, type) {
            const alertBox = document.getElementById('alertBox');
            alertBox.textContent = message;
            alertBox.className = 'alert alert-' + type;
            alertBox.style.display = 'block';
        }
        
        function hideAlert() {
            document.getElementById('alertBox').style.display = 'none';
        }
    </script>
</body>
</html>
"""


def load_config():
    """載入現有配置"""
    config_path = Path("config/config.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return None


def capture_frame_from_rtsp(rtsp_url):
    """從 RTSP 擷取影像"""
    print(f"正在連接攝影機: {rtsp_url}")
    cap = cv2.VideoCapture(rtsp_url)
    
    if not cap.isOpened():
        print("❌ 無法連接到攝影機")
        return None
    
    # 讀取幾幀後再使用
    for _ in range(5):
        ret, frame = cap.read()
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret or frame is None:
        print("❌ 無法讀取影像")
        return None
    
    print(f"✓ 影像擷取成功 (尺寸: {frame.shape[1]} x {frame.shape[0]})")
    return frame


@app.route('/')
def index():
    """首頁"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/get_frame')
def get_frame():
    """取得當前影像"""
    if current_frame is None:
        return jsonify({'error': '無法取得影像'}), 500
    
    # 轉換為 JPEG
    _, buffer = cv2.imencode('.jpg', current_frame)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return jsonify({'frame': frame_base64})


@app.route('/save_fence', methods=['POST'])
def save_fence():
    """儲存圍籬配置"""
    try:
        fence_data = request.json
        
        # 更新配置
        if 'virtual_fences' not in config:
            config['virtual_fences'] = {
                'enabled': True,
                'fences': []
            }
        
        if 'fences' not in config['virtual_fences']:
            config['virtual_fences']['fences'] = []
        
        # 建立新圍籬
        new_fence = {
            'id': fence_data['id'],
            'name': fence_data['name'],
            'points': fence_data['points'],
            'target_classes': fence_data['target_classes'],
            'min_confidence': fence_data['min_confidence'],
            'enabled': True
        }
        
        # 檢查是否已存在
        existing_index = None
        for i, fence in enumerate(config['virtual_fences']['fences']):
            if fence.get('id') == fence_data['id']:
                existing_index = i
                break
        
        if existing_index is not None:
            config['virtual_fences']['fences'][existing_index] = new_fence
            print(f"✓ 已更新圍籬: {fence_data['id']}")
        else:
            config['virtual_fences']['fences'].append(new_fence)
            print(f"✓ 已新增圍籬: {fence_data['id']}")
        
        # 儲存配置
        config_path = Path("config/config.yaml")
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        print(f"✓ 配置已儲存至: {config_path}")
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"❌ 儲存失敗: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def main():
    """主程式"""
    global current_frame, config
    
    # 載入配置
    config = load_config()
    if not config:
        print("❌ 找不到配置檔案 config/config.yaml")
        return
    
    # 取得 RTSP URL
    rtsp_url = None
    
    if 'camera' in config:
        rtsp_url = config['camera'].get('rtsp_url')
    
    if not rtsp_url and 'cameras' in config:
        for camera in config['cameras']:
            if camera.get('enabled', True):
                rtsp_url = camera.get('rtsp_url')
                camera_name = camera.get('name', '未命名')
                print(f"使用攝影機: {camera_name}")
                break
    
    if not rtsp_url:
        print("❌ 配置檔案中找不到 RTSP URL")
        return
    
    # 擷取影像
    current_frame = capture_frame_from_rtsp(rtsp_url)
    if current_frame is None:
        return
    
    # 啟動 Web 伺服器
    print("\n" + "="*60)
    print("網頁版圍籬選取工具已啟動")
    print("="*60)
    print("請開啟瀏覽器: http://localhost:5001")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 已中斷")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
