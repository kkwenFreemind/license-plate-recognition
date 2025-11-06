"""
模組化物件辨識系統
支援可插拔的細部辨識模組
"""

from ultralytics import YOLO
import cv2
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
import json


# ============================================================================
# 1. 基礎偵測引擎
# ============================================================================

class BaseDetector:
    """YOLO 基礎偵測器"""
    
    def __init__(self, model_path='yolov8n.pt'):
        print(f"載入 YOLO 模型: {model_path}")
        self.model = YOLO(model_path)
        print("✓ YOLO 模型載入完成")
        
    def detect(self, image, conf_threshold=0.5, classes=None):
        """
        執行 YOLO 偵測
        
        Args:
            image: 輸入影像
            conf_threshold: 信心度閾值
            classes: 要偵測的類別列表 (None = 全部)
        
        Returns:
            List[Dict]: 偵測結果
        """
        results = self.model(image, verbose=False)
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                label = self.model.names[cls]
                
                # 過濾
                if conf < conf_threshold:
                    continue
                if classes and label not in classes:
                    continue
                
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                
                # 確保座標合法
                x1, y1 = max(0, x1), max(0, y1)
                x2 = min(image.shape[1], x2)
                y2 = min(image.shape[0], y2)
                
                detections.append({
                    'class': label,
                    'confidence': conf,
                    'bbox': [x1, y1, x2, y2],
                    'center': [(x1 + x2) // 2, (y1 + y2) // 2],
                    'area': (x2 - x1) * (y2 - y1)
                })
        
        return detections


# ============================================================================
# 2. 細部辨識模組介面
# ============================================================================

class DetailRecognizer(ABC):
    """細部辨識模組的抽象基類"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """模組名稱"""
        pass
    
    @property
    @abstractmethod
    def target_classes(self) -> List[str]:
        """此模組處理的 YOLO 類別"""
        pass
    
    @abstractmethod
    def initialize(self):
        """初始化模組 (載入模型等)"""
        pass
    
    @abstractmethod
    def recognize(self, image: np.ndarray, detection: Dict) -> Optional[Dict]:
        """
        執行細部辨識
        
        Args:
            image: 完整影像
            detection: YOLO 偵測結果
        
        Returns:
            Dict: 辨識結果,或 None 表示無結果
        """
        pass
    
    def should_process(self, detection: Dict) -> bool:
        """判斷是否要處理此偵測"""
        return detection['class'] in self.target_classes


# ============================================================================
# 3. 車牌辨識模組
# ============================================================================

class LicensePlateRecognizer(DetailRecognizer):
    """車牌辨識模組"""
    
    def __init__(self, min_confidence=0.3):
        self.min_confidence = min_confidence
        self.ocr_reader = None
        
    @property
    def name(self) -> str:
        return "license_plate"
    
    @property
    def target_classes(self) -> List[str]:
        return ['car', 'truck', 'bus', 'motorcycle']
    
    def initialize(self):
        """載入 OCR 模型"""
        import easyocr
        print(f"  載入 {self.name} 模組...")
        self.ocr_reader = easyocr.Reader(['en', 'ch_tra'], gpu=False)
        print(f"  ✓ {self.name} 模組就緒")
    
    def preprocess(self, image):
        """預處理圖片"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        _, binary = cv2.threshold(enhanced, 0, 255, 
                                 cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    def validate_plate(self, text):
        """驗證車牌格式"""
        import re
        text = text.replace(' ', '').replace('-', '').upper()
        text = re.sub(r'[^A-Z0-9]', '', text)
        
        patterns = [
            r'^[A-Z]{2,3}\d{4}$',
            r'^\d{4}[A-Z]{2}$',
        ]
        
        for pattern in patterns:
            if re.match(pattern, text):
                return True, self.format_plate(text)
        return False, text
    
    def format_plate(self, text):
        """格式化車牌"""
        alpha_part = ''.join([c for c in text if c.isalpha()])
        digit_part = ''.join([c for c in text if c.isdigit()])
        if alpha_part and digit_part:
            return f"{alpha_part}-{digit_part}"
        return text
    
    def recognize(self, image: np.ndarray, detection: Dict) -> Optional[Dict]:
        """辨識車牌"""
        x1, y1, x2, y2 = detection['bbox']
        
        # 提取車輛區域
        vehicle_region = image[y1:y2, x1:x2]
        
        if vehicle_region.size == 0:
            return None
        
        # 聚焦車輛下半部
        height = y2 - y1
        search_region = vehicle_region[int(height*0.5):, :]
        
        # 預處理
        processed = self.preprocess(search_region)
        
        # OCR
        results = self.ocr_reader.readtext(processed)
        
        for (bbox, text, prob) in results:
            if prob < self.min_confidence or len(text) < 5:
                continue
            
            is_valid, formatted = self.validate_plate(text)
            
            return {
                'plate_number': formatted,
                'confidence': prob,
                'is_valid': is_valid,
                'raw_text': text
            }
        
        return None


# ============================================================================
# 4. 人臉辨識模組 (範例)
# ============================================================================

class FaceRecognizer(DetailRecognizer):
    """人臉辨識模組"""
    
    def __init__(self):
        self.known_encodings = []
        self.known_names = []
        
    @property
    def name(self) -> str:
        return "face_recognition"
    
    @property
    def target_classes(self) -> List[str]:
        return ['person']
    
    def initialize(self):
        """載入人臉模型"""
        print(f"  載入 {self.name} 模組...")
        try:
            import face_recognition
            self.face_recognition = face_recognition
            print(f"  ✓ {self.name} 模組就緒")
        except ImportError:
            print(f"  ⚠ {self.name} 需要安裝: pip install face-recognition")
            self.face_recognition = None
    
    def load_known_faces(self, face_data: Dict[str, str]):
        """
        載入已知人臉
        
        Args:
            face_data: {name: image_path}
        """
        if not self.face_recognition:
            return
        
        for name, image_path in face_data.items():
            image = self.face_recognition.load_image_file(image_path)
            encodings = self.face_recognition.face_encodings(image)
            if encodings:
                self.known_encodings.append(encodings[0])
                self.known_names.append(name)
                print(f"    載入人臉: {name}")
    
    def recognize(self, image: np.ndarray, detection: Dict) -> Optional[Dict]:
        """辨識人臉"""
        if not self.face_recognition:
            return None
        
        x1, y1, x2, y2 = detection['bbox']
        person_region = image[y1:y2, x1:x2]
        
        if person_region.size == 0:
            return None
        
        # 偵測人臉
        face_locations = self.face_recognition.face_locations(person_region)
        if not face_locations:
            return None
        
        face_encodings = self.face_recognition.face_encodings(
            person_region, face_locations
        )
        
        if not face_encodings or not self.known_encodings:
            return {'identity': 'unknown', 'confidence': 0.0}
        
        # 比對
        face_encoding = face_encodings[0]
        matches = self.face_recognition.compare_faces(
            self.known_encodings, face_encoding, tolerance=0.6
        )
        
        face_distances = self.face_recognition.face_distance(
            self.known_encodings, face_encoding
        )
        
        best_match_index = np.argmin(face_distances)
        
        if matches[best_match_index]:
            return {
                'identity': self.known_names[best_match_index],
                'confidence': 1 - face_distances[best_match_index],
                'face_location': face_locations[0]
            }
        
        return {'identity': 'unknown', 'confidence': 0.0}


# ============================================================================
# 5. 自訂辨識模組範例
# ============================================================================

class CustomObjectRecognizer(DetailRecognizer):
    """自訂物件辨識模組 (範本)"""
    
    def __init__(self, target_class: str, model_path: str = None):
        self._target_class = target_class
        self.model_path = model_path
        self.custom_model = None
        
    @property
    def name(self) -> str:
        return f"custom_{self._target_class}"
    
    @property
    def target_classes(self) -> List[str]:
        return [self._target_class]
    
    def initialize(self):
        """載入自訂模型"""
        print(f"  載入 {self.name} 模組...")
        
        if self.model_path:
            # 載入您的自訓練模型
            # self.custom_model = load_your_model(self.model_path)
            pass
        
        print(f"  ✓ {self.name} 模組就緒")
    
    def recognize(self, image: np.ndarray, detection: Dict) -> Optional[Dict]:
        """執行自訂辨識"""
        x1, y1, x2, y2 = detection['bbox']
        region = image[y1:y2, x1:x2]
        
        if region.size == 0:
            return None
        
        # 這裡實作您的辨識邏輯
        # result = self.custom_model.predict(region)
        
        return {
            'custom_attribute': 'value',
            'confidence': 0.9
        }


# ============================================================================
# 6. 整合系統
# ============================================================================

class MultiModalRecognitionSystem:
    """多模態辨識系統"""
    
    def __init__(self, yolo_model='yolov8n.pt'):
        self.base_detector = BaseDetector(yolo_model)
        self.recognizers: Dict[str, DetailRecognizer] = {}
        
    def register_recognizer(self, recognizer: DetailRecognizer):
        """註冊辨識模組"""
        recognizer.initialize()
        self.recognizers[recognizer.name] = recognizer
        print(f"✓ 已註冊模組: {recognizer.name}")
    
    def process_image(self, image, conf_threshold=0.5, 
                     save_result=False) -> List[Dict]:
        """
        處理單張圖片
        
        Returns:
            List[Dict]: 完整辨識結果
        """
        # 1. YOLO 大類別偵測
        detections = self.base_detector.detect(image, conf_threshold)
        
        results = []
        
        # 2. 對每個偵測執行細部辨識
        for detection in detections:
            result = {
                'timestamp': datetime.now().isoformat(),
                'base_detection': detection,
                'details': {}
            }
            
            # 3. 找出適用的辨識模組
            for name, recognizer in self.recognizers.items():
                if recognizer.should_process(detection):
                    detail = recognizer.recognize(image, detection)
                    if detail:
                        result['details'][name] = detail
            
            results.append(result)
            
            # 4. 視覺化 (可選)
            if save_result:
                self._draw_result(image, result)
        
        return results
    
    def process_rtsp(self, rtsp_url, camera_id='CAM_001', 
                    interval=2.0, callback=None):
        """
        處理 RTSP 串流
        
        Args:
            rtsp_url: RTSP URL
            camera_id: 攝影機 ID
            interval: 處理間隔(秒)
            callback: 結果回調函數 callback(results)
        """
        import time
        
        print(f"\n連接 RTSP: {rtsp_url}")
        cap = cv2.VideoCapture(rtsp_url)
        
        if not cap.isOpened():
            print("❌ 無法連接 RTSP")
            return
        
        print("✓ RTSP 連接成功")
        print(f"處理間隔: {interval} 秒")
        print("按 'q' 停止\n")
        
        last_process_time = 0
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("⚠ 無法讀取,重新連線...")
                    time.sleep(5)
                    cap = cv2.VideoCapture(rtsp_url)
                    continue
                
                frame_count += 1
                current_time = time.time()
                
                # 顯示畫面
                display = frame.copy()
                cv2.putText(display, f"Camera: {camera_id}", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow('Recognition System', display)
                
                # 間隔處理
                if current_time - last_process_time >= interval:
                    results = self.process_image(frame)
                    
                    # 顯示結果
                    self._print_results(results, camera_id, frame_count)
                    
                    # 回調
                    if callback:
                        callback(camera_id, results)
                    
                    last_process_time = current_time
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            print("\n使用者中斷")
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    def _draw_result(self, image, result):
        """在圖片上繪製結果"""
        detection = result['base_detection']
        x1, y1, x2, y2 = detection['bbox']
        
        # 繪製邊框
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # 標籤文字
        label = detection['class']
        
        # 添加細部資訊
        if 'license_plate' in result['details']:
            plate = result['details']['license_plate']['plate_number']
            label += f" | {plate}"
        
        if 'face_recognition' in result['details']:
            identity = result['details']['face_recognition']['identity']
            label += f" | {identity}"
        
        cv2.putText(image, label, (x1, y1-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    def _print_results(self, results, camera_id, frame_count):
        """列印結果"""
        if not results:
            return
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] "
              f"Camera: {camera_id}, Frame: {frame_count}")
        print(f"偵測到 {len(results)} 個物件:")
        
        for i, result in enumerate(results, 1):
            detection = result['base_detection']
            print(f"\n  #{i} {detection['class']} "
                  f"(信心度: {detection['confidence']:.2f})")
            
            for module_name, detail in result['details'].items():
                print(f"    [{module_name}]")
                for key, value in detail.items():
                    print(f"      {key}: {value}")


# ============================================================================
# 7. 資料庫整合
# ============================================================================

class DatabaseHandler:
    """資料庫處理器"""
    
    def __init__(self, db_config):
        import psycopg2
        self.conn = psycopg2.connect(**db_config)
        self.create_tables()
    
    def create_tables(self):
        """建立資料表"""
        cursor = self.conn.cursor()
        
        # 主偵測表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id SERIAL PRIMARY KEY,
                camera_id VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                object_class VARCHAR(50),
                confidence FLOAT,
                bbox VARCHAR(100),
                details JSONB
            )
        """)
        
        # 車牌記錄表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plate_records (
                id SERIAL PRIMARY KEY,
                detection_id INTEGER REFERENCES detections(id),
                plate_number VARCHAR(20),
                is_valid BOOLEAN,
                confidence FLOAT
            )
        """)
        
        # 人臉記錄表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_records (
                id SERIAL PRIMARY KEY,
                detection_id INTEGER REFERENCES detections(id),
                identity VARCHAR(100),
                confidence FLOAT
            )
        """)
        
        self.conn.commit()
        cursor.close()
    
    def save_results(self, camera_id, results):
        """儲存辨識結果"""
        cursor = self.conn.cursor()
        
        for result in results:
            detection = result['base_detection']
            
            # 插入主記錄
            cursor.execute("""
                INSERT INTO detections 
                (camera_id, object_class, confidence, bbox, details)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                camera_id,
                detection['class'],
                detection['confidence'],
                json.dumps(detection['bbox']),
                json.dumps(result['details'])
            ))
            
            detection_id = cursor.fetchone()[0]
            
            # 插入車牌記錄
            if 'license_plate' in result['details']:
                plate = result['details']['license_plate']
                cursor.execute("""
                    INSERT INTO plate_records
                    (detection_id, plate_number, is_valid, confidence)
                    VALUES (%s, %s, %s, %s)
                """, (
                    detection_id,
                    plate['plate_number'],
                    plate['is_valid'],
                    plate['confidence']
                ))
            
            # 插入人臉記錄
            if 'face_recognition' in result['details']:
                face = result['details']['face_recognition']
                cursor.execute("""
                    INSERT INTO face_records
                    (detection_id, identity, confidence)
                    VALUES (%s, %s, %s)
                """, (
                    detection_id,
                    face['identity'],
                    face['confidence']
                ))
        
        self.conn.commit()
        cursor.close()


