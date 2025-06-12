#!/usr/bin/env python3
"""
ASCII动画生成器启动脚本
运行此脚本启动完整的Web界面和服务器
"""

import sys
import os
import subprocess

def main():
    print("🎬 ASCII动画生成器启动中...")
    print("=" * 50)
    
    # 检查依赖
    try:
        import flask
        import flask_socketio
        from convert import AsciiConverter
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install flask flask-socketio")
        return
    
    # 确保目录存在
    os.makedirs('ascii_frames', exist_ok=True)
    print("✅ 输出目录准备完成")
    
    # 启动服务器
    print("\n🚀 启动Web服务器...")
    print("📱 请在浏览器中访问: http://localhost:5001")
    print("🔧 功能包括:")
    print("   - 左侧：视频转ASCII参数控制")
    print("   - 中间：ASCII动画显示")
    print("   - 右侧：播放效果控制")
    print("   - 实时进度显示")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    try:
        # 导入并启动服务器
        from server import app, socketio
        socketio.run(app, host='0.0.0.0', port=5001, debug=False)
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")

if __name__ == '__main__':
    main() 