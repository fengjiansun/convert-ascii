from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_socketio import SocketIO, emit
import subprocess
import os
import json
import threading
import time
from convert import AsciiConverter, DEFAULT_CONFIG

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ascii_converter_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量存储当前转换状态
current_conversion = {
    'status': 'idle',  # idle, running, completed, error
    'progress': 0,
    'current_frame': 0,
    'total_frames': 0,
    'message': ''
}

@app.route('/')
def index():
    """提供index.html文件"""
    return send_from_directory('.', 'index.html')

@app.route('/api/convert', methods=['POST'])
def convert_video():
    """处理视频转换请求"""
    global current_conversion
    
    # 检查是否已有转换在进行中
    if current_conversion['status'] == 'running':
        return jsonify({'error': '已有转换任务在进行中'}), 400
    
    try:
        data = request.json
        video_file = data.get('video_file', 'bottom-banner.mp4')
        params = data.get('params', {})
        
        # 重置转换状态
        current_conversion.update({
            'status': 'running',
            'progress': 0,
            'current_frame': 0,
            'total_frames': 0,
            'message': '正在启动转换...'
        })
        
        # 广播开始状态
        socketio.emit('conversion_update', current_conversion)
        
        # 在新线程中执行转换
        thread = threading.Thread(target=perform_conversion, args=(video_file, params))
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': '转换已开始', 'status': 'running'})
        
    except Exception as e:
        current_conversion.update({
            'status': 'error',
            'message': f'启动转换失败: {str(e)}'
        })
        socketio.emit('conversion_update', current_conversion)
        return jsonify({'error': str(e)}), 500

def perform_conversion(video_file, params):
    """执行视频转换的实际工作"""
    global current_conversion
    
    try:
        # 构建配置
        config = DEFAULT_CONFIG.copy()
        
        # 更新配置参数
        config.update({
            'output_dir': params.get('output_dir', 'ascii_frames'),
            'frame_width': int(params.get('frame_width', 100)),
            'frame_height': int(params.get('frame_height')) if params.get('frame_height') else None,
            'brightness': float(params.get('brightness', 1.0)),
            'contrast': float(params.get('contrast', 1.0)),
            'gamma': float(params.get('gamma', 1.0)),
            'saturation': float(params.get('saturation', 1.0)),
            'sharpness': float(params.get('sharpness', 1.0)),
            'start_time': float(params.get('start_time', 0)),
            'duration': float(params.get('duration')) if params.get('duration') else None,
            'frame_skip': int(params.get('frame_skip', 1)),
            'invert': params.get('invert', False),
            'add_padding': params.get('padding', False),
        })
        
        # 设置字符集
        charset_type = params.get('charset', 'detailed')
        if charset_type == 'simple':
            config['ascii_chars'] = config['ascii_chars_simple']
        elif charset_type == 'detailed':
            config['ascii_chars'] = config['ascii_chars_detailed']
        elif charset_type == 'custom' and params.get('custom_chars'):
            config['ascii_chars'] = params.get('custom_chars')
        
        # 创建转换器
        converter = AsciiConverter(config)
        
        # 定义进度回调函数
        def progress_callback(progress, current, total):
            current_conversion.update({
                'progress': progress * 100,
                'current_frame': current,
                'total_frames': total,
                'message': f'正在处理第 {current}/{total} 帧'
            })
            socketio.emit('conversion_update', current_conversion)
        
        # 执行转换
        current_conversion['message'] = '正在分析视频...'
        socketio.emit('conversion_update', current_conversion)
        
        frame_count = converter.video_to_ascii_frames(video_file, progress_callback)
        
        if frame_count > 0:
            current_conversion.update({
                'status': 'completed',
                'progress': 100,
                'current_frame': frame_count,
                'total_frames': frame_count,
                'message': f'转换完成！共生成 {frame_count} 帧'
            })
        else:
            current_conversion.update({
                'status': 'error',
                'message': '转换失败：未生成任何帧'
            })
            
    except Exception as e:
        current_conversion.update({
            'status': 'error',
            'message': f'转换失败: {str(e)}'
        })
    
    # 广播最终状态
    socketio.emit('conversion_update', current_conversion)

@app.route('/api/status')
def get_status():
    """获取当前转换状态"""
    return jsonify(current_conversion)

@app.route('/api/config')
def get_default_config():
    """获取默认配置"""
    return jsonify(DEFAULT_CONFIG)

@app.route('/api/cancel', methods=['POST'])
def cancel_conversion():
    """取消当前转换（简单实现）"""
    global current_conversion
    
    if current_conversion['status'] == 'running':
        current_conversion.update({
            'status': 'idle',
            'progress': 0,
            'current_frame': 0,
            'total_frames': 0,
            'message': '转换已取消'
        })
        socketio.emit('conversion_update', current_conversion)
        return jsonify({'message': '转换已取消'})
    else:
        return jsonify({'message': '没有正在进行的转换'})

@app.route('/ascii_frames/<filename>')
def serve_frames(filename):
    """提供ASCII帧文件"""
    return send_from_directory('ascii_frames', filename)

@socketio.on('connect')
def handle_connect():
    """WebSocket连接建立"""
    print('客户端已连接')
    emit('conversion_update', current_conversion)

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket连接断开"""
    print('客户端已断开连接')

if __name__ == '__main__':
    # 确保输出目录存在
    os.makedirs('ascii_frames', exist_ok=True)
    
    print("🚀 ASCII转换服务器启动中...")
    print("📝 访问 http://localhost:5000 打开控制界面")
    print("🔧 服务器支持实时进度更新和参数调整")
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=True) 