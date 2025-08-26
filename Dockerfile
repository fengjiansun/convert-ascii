# 使用阿里云私有镜像作为基础镜像
FROM wisdom-knowledge-registry.cn-beijing.cr.aliyuncs.com/label-studio/python:3.12-slim

# 设置Python环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=server.py
ENV FLASK_ENV=production

# 设置工作目录
WORKDIR /app

# 先升级pip和安装基础构建工具
RUN pip install --upgrade pip setuptools wheel

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ffmpeg \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements-docker.txt .

# 安装Python依赖，使用兼容Python 3.12的版本
RUN pip install --no-cache-dir -r requirements-docker.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com || \
    pip install --no-cache-dir -r requirements-docker.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p ascii_frames uploads logs && \
    chmod 755 ascii_frames uploads logs

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 5001

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5001/api/config || exit 1

# 启动应用
CMD ["python", "start.py"]