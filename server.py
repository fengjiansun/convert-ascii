from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_socketio import SocketIO, emit
import subprocess
import os
import json
import threading
import time
from werkzeug.utils import secure_filename
from convert import AsciiConverter, DEFAULT_CONFIG

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ascii_converter_secret'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
socketio = SocketIO(app, cors_allowed_origins="*")

# 上传文件存储目录
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 全局变量存储每个用户的转换状态
user_conversions = {}

def get_user_conversion_state(user_id):
    """获取或创建用户的转换状态"""
    if user_id not in user_conversions:
        user_conversions[user_id] = {
            'status': 'idle',  # idle, running, completed, error
            'videos': []  # 存储每个视频的转换状态
        }
    return user_conversions[user_id]

def allowed_file(filename):
    """检查文件扩展名是否被允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """提供index.html文件"""
    return send_from_directory('.', 'index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    try:
        # 检查是否有文件在请求中
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        user_id = request.form.get('user_id')
        
        if not user_id:
            return jsonify({'error': '用户ID不能为空'}), 400
            
        # 如果用户没有选择文件，浏览器也会提交一个空的文件
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
            
        if file and allowed_file(file.filename):
            # 创建用户专属的上传目录
            user_upload_dir = os.path.join(UPLOAD_FOLDER, user_id)
            os.makedirs(user_upload_dir, exist_ok=True)
            
            # 安全化文件名并保存
            filename = secure_filename(file.filename)
            filepath = os.path.join(user_upload_dir, filename)
            file.save(filepath)
            
            return jsonify({
                'message': '文件上传成功',
                'filename': filename,
                'filepath': filepath
            })
        else:
            return jsonify({'error': '不支持的文件格式，请上传视频文件'}), 400
            
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/convert', methods=['POST'])
def convert_video():
    """处理视频转换请求"""
    try:
        data = request.json
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': '用户ID不能为空'}), 400
            
        videos = data.get('videos', [])
        if not videos:
            return jsonify({'error': '没有提供视频文件'}), 400
            
        # 获取用户转换状态
        user_conversion = get_user_conversion_state(user_id)
        
        # 检查是否已有转换在进行中
        if user_conversion['status'] == 'running':
            return jsonify({'error': '您已有转换任务在进行中'}), 400
        
        # 重置转换状态
        user_conversion.update({
            'status': 'running',
            'videos': []
        })
        
        # 为每个视频创建初始状态
        for i, video_data in enumerate(videos):
            video_file = video_data.get('video_file')
            video_params = video_data.get('params', {})
            
            # 如果是上传的文件，使用完整路径
            if video_file != 'bottom-banner.mp4' and not os.path.isabs(video_file):
                user_upload_dir = os.path.join(UPLOAD_FOLDER, user_id)
                uploaded_file_path = os.path.join(user_upload_dir, video_file)
                if os.path.exists(uploaded_file_path):
                    video_file = uploaded_file_path
            
            user_conversion['videos'].append({
                'video_index': i,
                'video_file': video_file,
                'params': video_params,
                'status': 'running',
                'progress': 0,
                'current_frame': 0,
                'total_frames': 0,
                'message': '正在启动转换...',
                'frame_folder': f'ascii_frames_{user_id}_{i}'
            })
        
        # 广播开始状态（发送给特定用户）
        socketio.emit('conversion_update', user_conversion, room=user_id)
        
        # 在新线程中执行转换
        thread = threading.Thread(target=perform_conversions, args=(user_id, user_conversion['videos']))
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': '转换已开始', 'status': 'running'})
        
    except Exception as e:
        if 'user_id' in locals():
            user_conversion = get_user_conversion_state(user_id)
            user_conversion.update({
                'status': 'error',
                'message': f'启动转换失败: {str(e)}'
            })
            socketio.emit('conversion_update', user_conversion, room=user_id)
        return jsonify({'error': str(e)}), 500

def perform_conversions(user_id, videos):
    """执行多个视频转换的实际工作"""
    user_conversion = get_user_conversion_state(user_id)
    
    try:
        # 创建线程列表
        threads = []
        
        # 为每个视频创建一个线程
        for video in videos:
            thread = threading.Thread(target=perform_single_conversion, args=(user_id, video))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查所有视频是否都完成
        all_completed = all(video['status'] == 'completed' for video in user_conversion['videos'])
        
        if all_completed:
            user_conversion.update({
                'status': 'completed',
                'message': '所有视频转换完成！'
            })
        else:
            # 检查是否有错误
            has_error = any(video['status'] == 'error' for video in user_conversion['videos'])
            if has_error:
                user_conversion.update({
                    'status': 'error',
                    'message': '部分视频转换失败！'
                })
            else:
                user_conversion.update({
                    'status': 'completed',
                    'message': '所有视频转换完成！'
                })
        
    except Exception as e:
        user_conversion.update({
            'status': 'error',
            'message': f'转换失败: {str(e)}'
        })
    
    # 广播最终状态
    socketio.emit('conversion_update', user_conversion, room=user_id)

def perform_single_conversion(user_id, video):
    """执行单个视频转换的实际工作"""
    user_conversion = get_user_conversion_state(user_id)
    video_index = video['video_index']
    video_file = video['video_file']
    params = video['params']
    output_dir = video['frame_folder']
    
    try:
        # 构建配置
        config = DEFAULT_CONFIG.copy()
        
        # 设置输出目录
        config['output_dir'] = output_dir
        
        # 清空目录中的旧frame文件
        if os.path.exists(output_dir):
            import glob
            old_frames = glob.glob(os.path.join(output_dir, 'frame_*.txt'))
            for old_frame in old_frames:
                try:
                    os.remove(old_frame)
                except OSError:
                    pass  # 忽略删除失败的文件
            video['message'] = f'已清理 {len(old_frames)} 个旧帧文件'
            socketio.emit('conversion_update', {
                'video_index': video_index,
                'status': 'running',
                'progress': 0,
                'message': video['message']
            }, room=user_id)
        
        # 确保目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 更新配置参数
        config.update({
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
            'mirror_frames': params.get('mirror_frames', False),
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
            video.update({
                'progress': progress * 100,
                'current_frame': current,
                'total_frames': total,
                'message': f'正在处理第 {current}/{total} 帧'
            })
            socketio.emit('conversion_update', {
                'video_index': video_index,
                'status': 'running',
                'progress': video['progress'],
                'current_frame': video['current_frame'],
                'total_frames': video['total_frames'],
                'message': video['message']
            }, room=user_id)
        
        # 执行转换
        video['message'] = '正在分析视频...'
        socketio.emit('conversion_update', {
            'video_index': video_index,
            'status': 'running',
            'progress': 0,
            'message': video['message']
        }, room=user_id)
        
        frame_count = converter.video_to_ascii_frames(video_file, progress_callback)
        
        if frame_count > 0:
            video.update({
                'status': 'completed',
                'progress': 100,
                'current_frame': frame_count,
                'total_frames': frame_count,
                'message': f'转换完成！共生成 {frame_count} 帧'
            })
        else:
            video.update({
                'status': 'error',
                'message': '转换失败：未生成任何帧'
            })
            
    except Exception as e:
        video.update({
            'status': 'error',
            'message': f'转换失败: {str(e)}'
        })
    
    # 广播最终状态
    socketio.emit('conversion_update', {
        'video_index': video_index,
        'status': video['status'],
        'progress': video['progress'],
        'current_frame': video['current_frame'],
        'total_frames': video['total_frames'],
        'message': video['message'],
        'frame_folder': video['frame_folder']
    }, room=user_id)

@app.route('/api/status', methods=['GET', 'POST'])
def get_status():
    """获取当前转换状态"""
    if request.method == 'POST':
        data = request.json or {}
        user_id = data.get('user_id')
    else:
        user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 400
        
    user_conversion = get_user_conversion_state(user_id)
    return jsonify(user_conversion)

@app.route('/api/config')
def get_default_config():
    """获取默认配置"""
    return jsonify(DEFAULT_CONFIG)

@app.route('/api/cancel', methods=['POST'])
def cancel_conversion():
    """取消当前转换（简单实现）"""
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 400
    
    user_conversion = get_user_conversion_state(user_id)
    
    if user_conversion['status'] == 'running':
        user_conversion.update({
            'status': 'idle',
            'message': '转换已取消'
        })
        # 取消所有视频的转换
        for video in user_conversion['videos']:
            video['status'] = 'idle'
        socketio.emit('conversion_update', user_conversion, room=user_id)
        return jsonify({'message': '转换已取消'})
    else:
        return jsonify({'message': '没有正在进行的转换'})

@app.route('/api/clear_frames', methods=['POST'])
def clear_frames():
    """清空用户的所有frame文件"""
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 400
    
    user_conversion = get_user_conversion_state(user_id)
    
    # 检查是否有转换正在进行
    if user_conversion['status'] == 'running':
        return jsonify({'error': '转换正在进行中，无法清空文件'}), 400
    
    try:
        output_dir = f'ascii_frames_{user_id}'
        if os.path.exists(output_dir):
            import glob
            frame_files = glob.glob(os.path.join(output_dir, 'frame_*.txt'))
            cleared_count = 0
            
            for frame_file in frame_files:
                try:
                    os.remove(frame_file)
                    cleared_count += 1
                except OSError:
                    pass  # 忽略删除失败的文件
            
            # 更新用户状态
            user_conversion.update({
                'status': 'idle',
                'progress': 0,
                'current_frame': 0,
                'total_frames': 0,
                'message': f'已清空 {cleared_count} 个帧文件'
            })
            socketio.emit('conversion_update', user_conversion, room=user_id)
            
            return jsonify({
                'message': f'成功清空 {cleared_count} 个帧文件',
                'cleared_count': cleared_count
            })
        else:
            return jsonify({
                'message': '用户目录不存在，无需清空',
                'cleared_count': 0
            })
            
    except Exception as e:
        return jsonify({'error': f'清空失败: {str(e)}'}), 500

@app.route('/api/check_frames/<frame_folder>')
def check_frames(frame_folder):
    """检查特定视频的帧文件是否生成完成"""
    try:
        # 检查目录是否存在
        if not os.path.exists(frame_folder):
            return jsonify({'status': 'error', 'message': '目录不存在'})
        
        # 获取所有帧文件
        import glob
        frame_files = glob.glob(os.path.join(frame_folder, 'frame_*.txt'))
        
        # 按帧号排序
        frame_files.sort()
        
        # 检查是否有帧文件
        if not frame_files:
            return jsonify({'status': 'running', 'message': '正在生成帧文件...'})
        
        # 返回帧文件列表
        return jsonify({'status': 'completed', 'frames': [os.path.basename(f) for f in frame_files]})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/ascii_frames_<user_id>/<filename>')
def serve_user_frames(user_id, filename):
    """提供用户专属的ASCII帧文件"""
    try:
        return send_from_directory(f'ascii_frames_{user_id}', filename)
    except FileNotFoundError:
        return "Frame not found", 404

@app.route('/frames/<frame_folder>/<filename>')
def serve_frames(frame_folder, filename):
    """提供ASCII帧文件"""
    try:
        return send_from_directory(frame_folder, filename)
    except FileNotFoundError:
        return "Frame not found", 404

@socketio.on('connect')
def handle_connect():
    """WebSocket连接建立"""
    print('客户端已连接')
    # 不再自动发送状态，等待客户端发送用户ID

@socketio.on('join_user_room')
def handle_join_user_room(data):
    """客户端加入用户专属房间"""
    user_id = data.get('user_id')
    if user_id:
        from flask_socketio import join_room
        join_room(user_id)
        user_conversion = get_user_conversion_state(user_id)
        emit('conversion_update', user_conversion)

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket连接断开"""
    print('客户端已断开连接')

if __name__ == '__main__':
    # 确保输出目录存在
    os.makedirs('ascii_frames', exist_ok=True)
    
    print("🚀 ASCII转换服务器启动中...")
    print("📝 访问 http://localhost:5001 打开控制界面")
    print("🔧 服务器支持实时进度更新和参数调整")
    
    # 生产环境运行配置
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)