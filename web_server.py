"""網頁展示伺服器 - Flask + WebSocket"""

import os
import sys
import cv2
import json
import base64
import time
import threading
import yaml
from pathlib import Path
from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
from datetime import datetime
from queue import Queue, Empty

# 加入專案路徑
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_manager import ConfigManager
from utils.logger import setup_logger
from core.system import MultiModalRecognitionSystem
from modules.license_plate import LicensePlateRecognizer
from modules.virtual_fence import VirtualFenceManager
from database.handler import DatabaseHandler

# 初始化 Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, 
                    cors_allowed_origins="*",
                    async_mode='threading',  # 使用 threading 模式
                    logger=True,
                    engineio_logger=True)

# 全域變數
frame_queue = Queue(maxsize=2)
detection_queue = Queue(maxsize=100)
latest_frame = None
system = None
config = None
logger = None
db_handler = None  # 資料庫處理器
fence_manager = None  # 電子圍籬管理器


def init_system():
    """初始化辨識系統"""
    global system, config, logger, db_handler, fence_manager
    
    # 載入配置
    config = ConfigManager('config/config.yaml')
    logger = setup_logger('WebServer', config.get_logging_config())
    logger.info("網頁伺服器啟動中...")
    
    # 初始化資料庫
    db_config = config.get('database', {})
    if db_config.get('enabled', True):
        try:
            db_handler = DatabaseHandler(db_config, logger)
            logger.info("✓ 資料庫連接成功")
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            logger.warning("系統將在沒有資料庫的情況下運行")
            db_handler = None
    else:
        db_handler = None
        logger.info("資料庫功能已停用")
    
    # 初始化電子圍籬
    fence_config = config.get('virtual_fences', {})
    if fence_config.get('enabled', False):
        fence_manager = VirtualFenceManager(logger)
        fence_manager.load_fences_from_config(fence_config)
        
        # 註冊入侵事件回調
        def on_intrusion(event):
            logger.warning(f"🚨 電子圍籬警報: {event['fence_name']} - {event['object_class']}")
            # 透過 WebSocket 發送警報到前端
            socketio.emit('fence_intrusion', event, namespace='/detections')
        
        fence_manager.register_intrusion_callback(on_intrusion)
        logger.info("✓ 電子圍籬功能已啟用")
    else:
        fence_manager = None
        logger.info("電子圍籬功能已停用")
    
    # 初始化系統
    system = MultiModalRecognitionSystem(config.config, logger)
    
    # 註冊車牌辨識模組
    plate_config = config.get_module_config('license_plate')
    if plate_config.get('enabled', True):
        plate_recognizer = LicensePlateRecognizer(plate_config, logger)
        system.register_recognizer(plate_recognizer)
    
    logger.info("✓ 系統初始化完成")


