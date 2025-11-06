"""
互動式圍籬區域選取工具
使用方法：python create_fence.py
"""

import cv2
import numpy as np
import yaml
from pathlib import Path

class FenceCreator:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.points = []
        self.temp_points = []
        self.frame = None
        self.display_frame = None
        self.window_name = "圍籬區域選取 - 左鍵點擊選點，右鍵完成，R重置，ESC取消"
        
    def mouse_callback(self, event, x, y, flags, param):
        """滑鼠事件處理"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # 左鍵：新增點
            self.temp_points.append([x, y])
            print(f"✓ 已選取點 {len(self.temp_points)}: ({x}, {y})")
            self.draw_fence()
            
        elif event == cv2.EVENT_MOUSEMOVE:
            # 滑鼠移動：顯示預覽線
            if len(self.temp_points) > 0:
                self.display_frame = self.frame.copy()
                self.draw_current_fence()
                # 繪製預覽線
                cv2.line(self.display_frame, 
                        tuple(self.temp_points[-1]), 
                        (x, y), 
                        (255, 255, 0), 2)
                cv2.imshow(self.window_name, self.display_frame)
                
        elif event == cv2.EVENT_RBUTTONDOWN:
            # 右鍵：完成選取
            if len(self.temp_points) >= 3:
                self.points = self.temp_points.copy()
                print(f"✓ 圍籬定義完成！共 {len(self.points)} 個點")
                self.draw_fence()
            else:
                print("⚠ 至少需要 3 個點才能形成圍籬區域")
    
    def draw_current_fence(self):
        """繪製當前選取的點和線"""
        if len(self.temp_points) == 0:
            return
            
        # 繪製點
        for i, point in enumerate(self.temp_points):
            cv2.circle(self.display_frame, tuple(point), 5, (0, 255, 0), -1)
            cv2.putText(self.display_frame, str(i+1), 
                       (point[0]+10, point[1]-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # 繪製線
        if len(self.temp_points) > 1:
            for i in range(len(self.temp_points) - 1):
                cv2.line(self.display_frame, 
                        tuple(self.temp_points[i]), 
                        tuple(self.temp_points[i+1]), 
                        (0, 255, 0), 2)
    
    def draw_fence(self):
        """繪製完整的圍籬區域"""
        self.display_frame = self.frame.copy()
        
        if len(self.temp_points) > 0:
            # 繪製臨時選取的點和線
            self.draw_current_fence()
        
        if len(self.points) >= 3:
            # 繪製完成的多邊形
            pts = np.array(self.points, dtype=np.int32)
            overlay = self.display_frame.copy()
            cv2.fillPoly(overlay, [pts], (0, 0, 255))
            cv2.addWeighted(overlay, 0.3, self.display_frame, 0.7, 0, self.display_frame)
            cv2.polylines(self.display_frame, [pts], True, (0, 0, 255), 2)
            
            # 標註完成狀態
            cv2.putText(self.display_frame, "COMPLETED", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       1, (0, 255, 0), 2)
        
        cv2.imshow(self.window_name, self.display_frame)
    
    def capture_frame(self):
        """從 RTSP 擷取一幀影像"""
        print(f"正在連接攝影機: {self.rtsp_url}")
        cap = cv2.VideoCapture(self.rtsp_url)
        
        if not cap.isOpened():
            print("❌ 無法連接到攝影機")
            return False
        
        # 讀取幾幀後再使用（RTSP 初始化）
        for _ in range(5):
            ret, frame = cap.read()
        
        ret, self.frame = cap.read()
        cap.release()
        
        if not ret or self.frame is None:
            print("❌ 無法讀取影像")
            return False
        
        print(f"✓ 影像擷取成功 (尺寸: {self.frame.shape[1]} x {self.frame.shape[0]})")
        self.display_frame = self.frame.copy()
        return True
    
    def run(self):
        """執行圍籬選取流程"""
        # 擷取影像
        if not self.capture_frame():
            return None
        
        # 建立視窗
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1280, 720)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        print("\n" + "="*60)
        print("互動式圍籬區域選取工具")
        print("="*60)
        print("操作說明：")
        print("  • 左鍵點擊：選取圍籬多邊形的頂點")
        print("  • 右鍵點擊：完成選取（至少需要3個點）")
        print("  • 按 R 鍵：重置所有點，重新選取")
        print("  • 按 S 鍵：儲存當前圍籬配置")
        print("  • 按 ESC 鍵：取消並退出")
        print("="*60 + "\n")
        
        cv2.imshow(self.window_name, self.display_frame)
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                print("❌ 已取消")
                cv2.destroyAllWindows()
                return None
            
            elif key == ord('r') or key == ord('R'):
                # 重置
                self.temp_points = []
                self.points = []
                print("🔄 已重置")
                self.draw_fence()
            
            elif key == ord('s') or key == ord('S'):
                # 儲存
                if len(self.points) >= 3:
                    cv2.destroyAllWindows()
                    return self.points
                else:
                    print("⚠ 請先完成圍籬選取（右鍵完成）")
        
        cv2.destroyAllWindows()
        return None


def load_config():
    """載入現有配置"""
    config_path = Path("config/config.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return None


def save_fence_to_config(points, config):
    """將圍籬座標儲存到配置檔案"""
    config_path = Path("config/config.yaml")
    
    print("\n" + "="*60)
    print("圍籬配置設定")
    print("="*60)
    
    # 輸入圍籬資訊
    fence_id = input("圍籬 ID (例如: fence_001): ").strip()
    if not fence_id:
        fence_id = f"fence_{len(config.get('virtual_fences', {}).get('fences', [])) + 1:03d}"
    
    fence_name = input("圍籬名稱 (例如: 人員禁入區): ").strip()
    if not fence_name:
        fence_name = "未命名圍籬"
    
    print("\n可用的物件類型:")
    print("  • person (人員)")
    print("  • car (汽車)")
    print("  • truck (卡車)")
    print("  • bus (巴士)")
    print("  • motorcycle (機車)")
    print("  • bicycle (腳踏車)")
    print("  • 留空表示偵測所有物件類型")
    
    target_classes_input = input("\n要偵測的物件類型 (用逗號分隔，例如: person,car): ").strip()
    target_classes = [c.strip() for c in target_classes_input.split(',') if c.strip()]
    
    min_confidence_input = input("最小信心度 (0.0-1.0，預設 0.6): ").strip()
    try:
        min_confidence = float(min_confidence_input) if min_confidence_input else 0.6
        min_confidence = max(0.0, min(1.0, min_confidence))
    except ValueError:
        min_confidence = 0.6
    
    # 建立圍籬配置
    new_fence = {
        'id': fence_id,
        'name': fence_name,
        'points': points,
        'target_classes': target_classes,
        'min_confidence': min_confidence,
        'enabled': True
    }
    
    # 更新配置
    if 'virtual_fences' not in config:
        config['virtual_fences'] = {
            'enabled': True,
            'fences': []
        }
    
    if 'fences' not in config['virtual_fences']:
        config['virtual_fences']['fences'] = []
    
    # 檢查是否已存在相同 ID
    existing_index = None
    for i, fence in enumerate(config['virtual_fences']['fences']):
        if fence.get('id') == fence_id:
            existing_index = i
            break
    
    if existing_index is not None:
        replace = input(f"\n⚠ 圍籬 {fence_id} 已存在，是否覆蓋？(y/n): ").strip().lower()
        if replace == 'y':
            config['virtual_fences']['fences'][existing_index] = new_fence
            print(f"✓ 已更新圍籬: {fence_id}")
        else:
            print("❌ 已取消")
            return False
    else:
        config['virtual_fences']['fences'].append(new_fence)
        print(f"✓ 已新增圍籬: {fence_id}")
    
    # 儲存配置
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"\n✓ 配置已儲存至: {config_path}")
    print("\n圍籬資訊:")
    print(f"  ID: {fence_id}")
    print(f"  名稱: {fence_name}")
    print(f"  座標: {points}")
    print(f"  目標類型: {target_classes if target_classes else '所有類型'}")
    print(f"  信心度: {min_confidence}")
    print("\n請重新啟動 web_server.py 以套用新配置")
    
    return True


def main():
    """主程式"""
    # 載入配置
    config = load_config()
    if not config:
        print("❌ 找不到配置檔案 config/config.yaml")
        return
    
    # 取得 RTSP URL（支援兩種配置格式）
    rtsp_url = None
    
    # 格式 1: camera.rtsp_url
    if 'camera' in config:
        rtsp_url = config['camera'].get('rtsp_url')
    
    # 格式 2: cameras 陣列（取第一個啟用的攝影機）
    if not rtsp_url and 'cameras' in config:
        for camera in config['cameras']:
            if camera.get('enabled', True):
                rtsp_url = camera.get('rtsp_url')
                camera_name = camera.get('name', '未命名')
                print(f"使用攝影機: {camera_name}")
                break
    
    if not rtsp_url:
        print("❌ 配置檔案中找不到 RTSP URL")
        print("請確認 config.yaml 中有 camera.rtsp_url 或 cameras 陣列")
        return
    
    # 建立圍籬選取工具
    creator = FenceCreator(rtsp_url)
    
    # 執行選取
    points = creator.run()
    
    if points:
        # 儲存配置
        save_fence_to_config(points, config)
    else:
        print("\n未建立圍籬")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 已中斷")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
