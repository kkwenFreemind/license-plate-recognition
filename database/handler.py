"""資料庫處理器"""

import psycopg2
from psycopg2 import pool
from typing import Dict, List, Optional
from datetime import datetime, timezone
import json
import logging


class DatabaseHandler:
    """PostgreSQL 資料庫處理器"""
    
    def __init__(self, config: Dict, logger: logging.Logger = None):
        """
        初始化資料庫處理器
        
        Args:
            config: 資料庫配置
            logger: 日誌記錄器
        """
        self.config = config
        self.logger = logger
        self.pool = None
        
        if config.get('enabled', True):
            self._create_connection_pool()
    
    def _create_connection_pool(self):
        """建立連線池"""
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                1,
                self.config.get('pool_size', 5),
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            if self.logger:
                self.logger.info("✓ 資料庫連線池建立成功")
        except Exception as e:
            if self.logger:
                self.logger.error(f"資料庫連線失敗: {e}")
            raise
    
    def get_connection(self):
        """從連線池取得連線"""
        if self.pool:
            return self.pool.getconn()
        return None
    
    def return_connection(self, conn):
        """歸還連線到連線池"""
        if self.pool and conn:
            self.pool.putconn(conn)
    
    def save_detection(self, camera_id: str, results: List[Dict], frame=None) -> bool:
        """
        儲存偵測結果到資料庫
        
        Args:
            camera_id: 攝影機 ID
            results: 辨識結果列表
            frame: 原始影像幀（用於截取車輛局部畫面）
        
        Returns:
            bool: 是否成功
        """
        if not self.config.get('enabled', True):
            return False
        
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for result in results:
                detection = result['base_detection']
                details = result.get('details', {})
                
                # 插入偵測記錄
                cursor.execute("""
                    INSERT INTO detections 
                    (camera_id, timestamp, object_class, confidence, bbox, details)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    camera_id,
                    datetime.fromisoformat(result['timestamp']),
                    detection['class'],
                    detection['confidence'],
                    json.dumps(detection['bbox']),
                    json.dumps(details)
                ))
                
                detection_id = cursor.fetchone()[0]
                
                # 如果有車牌辨識結果,額外記錄
                if 'license_plate' in details:
                    plate_info = details['license_plate']
                    if 'plate_number' in plate_info:
                        # 截取車輛局部畫面並轉為 base64
                        vehicle_snapshot_base64 = None
                        if frame is not None:
                            import cv2
                            import base64
                            
                            bbox = detection['bbox']
                            x1, y1, x2, y2 = map(int, bbox)
                            
                            # 擴展邊界框以包含更多車輛細節（增加 10%）
                            h, w = frame.shape[:2]
                            margin_x = int((x2 - x1) * 0.1)
                            margin_y = int((y2 - y1) * 0.1)
                            
                            x1 = max(0, x1 - margin_x)
                            y1 = max(0, y1 - margin_y)
                            x2 = min(w, x2 + margin_x)
                            y2 = min(h, y2 + margin_y)
                            
                            # 截取車輛區域
                            vehicle_crop = frame[y1:y2, x1:x2]
                            
                            # 轉為 JPEG 並編碼為 base64
                            _, buffer = cv2.imencode('.jpg', vehicle_crop, [cv2.IMWRITE_JPEG_QUALITY, 85])
                            vehicle_snapshot_base64 = base64.b64encode(buffer).decode('utf-8')
                        
                        cursor.execute("""
                            INSERT INTO plate_records 
                            (detection_id, plate_number, is_valid, confidence, first_seen_date, snapshot_base64)
                            VALUES (%s, %s, %s, %s, CURRENT_DATE, %s)
                            ON CONFLICT (plate_number, first_seen_date)
                            DO UPDATE SET
                                last_seen = CURRENT_TIMESTAMP,
                                count = plate_records.count + 1,
                                snapshot_base64 = COALESCE(EXCLUDED.snapshot_base64, plate_records.snapshot_base64)
                        """, (
                            detection_id,
                            plate_info['plate_number'],
                            plate_info.get('is_valid', True),
                            plate_info.get('confidence', 0),
                            vehicle_snapshot_base64
                        ))
            
            conn.commit()
            
            if self.logger:
                self.logger.debug(f"已儲存 {len(results)} 筆偵測記錄")
            
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            if self.logger:
                self.logger.error(f"儲存資料失敗: {e}")
            return False
        finally:
            if conn:
                self.return_connection(conn)
    
    def get_recent_detections(self, camera_id: str = None, 
                             limit: int = 100) -> List[Dict]:
        """
        取得最近的偵測記錄
        
        Args:
            camera_id: 攝影機 ID (None = 全部)
            limit: 最多回傳筆數
        
        Returns:
            List[Dict]: 偵測記錄列表
        """
        if not self.config.get('enabled', True):
            return []
        
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if camera_id:
                cursor.execute("""
                    SELECT id, camera_id, timestamp, object_class, 
                           confidence, bbox, details
                    FROM detections
                    WHERE camera_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (camera_id, limit))
            else:
                cursor.execute("""
                    SELECT id, camera_id, timestamp, object_class, 
                           confidence, bbox, details
                    FROM detections
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (limit,))
            
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'camera_id': row[1],
                    'timestamp': row[2].isoformat(),
                    'object_class': row[3],
                    'confidence': row[4],
                    'bbox': json.loads(row[5]) if row[5] else None,
                    'details': json.loads(row[6]) if row[6] else {}
                })
            
            return results
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"查詢資料失敗: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)
    
    def get_plate_statistics(self, days: int = 7) -> List[Dict]:
        """
        取得車牌統計
        
        Args:
            days: 統計天數
        
        Returns:
            List[Dict]: 統計結果
        """
        if not self.config.get('enabled', True):
            return []
        
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT plate_number, 
                       COUNT(*) as total_count,
                       MIN(first_seen) as first_seen,
                       MAX(last_seen) as last_seen
                FROM plate_records
                WHERE first_seen >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY plate_number
                ORDER BY total_count DESC
            """, (days,))
            
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'plate_number': row[0],
                    'count': row[1],
                    'first_seen': row[2].isoformat() if row[2] else None,
                    'last_seen': row[3].isoformat() if row[3] else None
                })
            
            return results
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"查詢統計失敗: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)
    
    def save_fence_intrusion(self, intrusion_data: Dict) -> bool:
        """
        儲存圍籬入侵事件到資料庫
        
        Args:
            intrusion_data: 入侵事件資料
                - fence_id: 圍籬ID
                - fence_name: 圍籬名稱
                - object_class: 物件類型
                - confidence: 信心度
                - bbox: 邊界框 [x1, y1, x2, y2]
                - camera_id: 攝影機ID
                - camera_name: 攝影機名稱
                - snapshot_base64: 影像截圖 (Base64)
                - timestamp: 時間戳記
        
        Returns:
            bool: 是否成功
        """
        if not self.config.get('enabled', True):
            return False
        
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            bbox = intrusion_data.get('bbox', [None, None, None, None])
            timestamp = intrusion_data.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            elif timestamp is None:
                timestamp = datetime.now(timezone.utc).astimezone()
            
            cursor.execute("""
                INSERT INTO fence_intrusions 
                (fence_id, fence_name, object_class, confidence, 
                 bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                 camera_id, camera_name, snapshot_base64, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                intrusion_data['fence_id'],
                intrusion_data['fence_name'],
                intrusion_data['object_class'],
                intrusion_data['confidence'],
                bbox[0] if len(bbox) > 0 else None,
                bbox[1] if len(bbox) > 1 else None,
                bbox[2] if len(bbox) > 2 else None,
                bbox[3] if len(bbox) > 3 else None,
                intrusion_data.get('camera_id'),
                intrusion_data.get('camera_name'),
                intrusion_data.get('snapshot_base64'),
                timestamp
            ))
            
            intrusion_id = cursor.fetchone()[0]
            conn.commit()
            
            if self.logger:
                self.logger.info(f"✓ 已儲存圍籬入侵事件 ID: {intrusion_id}")
            
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            if self.logger:
                self.logger.error(f"儲存圍籬入侵事件失敗: {e}")
            return False
        finally:
            if conn:
                self.return_connection(conn)
    
    def get_recent_fence_intrusions(self, fence_id: str = None, 
                                   limit: int = 100) -> List[Dict]:
        """
        取得最近的圍籬入侵記錄
        
        Args:
            fence_id: 圍籬 ID (None = 全部)
            limit: 最多回傳筆數
        
        Returns:
            List[Dict]: 入侵記錄列表
        """
        if not self.config.get('enabled', True):
            return []
        
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if fence_id:
                cursor.execute("""
                    SELECT id, fence_id, fence_name, object_class, confidence,
                           bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                           camera_id, camera_name, snapshot_base64, timestamp
                    FROM fence_intrusions
                    WHERE fence_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (fence_id, limit))
            else:
                cursor.execute("""
                    SELECT id, fence_id, fence_name, object_class, confidence,
                           bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                           camera_id, camera_name, snapshot_base64, timestamp
                    FROM fence_intrusions
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (limit,))
            
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'fence_id': row[1],
                    'fence_name': row[2],
                    'object_class': row[3],
                    'confidence': row[4],
                    'bbox': [row[5], row[6], row[7], row[8]] if row[5] is not None else None,
                    'camera_id': row[9],
                    'camera_name': row[10],
                    'snapshot_base64': row[11],
                    'timestamp': row[12].isoformat() if row[12] else None
                })
            
            return results
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"查詢圍籬入侵記錄失敗: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)
    
    def close(self):
        """關閉連線池"""
        if self.pool:
            self.pool.closeall()
            if self.logger:
                self.logger.info("資料庫連線池已關閉")
