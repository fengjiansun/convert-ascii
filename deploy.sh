#!/bin/bash

# ASCII动画生成器阿里云部署脚本
# 使用方法：./deploy.sh [mode]
# mode: local | ecs | ack
# 例如：./deploy.sh ecs

set -e

# 配置变量
APP_NAME="ascii-converter"
DOCKER_IMAGE="$APP_NAME:latest"
ACR_REGISTRY="registry.cn-hangzhou.aliyuncs.com"
ACR_NAMESPACE="your-namespace"  # 请替换为你的命名空间
ACR_IMAGE="$ACR_REGISTRY/$ACR_NAMESPACE/$APP_NAME:latest"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    log_info "Docker 已安装: $(docker --version)"
}

# 检查Docker Compose是否安装
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    log_info "Docker Compose 已安装: $(docker-compose --version)"
}

# 构建镜像
build_image() {
    log_info "开始构建镜像..."
    docker build -t $DOCKER_IMAGE .
    log_info "镜像构建完成: $DOCKER_IMAGE"
}

# 本地部署
deploy_local() {
    log_info "开始本地部署..."
    
    check_docker
    check_docker_compose
    
    # 创建必要目录
    mkdir -p uploads ascii_frames logs
    chmod 755 uploads ascii_frames logs
    
    # 构建并启动服务
    build_image
    docker-compose up -d
    
    log_info "本地部署完成！"
    log_info "访问地址: http://localhost:5001"
    
    # 显示服务状态
    sleep 3
    docker-compose ps
}

# ECS部署
deploy_ecs() {
    log_info "开始ECS部署..."
    
    check_docker
    
    # 停止现有容器
    if docker ps -q -f name=$APP_NAME; then
        log_info "停止现有容器..."
        docker stop $APP_NAME
        docker rm $APP_NAME
    fi
    
    # 创建必要目录
    mkdir -p uploads ascii_frames logs
    chmod 755 uploads ascii_frames logs
    
    # 构建镜像
    build_image
    
    # 启动容器
    log_info "启动应用容器..."
    docker run -d \
        --name $APP_NAME \
        -p 5001:5001 \
        -v $(pwd)/uploads:/app/uploads \
        -v $(pwd)/ascii_frames:/app/ascii_frames \
        -v $(pwd)/logs:/app/logs \
        --restart unless-stopped \
        $DOCKER_IMAGE
    
    log_info "ECS部署完成！"
    log_info "访问地址: http://YOUR_SERVER_IP:5001"
    
    # 显示容器状态
    docker ps -f name=$APP_NAME
}

# ACK部署
deploy_ack() {
    log_info "开始ACK部署..."
    
    # 检查kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安装，请先安装并配置 kubectl"
        exit 1
    fi
    
    # 检查集群连接
    if ! kubectl cluster-info &> /dev/null; then
        log_error "无法连接到Kubernetes集群，请检查kubectl配置"
        exit 1
    fi
    
    log_info "连接到集群: $(kubectl config current-context)"
    
    # 构建并推送镜像
    build_image
    
    log_info "标记镜像..."
    docker tag $DOCKER_IMAGE $ACR_IMAGE
    
    log_warn "请确保已登录阿里云容器镜像服务："
    log_warn "docker login $ACR_REGISTRY"
    
    log_info "推送镜像到ACR..."
    docker push $ACR_IMAGE
    
    # 更新Kubernetes配置中的镜像地址
    sed -i "s|registry.cn-hangzhou.aliyuncs.com/your-namespace/ascii-converter:latest|$ACR_IMAGE|g" k8s-deployment.yaml
    
    # 部署到集群
    log_info "部署到Kubernetes集群..."
    kubectl apply -f k8s-deployment.yaml
    
    log_info "ACK部署完成！"
    log_info "查看部署状态："
    log_info "kubectl get pods -l app=ascii-converter"
    log_info "kubectl get services"
    
    # 显示部署状态
    sleep 5
    kubectl get pods -l app=ascii-converter
    kubectl get services ascii-converter-lb
}

# 清理资源
cleanup() {
    log_info "清理资源..."
    
    case $1 in
        local)
            docker-compose down -v
            docker rmi $DOCKER_IMAGE 2>/dev/null || true
            ;;
        ecs)
            docker stop $APP_NAME 2>/dev/null || true
            docker rm $APP_NAME 2>/dev/null || true
            docker rmi $DOCKER_IMAGE 2>/dev/null || true
            ;;
        ack)
            kubectl delete -f k8s-deployment.yaml 2>/dev/null || true
            docker rmi $DOCKER_IMAGE $ACR_IMAGE 2>/dev/null || true
            ;;
    esac
    
    log_info "清理完成"
}

# 显示帮助信息
show_help() {
    echo "ASCII动画生成器阿里云部署脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [命令]"
    echo ""
    echo "命令:"
    echo "  local     本地Docker部署"
    echo "  ecs       阿里云ECS部署"
    echo "  ack       阿里云ACK部署"
    echo "  cleanup   清理资源 [local|ecs|ack]"
    echo "  help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 local           # 本地部署"
    echo "  $0 ecs             # ECS部署"
    echo "  $0 ack             # ACK部署"
    echo "  $0 cleanup local   # 清理本地资源"
}

# 主函数
main() {
    case $1 in
        local)
            deploy_local
            ;;
        ecs)
            deploy_ecs
            ;;
        ack)
            deploy_ack
            ;;
        cleanup)
            cleanup $2
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main $@