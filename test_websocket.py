"""測試 WebSocket 連接和資料發送"""

import time
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return """
    <html>
        <head>
            <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
        </head>
        <body>
            <h1>WebSocket 測試</h1>
            <div id="messages"></div>
            <script>
                const socket = io('/detections');
                
                socket.on('connect', function() {
                    console.log('已連接');
                    document.getElementById('messages').innerHTML += '<p>✅ 已連接</p>';
                });
                
                socket.on('new_detection', function(data) {
                    console.log('收到資料:', data);
                    document.getElementById('messages').innerHTML += 
                        '<p>🎯 偵測到: ' + data.object_class + ' (' + data.confidence + ')</p>';
                });
            </script>
        </body>
    </html>
    """

@socketio.on('connect', namespace='/detections')
def handle_connect():
    print('客戶端已連接')
    emit('status', {'message': '已連接到伺服器'})

def send_test_data():
    """定期發送測試資料"""
    import threading
    
    def sender():
        time.sleep(3)  # 等待 3 秒
        test_objects = ['car', 'person', 'truck', 'bus', 'motorcycle']
        count = 0
        
        while True:
            count += 1
            obj = test_objects[count % len(test_objects)]
            
            data = {
                'camera_id': 'test',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'object_class': obj,
                'confidence': 0.85 + (count % 10) * 0.01,
                'bbox': [100, 100, 300, 300],
                'is_vehicle': obj in ['car', 'truck', 'bus', 'motorcycle']
            }
            
            print(f"發送測試資料: {data}")
            socketio.emit('new_detection', data, namespace='/detections')
            time.sleep(2)
    
    thread = threading.Thread(target=sender, daemon=True)
    thread.start()

if __name__ == '__main__':
    print("啟動測試伺服器: http://localhost:5001")
    send_test_data()
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)