def process_camera():
    """處理攝影機串流"""
    global latest_frame
    
    cameras = config.get_enabled_cameras()
    if not cameras:
        logger.error("沒有啟用的攝影機!")
        return
    
    cam = cameras[0]  # 使用第一個攝影機
    rtsp_url = cam['rtsp_url']
    camera_id = cam['id']
    
    logger.info(f"連接攝影機: {rtsp_url}")
    cap = cv2.VideoCapture(rtsp_url)
    
    if not cap.isOpened():
        logger.error("無法連接 RTSP")
        return
    
    logger.info("✓ RTSP 連接成功")
    
    frame_count = 0
    conf_threshold = config.config.get('yolo', {}).get('confidence_threshold', 0.5)
    process_interval = cam.get('process_interval', 2.0)
    last_process_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            logger.warning("讀取幀失敗，嘗試重新連接...")
            cap.release()
            cap = cv2.VideoCapture(rtsp_url)
            continue
        
        frame_count += 1
        current_time = time.time()
        
        # 使用時間間隔而不是幀數
        if current_time - last_process_time >= process_interval:
            logger.debug(f"處理第 {frame_count} 幀...")
            
            # 執行辨識
            results = system.process_image(frame, conf_threshold)
            logger.info(f"偵測到 {len(results)} 個物件")
            
            # 繪製框選結果
            annotated_frame = draw_detections(frame.copy(), results)
            
            # 檢查電子圍籬入侵
            if fence_manager and results:
                # 提取基本偵測資訊
                detections = [r['base_detection'] for r in results]
                intrusions = fence_manager.check_detections(detections)
                
                if intrusions:
                    logger.warning(f"🚨 偵測到 {len(intrusions)} 個電子圍籬入侵事件")
                    
                    # 儲存入侵事件（包含截圖）
                    for intrusion in intrusions:
                        # 擷取當前影像並轉成 base64
                        _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        snapshot_base64 = base64.b64encode(buffer).decode('utf-8')
                        
                        # 準備儲存資料
                        intrusion_data = {
                            'fence_id': intrusion['fence_id'],
                            'fence_name': intrusion['fence_name'],
                            'object_class': intrusion['object_class'],
                            'confidence': intrusion['confidence'],
                            'bbox': intrusion['bbox'],
                            'camera_id': camera_id,
                            'camera_name': cam.get('name', '未命名'),
                            'snapshot_base64': snapshot_base64,
                            'timestamp': intrusion['timestamp']
                        }
                        
                        # 儲存到資料庫
                        if db_handler:
                            db_handler.save_fence_intrusion(intrusion_data)
                        
                        # 同時發送到前端（帶圖片）
                        socketio.emit('fence_intrusion', {
                            **intrusion,
                            'camera_name': cam.get('name', '未命名'),
                            'snapshot_base64': snapshot_base64
                        }, namespace='/detections')
            
            # 繪製電子圍籬
            if fence_manager:
                fence_manager.draw_all_fences(annotated_frame)
            
            latest_frame = annotated_frame
            
            # 發送辨識結果到前端
            if results:
                logger.info(f"發送 {len(results)} 個偵測結果到前端")
                send_detection_results(camera_id, results)
            else:
                logger.warning("沒有偵測到任何物件")
            
            last_process_time = current_time
        else:
            # 只繪製框，不執行辨識
            if latest_frame is not None:
                pass
            else:
                latest_frame = frame
        
        # 放入隊列供串流使用
        if not frame_queue.full():
            try:
                frame_queue.put(latest_frame if latest_frame is not None else frame, block=False)
            except:
                pass


