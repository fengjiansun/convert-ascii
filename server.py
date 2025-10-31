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
# 预设配置存储目录
PRESETS_FOLDER = 'presets'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PRESETS_FOLDER, exist_ok=True)

# 全局变量存储每个用户的转换状态
user_conversions = {}

def get_user_conversion_state(user_id):
    """获取或创建用户的转换状态"""
    if user_id not in user_conversions:
        user_conversions[user_id] = {
            'status': 'idle',  # idle, running, completed, error
            'progress': 0,
            'current_frame': 0,
            'total_frames': 0,
            'message': ''
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
            
        video_file = data.get('video_file', 'bottom-banner.mp4')
        params = data.get('params', {})
        
        # 如果是上传的文件，使用完整路径
        if video_file != 'bottom-banner.mp4' and not os.path.isabs(video_file):
            user_upload_dir = os.path.join(UPLOAD_FOLDER, user_id)
            uploaded_file_path = os.path.join(user_upload_dir, video_file)
            if os.path.exists(uploaded_file_path):
                video_file = uploaded_file_path
        
        # 获取用户转换状态
        user_conversion = get_user_conversion_state(user_id)
        
        # 检查是否已有转换在进行中
        if user_conversion['status'] == 'running':
            return jsonify({'error': '您已有转换任务在进行中'}), 400
        
        # 重置转换状态
        user_conversion.update({
            'status': 'running',
            'progress': 0,
            'current_frame': 0,
            'total_frames': 0,
            'message': '正在启动转换...'
        })
        
        # 广播开始状态（发送给特定用户）
        socketio.emit('conversion_update', user_conversion, room=user_id)
        
        # 在新线程中执行转换
        thread = threading.Thread(target=perform_conversion, args=(user_id, video_file, params))
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

def perform_conversion(user_id, video_file, params):
    """执行视频转换的实际工作"""
    user_conversion = get_user_conversion_state(user_id)
    
    try:
        # 构建配置
        config = DEFAULT_CONFIG.copy()
        
        # 设置用户专属输出目录
        output_dir = f'ascii_frames_{user_id}'
        config['output_dir'] = output_dir
        
        # 清空用户目录中的旧frame文件
        if os.path.exists(output_dir):
            import glob
            old_frames = glob.glob(os.path.join(output_dir, 'frame_*.txt'))
            for old_frame in old_frames:
                try:
                    os.remove(old_frame)
                except OSError:
                    pass  # 忽略删除失败的文件
            user_conversion['message'] = f'已清理 {len(old_frames)} 个旧帧文件'
            socketio.emit('conversion_update', user_conversion, room=user_id)
        
        # 确保用户目录存在
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
            user_conversion.update({
                'progress': progress * 100,
                'current_frame': current,
                'total_frames': total,
                'message': f'正在处理第 {current}/{total} 帧'
            })
            socketio.emit('conversion_update', user_conversion, room=user_id)
        
        # 执行转换
        user_conversion['message'] = '正在分析视频...'
        socketio.emit('conversion_update', user_conversion, room=user_id)
        
        frame_count = converter.video_to_ascii_frames(video_file, progress_callback)
        
        if frame_count > 0:
            user_conversion.update({
                'status': 'completed',
                'progress': 100,
                'current_frame': frame_count,
                'total_frames': frame_count,
                'message': f'转换完成！共生成 {frame_count} 帧'
            })
        else:
            user_conversion.update({
                'status': 'error',
                'message': '转换失败：未生成任何帧'
            })
            
    except Exception as e:
        user_conversion.update({
            'status': 'error',
            'message': f'转换失败: {str(e)}'
        })
    
    # 广播最终状态
    socketio.emit('conversion_update', user_conversion, room=user_id)

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
            'progress': 0,
            'current_frame': 0,
            'total_frames': 0,
            'message': '转换已取消'
        })
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

@app.route('/api/get_frame', methods=['GET'])
def get_frame():
    """获取单个帧的内容"""
    user_id = request.args.get('user_id')
    frame_index = request.args.get('frame_index')
    
    if not user_id or not frame_index:
        return jsonify({'error': '用户ID和帧索引不能为空'}), 400
    
    try:
        frame_index = int(frame_index)
        output_dir = f'ascii_frames_{user_id}'
        frame_file = os.path.join(output_dir, f'frame_{frame_index:05d}.txt')
        
        if os.path.exists(frame_file):
            with open(frame_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'content': content})
        else:
            return jsonify({'error': '帧文件不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': f'获取帧失败: {str(e)}'}), 500

