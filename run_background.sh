#!/bin/bash

# ASCII动画生成器后台运行脚本

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$PROJECT_DIR/ascii-generator.pid"
LOG_FILE="$PROJECT_DIR/ascii-generator.log"

cd "$PROJECT_DIR"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "❌ 服务已在运行中 (PID: $(cat $PID_FILE))"
            exit 1
        fi
        
        echo "🚀 启动ASCII动画生成器后台服务..."
        
        # 激活虚拟环境（如果存在）
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        fi
        
        # 使用nohup后台运行
        nohup python start.py > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        
        echo "✅ 服务已启动 (PID: $!)"
        echo "📝 日志文件: $LOG_FILE"
        echo "📱 访问地址: http://localhost:5001"
        ;;
        
    stop)
        if [ ! -f "$PID_FILE" ]; then
            echo "❌ 服务未运行"
            exit 1
        fi
        
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🛑 停止服务 (PID: $PID)..."
            kill "$PID"
            
            # 等待进程结束
            for i in {1..10}; do
                if ! kill -0 "$PID" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            
            # 如果还没结束，强制杀死
            if kill -0 "$PID" 2>/dev/null; then
                echo "⚠️  强制终止进程..."
                kill -9 "$PID"
            fi
            
            rm -f "$PID_FILE"
            echo "✅ 服务已停止"
        else
            echo "❌ 进程不存在，清理PID文件"
            rm -f "$PID_FILE"
        fi
        ;;
        
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "✅ 服务正在运行 (PID: $(cat $PID_FILE))"
            echo "📝 日志文件: $LOG_FILE"
        else
            echo "❌ 服务未运行"
            exit 1
        fi
        ;;
        
    logs)
        if [ -f "$LOG_FILE" ]; then
            echo "📝 实时日志 (按Ctrl+C退出):"
            tail -f "$LOG_FILE"
        else
            echo "❌ 日志文件不存在"
        fi
        ;;
        
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动服务"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  status  - 查看状态"
        echo "  logs    - 查看实时日志"
        exit 1
        ;;
esac 