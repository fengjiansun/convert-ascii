#!/usr/bin/env python3
"""
ASCII动画生成器守护进程启动脚本
支持后台运行、日志记录、进程管理
"""

import sys
import os
import subprocess
import signal
import time
import logging
from pathlib import Path
import argparse
import daemon
import lockfile

# 配置常量
PROJECT_DIR = Path(__file__).parent.absolute()
PID_FILE = PROJECT_DIR / 'ascii-generator.pid'
LOG_FILE = PROJECT_DIR / 'ascii-generator.log'
ERROR_LOG_FILE = PROJECT_DIR / 'ascii-generator-error.log'

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('ascii-generator')

def check_dependencies():
    """检查依赖"""
    try:
        import flask
        import flask_socketio
        from convert import AsciiConverter
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install flask flask-socketio")
        return False

def is_running():
    """检查服务是否已在运行"""
    if not PID_FILE.exists():
        return False
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        # 检查进程是否存在
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        # 进程不存在，删除过期的PID文件
        PID_FILE.unlink(missing_ok=True)
        return False

def write_pid():
    """写入PID文件"""
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

def remove_pid():
    """删除PID文件"""
    PID_FILE.unlink(missing_ok=True)

def signal_handler(signum, frame):
    """信号处理器"""
    logger = logging.getLogger('ascii-generator')
    logger.info(f"收到信号 {signum}，正在关闭服务...")
    remove_pid()
    sys.exit(0)

def run_server():
    """运行服务器"""
    logger = setup_logging()
    
    # 注册信号处理器
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 写入PID文件
    write_pid()
    
    logger.info("🎬 ASCII动画生成器守护进程启动中...")
    logger.info("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        logger.error("依赖检查失败")
        return
    
    logger.info("✅ 依赖检查通过")
    
    # 确保目录存在
    os.makedirs('ascii_frames', exist_ok=True)
    logger.info("✅ 输出目录准备完成")
    
    # 启动服务器
    logger.info("🚀 启动Web服务器...")
    logger.info("📱 服务运行在: http://localhost:5001")
    logger.info("🔧 功能包括:")
    logger.info("   - 左侧：视频转ASCII参数控制")
    logger.info("   - 中间：ASCII动画显示")
    logger.info("   - 右侧：播放效果控制")
    logger.info("   - 实时进度显示")
    logger.info("   - 多用户隔离支持")
    logger.info("=" * 50)
    
    try:
        # 导入并启动服务器
        from server import app, socketio
        socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"启动失败: {e}")
        remove_pid()
        raise

def start_daemon():
    """启动守护进程"""
    if is_running():
        print("❌ 服务已在运行中")
        return False
    
    print("🚀 启动守护进程...")
    
    # 创建守护进程上下文
    context = daemon.DaemonContext(
        pidfile=lockfile.FileLock(str(PID_FILE)),
        working_directory=str(PROJECT_DIR),
        umask=0o002,
        stdout=open(LOG_FILE, 'a'),
        stderr=open(ERROR_LOG_FILE, 'a'),
    )
    
    with context:
        run_server()
    
    return True

def stop_daemon():
    """停止守护进程"""
    if not is_running():
        print("❌ 服务未运行")
        return False
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        print(f"🛑 停止进程 {pid}...")
        os.kill(pid, signal.SIGTERM)
        
        # 等待进程结束
        for _ in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(1)
            except OSError:
                break
        else:
            # 强制杀死
            print("⚠️  强制终止进程...")
            os.kill(pid, signal.SIGKILL)
        
        remove_pid()
        print("✅ 服务已停止")
        return True
        
    except (OSError, ValueError) as e:
        print(f"❌ 停止失败: {e}")
        return False

def restart_daemon():
    """重启守护进程"""
    print("🔄 重启服务...")
    stop_daemon()
    time.sleep(2)
    return start_daemon()

def status_daemon():
    """查看守护进程状态"""
    if is_running():
        with open(PID_FILE, 'r') as f:
            pid = f.read().strip()
        print(f"✅ 服务正在运行 (PID: {pid})")
        print(f"📝 日志文件: {LOG_FILE}")
        print(f"❌ 错误日志: {ERROR_LOG_FILE}")
        return True
    else:
        print("❌ 服务未运行")
        return False

def show_logs(lines=50):
    """显示日志"""
    if LOG_FILE.exists():
        print(f"📝 最近 {lines} 行日志:")
        print("-" * 50)
        try:
            result = subprocess.run(['tail', '-n', str(lines), str(LOG_FILE)], 
                                  capture_output=True, text=True)
            print(result.stdout)
        except FileNotFoundError:
            # 如果没有tail命令，使用Python实现
            with open(LOG_FILE, 'r') as f:
                lines_list = f.readlines()
                for line in lines_list[-lines:]:
                    print(line.rstrip())
    else:
        print("❌ 日志文件不存在")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='ASCII动画生成器守护进程管理')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'logs', 'foreground'],
                       help='操作类型')
    parser.add_argument('--lines', type=int, default=50,
                       help='显示日志行数 (仅用于logs操作)')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        if start_daemon():
            print("✅ 守护进程启动成功")
        else:
            sys.exit(1)
    
    elif args.action == 'stop':
        if stop_daemon():
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif args.action == 'restart':
        if restart_daemon():
            print("✅ 守护进程重启成功")
        else:
            sys.exit(1)
    
    elif args.action == 'status':
        if not status_daemon():
            sys.exit(1)
    
    elif args.action == 'logs':
        show_logs(args.lines)
    
    elif args.action == 'foreground':
        # 前台运行模式
        if is_running():
            print("❌ 服务已在运行中，请先停止")
            sys.exit(1)
        
        print("🎬 前台运行模式...")
        try:
            run_server()
        except KeyboardInterrupt:
            print("\n👋 服务已停止")

if __name__ == '__main__':
    main() 