@app.route('/api/save_frame', methods=['POST'])
def save_frame():
    """保存单个帧的内容"""
    data = request.json
    user_id = data.get('user_id')
    frame_index = data.get('frame_index')
    content = data.get('content')
    
    if not user_id or not frame_index or not content:
        return jsonify({'error': '用户ID、帧索引和内容不能为空'}), 400
    
    try:
        frame_index = int(frame_index)
        output_dir = f'ascii_frames_{user_id}'
        frame_file = os.path.join(output_dir, f'frame_{frame_index:05d}.txt')
        
        if os.path.exists(output_dir):
            with open(frame_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return jsonify({'message': '帧保存成功'})
        else:
            return jsonify({'error': '用户目录不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': f'保存帧失败: {str(e)}'}), 500

@app.route('/api/get_presets', methods=['GET'])
def get_presets():
    """获取用户的所有预设配置"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 400
    
    try:
        user_presets_dir = os.path.join(PRESETS_FOLDER, user_id)
        presets = []
        
        print(f'获取预设: 用户ID {user_id}')
        print(f'用户预设目录: {user_presets_dir}')
        print(f'目录是否存在: {os.path.exists(user_presets_dir)}')
        
        if os.path.exists(user_presets_dir):
            print(f'目录中的文件: {os.listdir(user_presets_dir)}')
            for filename in os.listdir(user_presets_dir):
                if filename.endswith('.json'):
                    preset_path = os.path.join(user_presets_dir, filename)
                    print(f'读取预设文件: {preset_path}')
                    with open(preset_path, 'r', encoding='utf-8') as f:
                        try:
                            preset = json.load(f)
                            presets.append(preset)
                            print(f'成功加载预设: {preset["name"]}')
                        except json.JSONDecodeError as e:
                            print(f'解析预设文件失败: {preset_path}, 错误: {e}')
                            continue
        
        print(f'返回预设数量: {len(presets)}')
        return jsonify({'presets': presets})
            
    except Exception as e:
        print(f'获取预设失败: {str(e)}')
        return jsonify({'error': f'获取预设失败: {str(e)}'}), 500

@app.route('/api/save_preset', methods=['POST'])
def save_preset():
    """保存预设配置"""
    data = request.json
    user_id = data.get('user_id')
    preset_name = data.get('preset_name')
    config = data.get('config')
    
    if not user_id or not preset_name or not config:
        return jsonify({'error': '用户ID、预设名称和配置不能为空'}), 400
    
    try:
        user_presets_dir = os.path.join(PRESETS_FOLDER, user_id)
        os.makedirs(user_presets_dir, exist_ok=True)
        
        preset_path = os.path.join(user_presets_dir, f'{preset_name}.json')
        
        with open(preset_path, 'w', encoding='utf-8') as f:
            json.dump({                'name': preset_name,                'config': config,                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),                'updated_at': time.strftime('%Y-%m-%d %H:%M:%S')            }, f, ensure_ascii=False, indent=2)
        
        # 调试信息：检查文件是否真正保存
        if os.path.exists(preset_path):
            with open(preset_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                print(f'预设保存成功: {preset_name} for user {user_id}')
                print(f'保存的配置: {saved_data}')
        else:
            print(f'预设保存失败: 文件不存在 {preset_path}')
        
        return jsonify({'message': '预设保存成功'})
            
    except Exception as e:
        print(f'保存预设失败: {str(e)}')
        return jsonify({'error': f'保存预设失败: {str(e)}'}), 500

@app.route('/api/delete_preset', methods=['POST'])
def delete_preset():
    """删除预设配置"""
    data = request.json
    user_id = data.get('user_id')
    preset_name = data.get('preset_name')
    
    if not user_id or not preset_name:
        return jsonify({'error': '用户ID和预设名称不能为空'}), 400
    
    try:
        user_presets_dir = os.path.join(PRESETS_FOLDER, user_id)
        preset_path = os.path.join(user_presets_dir, f'{preset_name}.json')
        
        if os.path.exists(preset_path):
            os.remove(preset_path)
            return jsonify({'message': '预设删除成功'})
        else:
            return jsonify({'error': '预设不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': f'删除预设失败: {str(e)}'}), 500

@app.route('/api/batch_replace', methods=['POST'])
def batch_replace():
    """批量替换所有帧中的字符"""
    data = request.json
    user_id = data.get('user_id')
    find_char = data.get('find_char')
    replace_char = data.get('replace_char')
    
    if not user_id or not find_char:
        return jsonify({'error': '用户ID和要查找的字符不能为空'}), 400
    
    try:
        output_dir = f'ascii_frames_{user_id}'
        if not os.path.exists(output_dir):
            return jsonify({'error': '用户目录不存在'}), 404
        
        import glob
        frame_files = glob.glob(os.path.join(output_dir, 'frame_*.txt'))
        replaced_count = 0
        
        for frame_file in frame_files:
            try:
                with open(frame_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if find_char in content:
                    new_content = content.replace(find_char, replace_char or '')
                    with open(frame_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    replaced_count += 1
            except Exception:
                continue
        
        return jsonify({
            'message': f'批量替换完成，共修改 {replaced_count} 个帧文件',
            'replaced_count': replaced_count
        })
            
    except Exception as e:
        return jsonify({'error': f'批量替换失败: {str(e)}'}), 500

@app.route('/ascii_frames_<user_id>/<filename>')
def serve_user_frames(user_id, filename):
    """提供用户专属的ASCII帧文件"""
    try:
        return send_from_directory(f'ascii_frames_{user_id}', filename)
    except FileNotFoundError:
        return "Frame not found", 404

@app.route('/ascii_frames/<filename>')
def serve_frames(filename):
    """提供ASCII帧文件（向后兼容）"""
    return send_from_directory('ascii_frames', filename)

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