def draw_detections(frame, results):
    """在影像上繪製偵測框和車牌結果"""
    for result in results:
        detection = result['base_detection']
        bbox = detection['bbox']
        class_name = detection['class']
        confidence = detection['confidence']
        
        # 繪製框
        x1, y1, x2, y2 = map(int, bbox)
        color = (0, 255, 0)  # 綠色
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # 標籤
        label = f"{class_name} {confidence:.2f}"
        
        # 如果有車牌辨識結果
        if 'license_plate' in result.get('details', {}):
            plate_info = result['details']['license_plate']
            if 'plate_number' in plate_info:
                plate_number = plate_info['plate_number']
                label = f"{plate_number} ({confidence:.2f})"
                color = (0, 255, 255)  # 黃色表示有車牌
        
        # 繪製標籤背景
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(frame, (x1, y1 - 20), (x1 + w, y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    return frame


def send_detection_results(camera_id, results):
    """發送辨識結果到前端 - 顯示所有物件偵測"""
    # 先寫入資料庫（與 main.py 邏輯一致）
    if db_handler and results:
        try:
            db_handler.save_detection(camera_id, results)
            logger.debug(f"已寫入 {len(results)} 筆資料到資料庫")
        except Exception as e:
            logger.error(f"寫入資料庫失敗: {e}")
    
    # 再透過 WebSocket 即時發送到前端
    for result in results:
        detection = result['base_detection']
        timestamp = result['timestamp']
        
        data = {
            'camera_id': camera_id,
            'timestamp': timestamp,
            'object_class': detection['class'],
            'confidence': detection['confidence'],
            'bbox': detection['bbox'],
            'is_vehicle': detection['class'] in ['car', 'truck', 'bus', 'motorcycle'],
        }
        
        # 如果有車牌辨識結果（保留但次要）
        if 'license_plate' in result.get('details', {}):
            plate_info = result['details']['license_plate']
            if 'plate_number' in plate_info:
                data['plate_number'] = plate_info['plate_number']
                data['plate_confidence'] = plate_info['confidence']
                data['zone'] = plate_info.get('zone', 'unknown')
        
        # 透過 WebSocket 發送所有物件偵測
        logger.debug(f"準備發送到 /detections: {data['object_class']}")
        socketio.emit('new_detection', data, namespace='/detections')
        logger.debug(f"已發送 new_detection 事件")


def generate_frames():
    """生成影像串流"""
    while True:
        try:
            frame = frame_queue.get(timeout=1)
            
            # 編碼為 JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Empty:
            continue
        except Exception as e:
            logger.error(f"串流錯誤: {e}")
            break


@app.route('/')
def index():
    """主頁面 - 物件偵測"""
    return render_template('index.html')


@app.route('/fence')
def fence_monitor():
    """電子圍籬監控頁面"""
    return render_template('fence_monitor.html')


@app.route('/fence/setup')
def fence_setup():
    """圍籬設定頁面"""
    return render_template('fence_setup.html')


@app.route('/debug')
def debug():
    """診斷頁面"""
    return render_template('debug.html')


@app.route('/video_feed')
def video_feed():
    """影像串流端點"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/stats')
def get_stats():
    """取得統計資料"""
    # TODO: 從資料庫查詢統計
    return jsonify({
        'total_detections': 0,
        'total_plates': 0,
        'success_rate': 0.0
    })


@app.route('/api/fence_intrusions')
def get_fence_intrusions():
    """取得圍籬入侵記錄"""
    limit = int(request.args.get('limit', 50))
    fence_id = request.args.get('fence_id', None)
    
    if db_handler:
        try:
            intrusions = db_handler.get_recent_fence_intrusions(fence_id, limit)
            return jsonify({
                'success': True,
                'data': intrusions,
                'count': len(intrusions)
            })
        except Exception as e:
            logger.error(f"查詢圍籬入侵記錄失敗: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    else:
        return jsonify({
            'success': False,
            'error': '資料庫未啟用'
        }), 503


@app.route('/api/current_frame')
def get_current_frame():
    """取得當前影像幀（用於圍籬設定）"""
    global latest_frame
    
    if latest_frame is None:
        return jsonify({
            'success': False,
            'error': '尚未取得影像'
        }), 503
    
    try:
        # 轉換為 JPEG 並編碼為 base64
        _, buffer = cv2.imencode('.jpg', latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # 取得影像尺寸
        height, width = latest_frame.shape[:2]
        
        return jsonify({
            'success': True,
            'frame': frame_base64,
            'width': width,
            'height': height
        })
    except Exception as e:
        logger.error(f"取得當前影像失敗: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/save_fence_config', methods=['POST'])
def save_fence_config():
    """儲存圍籬配置"""
    try:
        fence_data = request.json
        
        # 載入當前配置
        config_path = Path('config/config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        # 更新圍籬配置
        if 'virtual_fences' not in config_dict:
            config_dict['virtual_fences'] = {
                'enabled': True,
                'fences': []
            }
        
        if 'fences' not in config_dict['virtual_fences']:
            config_dict['virtual_fences']['fences'] = []
        
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
        for i, fence in enumerate(config_dict['virtual_fences']['fences']):
            if fence.get('id') == fence_data['id']:
                existing_index = i
                break
        
        if existing_index is not None:
            config_dict['virtual_fences']['fences'][existing_index] = new_fence
            logger.info(f"✓ 已更新圍籬: {fence_data['id']}")
        else:
            config_dict['virtual_fences']['fences'].append(new_fence)
            logger.info(f"✓ 已新增圍籬: {fence_data['id']}")
        
        # 儲存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        return jsonify({
            'success': True,
            'message': '配置已儲存，請重新啟動伺服器以套用'
        })
    
    except Exception as e:
        logger.error(f"儲存圍籬配置失敗: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@socketio.on('connect', namespace='/detections')
def handle_connect():
    """客戶端連接"""
    from flask import request
    logger.info(f'客戶端已連接 - SID: {request.sid}')
    emit('status', {'message': '已連接到伺服器'})
    logger.info('已發送 status 事件')


@socketio.on('disconnect', namespace='/detections')
def handle_disconnect():
    """客戶端斷開"""
    from flask import request
    logger.info(f'客戶端已斷開 - SID: {request.sid}')


def run_server():
    """啟動伺服器"""
    init_system()
    
    # 啟動攝影機處理執行緒
    camera_thread = threading.Thread(target=process_camera, daemon=True)
    camera_thread.start()
    
    # 啟動 Flask-SocketIO 伺服器
    logger.info("網頁伺服器啟動於 http://localhost:5000")
    logger.info("WebSocket 模式: threading")
    socketio.run(app, 
                 host='0.0.0.0', 
                 port=5000, 
                 debug=False,
                 allow_unsafe_werkzeug=True)  # 允許在開發環境中使用


if __name__ == "__main__":
    run_server()
