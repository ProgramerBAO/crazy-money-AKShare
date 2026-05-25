#!/bin/bash

# ============================================
# Crazy Money 服务重启脚本
# 功能：检查并重启前后端服务
# ============================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 端口配置
BACKEND_PORT=8000
FRONTEND_PORT=3000

# 项目路径
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# 日志文件
LOG_FILE="$PROJECT_ROOT/logs/restart.log"

# 确保日志目录存在
mkdir -p "$PROJECT_ROOT/logs"

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

stop_service() {
    local port=$1
    local service_name=$2
    local success=1
    
    # 检查端口是否被占用（循环检查直到没有进程）
    local attempts=0
    local max_attempts=5
    
    while [ $attempts -lt $max_attempts ]; do
        # 获取占用端口的所有PID
        local pids=$(lsof -ti :"$port" 2>/dev/null)
        
        if [ -z "$pids" ]; then
            # 没有进程了
            log "${GREEN}$service_name 已停止${NC}"
            return 0
        fi
        
        if [ $attempts -eq 0 ]; then
            log "${YELLOW}正在停止 $service_name (端口 $port)...${NC}"
            log "进程PID: $pids"
        fi
        
        # 逐个终止进程
        for pid in $pids; do
            # 尝试优雅停止
            kill -TERM "$pid" 2>/dev/null
        done
        
        # 等待
        sleep 1
        
        # 检查是否还在运行
        local remaining_pids=$(lsof -ti :"$port" 2>/dev/null)
        
        if [ -n "$remaining_pids" ]; then
            log "${YELLOW}进程仍在运行，尝试强制终止...${NC}"
            for pid in $remaining_pids; do
                kill -9 "$pid" 2>/dev/null
            done
            sleep 0.5
        fi
        
        attempts=$((attempts + 1))
    done
    
    # 最终检查
    local final_pids=$(lsof -ti :"$port" 2>/dev/null)
    if [ -z "$final_pids" ]; then
        log "${GREEN}$service_name 已停止${NC}"
        return 0
    else
        log "${RED}$service_name 停止失败，仍有进程: $final_pids${NC}"
        return 1
    fi
}

start_backend() {
    log "${YELLOW}启动后端服务...${NC}"
    
    # 检查虚拟环境
    if [ ! -d "$PROJECT_ROOT/.venv" ]; then
        log "${RED}虚拟环境不存在，请先创建：python3 -m venv .venv${NC}"
        return 1
    fi
    
    # 切换到后端目录并启动
    cd "$BACKEND_DIR" || { log "${RED}无法进入后端目录${NC}"; return 1; }
    
    # 激活虚拟环境并启动
    source "$PROJECT_ROOT/.venv/bin/activate"
    
    # 检查端口是否已被占用
    if lsof -ti :"$BACKEND_PORT" >/dev/null 2>&1; then
        log "${RED}端口 $BACKEND_PORT 仍被占用，无法启动后端${NC}"
        return 1
    fi
    
    # 启动后端服务（后台运行）
    nohup python3 app.py > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    
    log "后端服务已启动 (PID: $BACKEND_PID)"
    
    # 等待服务启动
    local attempts=0
    local max_attempts=10
    
    while [ $attempts -lt $max_attempts ]; do
        if curl -s http://localhost:"$BACKEND_PORT"/api/system/status >/dev/null 2>&1; then
            log "${GREEN}后端服务启动成功${NC}"
            return 0
        fi
        sleep 1
        attempts=$((attempts + 1))
    done
    
    log "${RED}后端服务启动失败，请检查日志${NC}"
    return 1
}

start_frontend() {
    log "${YELLOW}启动前端服务...${NC}"
    
    # 切换到前端目录
    cd "$FRONTEND_DIR" || { log "${RED}无法进入前端目录${NC}"; return 1; }
    
    # 检查端口是否已被占用
    if lsof -ti :"$FRONTEND_PORT" >/dev/null 2>&1; then
        log "${RED}端口 $FRONTEND_PORT 仍被占用，无法启动前端${NC}"
        return 1
    fi
    
    # 启动前端服务（后台运行）
    nohup npm run dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    
    log "前端服务已启动 (PID: $FRONTEND_PID)"
    
    # 等待服务启动（Next.js 需要一些时间编译）
    local attempts=0
    local max_attempts=20
    
    while [ $attempts -lt $max_attempts ]; do
        # 检查日志中是否有 "Ready" 字样
        if grep -q "Ready" "$PROJECT_ROOT/logs/frontend.log" 2>/dev/null; then
            log "${GREEN}前端服务启动成功${NC}"
            return 0
        fi
        # 同时检查端口是否可访问
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:"$FRONTEND_PORT" | grep -q "200\|304"; then
            log "${GREEN}前端服务启动成功${NC}"
            return 0
        fi
        sleep 1
        attempts=$((attempts + 1))
    done
    
    log "${RED}前端服务启动失败或超时，请检查日志${NC}"
    return 1
}

# 主函数
main() {
    log "${GREEN}=============================${NC}"
    log "${GREEN}Crazy Money 服务重启脚本${NC}"
    log "${GREEN}=============================${NC}"
    
    # 停止后端服务
    log ""
    stop_service "$BACKEND_PORT" "后端服务"
    
    # 停止前端服务
    log ""
    stop_service "$FRONTEND_PORT" "前端服务"
    
    # 等待端口释放
    log ""
    log "${YELLOW}等待端口释放...${NC}"
    sleep 1
    
    # 启动后端服务
    log ""
    if ! start_backend; then
        log "${RED}后端启动失败，终止脚本${NC}"
        exit 1
    fi
    
    # 启动前端服务
    log ""
    if ! start_frontend; then
        log "${RED}前端启动失败${NC}"
    fi
    
    log ""
    log "${GREEN}=============================${NC}"
    log "${GREEN}服务重启完成${NC}"
    log "${GREEN}后端地址: http://localhost:$BACKEND_PORT${NC}"
    log "${GREEN}前端地址: http://localhost:$FRONTEND_PORT${NC}"
    log "${GREEN}=============================${NC}"
}

# 执行主函数
main "$@"