# ============================================================================
# 8. 使用範例
# ============================================================================

def main():
    """主程式範例"""
    
    print("=" * 70)
    print("多模態物件辨識系統")
    print("=" * 70)
    
    # 1. 建立系統
    system = MultiModalRecognitionSystem()
    
    # 2. 註冊需要的辨識模組
    print("\n註冊辨識模組:")
    
    # 車牌辨識
    plate_recognizer = LicensePlateRecognizer(min_confidence=0.3)
    system.register_recognizer(plate_recognizer)
    
    # 人臉辨識 (可選)
    # face_recognizer = FaceRecognizer()
    # system.register_recognizer(face_recognizer)
    # face_recognizer.load_known_faces({
    #     '張三': 'faces/zhang_san.jpg',
    #     '李四': 'faces/li_si.jpg'
    # })
    
    # 自訂模組 (可選)
    # custom = CustomObjectRecognizer('bottle', 'models/bottle_classifier.pt')
    # system.register_recognizer(custom)
    
    print("\n系統就緒!")
    
    # 3. 選擇處理模式
    print("\n請選擇模式:")
    print("1. 處理圖片")
    print("2. 處理 RTSP 串流")
    
    choice = input("\n輸入選項: ").strip()
    
    if choice == '1':
        # 處理圖片
        image_path = input("圖片路徑: ").strip()
        image = cv2.imread(image_path)
        
        if image is None:
            print("無法讀取圖片")
            return
        
        results = system.process_image(image, save_result=True)
        
        # 儲存結果圖
        output_path = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(output_path, image)
        print(f"\n結果已儲存: {output_path}")
        
        # 顯示 JSON 結果
        print("\n完整結果 (JSON):")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    elif choice == '2':
        # 處理 RTSP
        rtsp_url = input("RTSP URL: ").strip()
        camera_id = input("攝影機 ID: ").strip() or 'CAM_001'
        
        # 可選: 設定資料庫
        use_db = input("是否儲存到資料庫? (y/n): ").strip().lower() == 'y'
        
        db = None
        if use_db:
            db_config = {
                'host': input("資料庫 host: ") or 'localhost',
                'database': input("資料庫名稱: "),
                'user': input("使用者: "),
                'password': input("密碼: ")
            }
            db = DatabaseHandler(db_config)
        
        # 定義回調函數
        def save_callback(camera_id, results):
            if db and results:
                db.save_results(camera_id, results)
        
        # 開始處理
        system.process_rtsp(
            rtsp_url, 
            camera_id, 
            interval=2.0,
            callback=save_callback if use_db else None
        )


if __name__ == "__main__":
    main()
