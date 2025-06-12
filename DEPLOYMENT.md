# ECS 部署指南

本文档介绍如何在阿里云ECS服务器上部署ASCII动画生成器，实现常驻运行。

## 🚀 快速部署

### 1. 环境准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和必要工具
sudo apt install python3 python3-pip python3-venv git -y

# 安装系统依赖
sudo apt install libgl1-mesa-glx libglib2.0-0 -y
```

### 2. 项目部署

```bash
# 克隆项目（或上传项目文件）
git clone <your-repo-url> /opt/ascii-generator
cd /opt/ascii-generator

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置防火墙

```bash
# 开放5001端口
sudo ufw allow 5001
sudo ufw enable
```

## 🔧 常驻运行方案

### 方案1：使用systemd服务（推荐）

#### 1.1 修改服务配置文件

编辑 `ascii-generator.service` 文件，修改路径：

```ini
[Unit]
Description=ASCII Animation Generator Web Service
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/ascii-generator
Environment=PATH=/opt/ascii-generator/.venv/bin
ExecStart=/opt/ascii-generator/.venv/bin/python /opt/ascii-generator/start.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ascii-generator

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/ascii-generator

[Install]
WantedBy=multi-user.target
```

#### 1.2 安装和启动服务

```bash
# 复制服务文件
sudo cp ascii-generator.service /etc/systemd/system/

# 重新加载systemd
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable ascii-generator

# 启动服务
sudo systemctl start ascii-generator

# 查看状态
sudo systemctl status ascii-generator
```

#### 1.3 服务管理命令

```bash
# 启动服务
sudo systemctl start ascii-generator

# 停止服务
sudo systemctl stop ascii-generator

# 重启服务
sudo systemctl restart ascii-generator

# 查看状态
sudo systemctl status ascii-generator

# 查看日志
sudo journalctl -u ascii-generator -f

# 禁用服务
sudo systemctl disable ascii-generator
```

### 方案2：使用守护进程脚本

#### 2.1 使用Python守护进程

```bash
# 启动守护进程
python start_daemon.py start

# 停止守护进程
python start_daemon.py stop

# 重启守护进程
python start_daemon.py restart

# 查看状态
python start_daemon.py status

# 查看日志
python start_daemon.py logs

# 前台运行（调试用）
python start_daemon.py foreground
```

#### 2.2 使用Shell脚本

```bash
# 给脚本执行权限
chmod +x run_background.sh

# 启动服务
./run_background.sh start

# 停止服务
./run_background.sh stop

# 重启服务
./run_background.sh restart

# 查看状态
./run_background.sh status

# 查看实时日志
./run_background.sh logs
```

### 方案3：使用screen会话

```bash
# 安装screen
sudo apt install screen -y

# 创建新的screen会话
screen -S ascii-generator

# 在screen中启动服务
cd /opt/ascii-generator
source .venv/bin/activate
python start.py

# 按 Ctrl+A 然后按 D 分离会话

# 重新连接会话
screen -r ascii-generator

# 查看所有会话
screen -ls

# 终止会话
screen -S ascii-generator -X quit
```

## 🔍 监控和维护

### 日志管理

```bash
# systemd服务日志
sudo journalctl -u ascii-generator -f --since "1 hour ago"

# 守护进程日志
tail -f /opt/ascii-generator/ascii-generator.log

# 错误日志
tail -f /opt/ascii-generator/ascii-generator-error.log
```

### 性能监控

```bash
# 查看进程状态
ps aux | grep python

# 查看端口占用
netstat -tlnp | grep 5001

# 查看系统资源
htop
```

### 自动重启脚本

创建监控脚本 `monitor.sh`：

```bash
#!/bin/bash
# 服务监控脚本

SERVICE_URL="http://localhost:5001"
MAX_RETRIES=3

for i in $(seq 1 $MAX_RETRIES); do
    if curl -f -s "$SERVICE_URL" > /dev/null; then
        echo "$(date): 服务正常运行"
        exit 0
    else
        echo "$(date): 服务检查失败，尝试 $i/$MAX_RETRIES"
        sleep 10
    fi
done

echo "$(date): 服务异常，尝试重启..."
sudo systemctl restart ascii-generator
```

添加到crontab：

```bash
# 编辑crontab
crontab -e

# 添加监控任务（每5分钟检查一次）
*/5 * * * * /opt/ascii-generator/monitor.sh >> /var/log/ascii-monitor.log 2>&1
```

## 🔒 安全配置

### 1. 创建专用用户

```bash
# 创建专用用户
sudo useradd -r -s /bin/false ascii-generator

# 修改文件所有权
sudo chown -R ascii-generator:ascii-generator /opt/ascii-generator

# 修改服务文件中的用户
sudo sed -i 's/User=ubuntu/User=ascii-generator/' /etc/systemd/system/ascii-generator.service
sudo sed -i 's/Group=ubuntu/Group=ascii-generator/' /etc/systemd/system/ascii-generator.service
```

### 2. 配置反向代理（可选）

使用Nginx作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🐛 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   sudo lsof -i :5001
   sudo kill -9 <PID>
   ```

2. **权限问题**
   ```bash
   sudo chown -R $USER:$USER /opt/ascii-generator
   chmod +x /opt/ascii-generator/*.py
   ```

3. **依赖问题**
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **服务无法启动**
   ```bash
   # 检查服务状态
   sudo systemctl status ascii-generator
   
   # 查看详细日志
   sudo journalctl -u ascii-generator -n 50
   ```

### 性能优化

1. **增加文件描述符限制**
   ```bash
   echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
   echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
   ```

2. **优化Python性能**
   ```bash
   # 在服务文件中添加环境变量
   Environment=PYTHONUNBUFFERED=1
   Environment=PYTHONOPTIMIZE=1
   ```

## 📋 部署检查清单

- [ ] 系统依赖已安装
- [ ] Python虚拟环境已创建
- [ ] 项目依赖已安装
- [ ] 防火墙端口已开放
- [ ] 服务配置文件已修改路径
- [ ] systemd服务已安装并启用
- [ ] 服务正常启动
- [ ] Web界面可正常访问
- [ ] 多用户功能正常
- [ ] 日志记录正常
- [ ] 监控脚本已配置（可选）
- [ ] 反向代理已配置（可选）

## 🔄 更新部署

```bash
# 停止服务
sudo systemctl stop ascii-generator

# 更新代码
cd /opt/ascii-generator
git pull

# 更新依赖
source .venv/bin/activate
pip install -r requirements.txt

# 重启服务
sudo systemctl start ascii-generator

# 检查状态
sudo systemctl status ascii-generator
``` 