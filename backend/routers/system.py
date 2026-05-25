"""
系统控制路由
负责服务启停和CLI命令执行
"""
import subprocess
import psutil
import os
import signal
import logging
import asyncio
import re
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from services.progress_manager import progress_manager

router = APIRouter()

PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"

class ProcessInfo(BaseModel):
    pid: Optional[int]
    status: str
    uptime: Optional[str] = None
    port: Optional[int] = None

class CommandRequest(BaseModel):
    command: str
    options: Optional[Dict[str, Any]] = None

class CommandResponse(BaseModel):
    success: bool
    message: str
    output: Optional[str] = None
    error: Optional[str] = None

_processes: Dict[str, Dict[str, Any]] = {
    "backend": {"pid": None, "process": None, "start_time": None, "port": 8000},
    "frontend": {"pid": None, "process": None, "start_time": None, "port": 3000},
    "scheduler": {"pid": None, "process": None, "start_time": None, "port": None},
}

def get_process_uptime(start_time: float) -> str:
    """获取进程运行时长"""
    if not start_time:
        return "未知"
    seconds = datetime.now().timestamp() - start_time
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        return f"{int(seconds / 60)}分钟"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}小时{minutes}分钟"

def is_port_in_use(port: int) -> bool:
    """检查端口是否被占用"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except OSError:
            return True

def kill_process_by_port(port: int) -> bool:
    """根据端口号杀死进程"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            connections = proc.connections()
            for conn in connections:
                if conn.laddr.port == port:
                    kill_process_tree(proc.pid)
                    logger.info(f"已杀死占用端口 {port} 的进程 (PID: {proc.pid})")
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def kill_process_tree(pid: int) -> bool:
    """杀死进程树"""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        parent.terminate()
        parent.wait(timeout=5)
        return True
    except psutil.NoSuchProcess:
        return True
    except Exception as e:
        logger.error(f"终止进程失败: {e}")
        return False

@router.get("/status", summary="获取所有服务状态")
async def get_all_status() -> Dict[str, Any]:
    """
    获取所有服务的运行状态
    """
    status = {}

    backend_port_in_use = is_port_in_use(8000)
    frontend_port_in_use = is_port_in_use(3000)

    for name, info in _processes.items():
        pid = info.get("pid")
        process = info.get("process")
        port = info.get("port")

        if pid and process:
            try:
                p = psutil.Process(pid)
                if p.is_running():
                    status[name] = {
                        "running": True,
                        "pid": pid,
                        "uptime": get_process_uptime(info.get("start_time")),
                        "port": port,
                        "status": p.status()
                    }
                else:
                    status[name] = {
                        "running": False,
                        "pid": None,
                        "uptime": None,
                        "port": port,
                        "reason": "进程未运行"
                    }
                    _processes[name] = {"pid": None, "process": None, "start_time": None, "port": port}
            except psutil.NoSuchProcess:
                status[name] = {
                    "running": False,
                    "pid": None,
                    "uptime": None,
                    "port": port,
                    "reason": "进程不存在"
                }
                _processes[name] = {"pid": None, "process": None, "start_time": None, "port": port}
        else:
            if name == "backend" and backend_port_in_use:
                status[name] = {
                    "running": True,
                    "pid": "external",
                    "uptime": None,
                    "port": port,
                    "status": "external"
                }
            elif name == "frontend" and frontend_port_in_use:
                status[name] = {
                    "running": True,
                    "pid": "external",
                    "uptime": None,
                    "port": port,
                    "status": "external"
                }
            else:
                status[name] = {
                    "running": False,
                    "pid": None,
                    "uptime": None,
                    "port": port
                }

    status["ports"] = {
        "backend": {"in_use": backend_port_in_use, "port": 8000},
        "frontend": {"in_use": frontend_port_in_use, "port": 3000},
    }

    return {"code": 200, "data": status, "message": "success"}

@router.post("/start/backend", summary="启动后端服务")
async def start_backend():
    """启动后端API服务"""
    info = _processes["backend"]

    if info["pid"] and info["process"]:
        try:
            p = psutil.Process(info["pid"])
            if p.is_running():
                return {"code": 200, "data": {"running": True, "pid": info["pid"]}, "message": "后端服务已在运行"}
        except psutil.NoSuchProcess:
            pass

    if is_port_in_use(8000):
        return {"code": 200, "data": {"running": True, "pid": None}, "message": "后端服务已在运行（外部启动）"}

    try:
        proc = subprocess.Popen(
            [str(VENV_PYTHON), "app.py"],
            cwd=str(BACKEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        info["pid"] = proc.pid
        info["process"] = proc
        info["start_time"] = datetime.now().timestamp()

        return {"code": 200, "data": {"running": True, "pid": proc.pid}, "message": "后端服务启动成功"}
    except Exception as e:
        logger.error(f"启动后端服务失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动后端服务失败: {str(e)}")

@router.post("/stop/backend", summary="停止后端服务")
async def stop_backend():
    """停止后端API服务"""
    info = _processes["backend"]
    import asyncio

    if info["pid"] and info["process"]:
        try:
            # 先返回响应，再在后台杀掉进程
            asyncio.create_task(asyncio.to_thread(lambda: kill_process_tree(info["pid"])))
            info["pid"] = None
            info["process"] = None
            info["start_time"] = None
            return {"code": 200, "data": {"running": False}, "message": "后端服务已停止"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"停止后端服务失败: {str(e)}")
    elif is_port_in_use(8000):
        try:
            # 先返回响应，再在后台杀掉进程
            asyncio.create_task(asyncio.to_thread(lambda: kill_process_by_port(8000)))
            return {"code": 200, "data": {"running": False}, "message": "后端服务已停止（外部进程）"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"停止后端服务失败: {str(e)}")
    else:
        return {"code": 200, "data": {"running": False}, "message": "后端服务未运行"}

@router.post("/start/frontend", summary="启动前端服务")
async def start_frontend():
    """启动前端开发服务"""
    info = _processes["frontend"]

    if info["pid"] and info["process"]:
        try:
            p = psutil.Process(info["pid"])
            if p.is_running():
                return {"code": 200, "data": {"running": True, "pid": info["pid"]}, "message": "前端服务已在运行"}
        except psutil.NoSuchProcess:
            pass

    if not FRONTEND_DIR.exists():
        raise HTTPException(status_code=500, detail="前端目录不存在")

    if is_port_in_use(3000):
        return {"code": 200, "data": {"running": True, "pid": None}, "message": "前端服务已在运行（外部启动）"}

    try:
        proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(FRONTEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        info["pid"] = proc.pid
        info["process"] = proc
        info["start_time"] = datetime.now().timestamp()

        return {"code": 200, "data": {"running": True, "pid": proc.pid}, "message": "前端服务启动成功"}
    except Exception as e:
        logger.error(f"启动前端服务失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动前端服务失败: {str(e)}")

@router.post("/stop/frontend", summary="停止前端服务")
async def stop_frontend():
    """停止前端开发服务"""
    info = _processes["frontend"]

    if info["pid"] and info["process"]:
        try:
            kill_process_tree(info["pid"])
            info["pid"] = None
            info["process"] = None
            info["start_time"] = None
            return {"code": 200, "data": {"running": False}, "message": "前端服务已停止"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"停止前端服务失败: {str(e)}")
    elif is_port_in_use(3000):
        try:
            kill_process_by_port(3000)
            return {"code": 200, "data": {"running": False}, "message": "前端服务已停止（外部进程）"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"停止前端服务失败: {str(e)}")
    else:
        return {"code": 200, "data": {"running": False}, "message": "前端服务未运行"}

@router.post("/start/scheduler", summary="启动调度器")
async def start_scheduler():
    """启动数据更新调度器"""
    info = _processes["scheduler"]

    if info["pid"] and info["process"]:
        try:
            p = psutil.Process(info["pid"])
            if p.is_running():
                return {"code": 200, "data": {"running": True, "pid": info["pid"]}, "message": "调度器已在运行"}
        except psutil.NoSuchProcess:
            pass

    try:
        proc = subprocess.Popen(
            [str(VENV_PYTHON), "cli.py", "scheduler"],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        info["pid"] = proc.pid
        info["process"] = proc
        info["start_time"] = datetime.now().timestamp()

        return {"code": 200, "data": {"running": True, "pid": proc.pid}, "message": "调度器启动成功"}
    except Exception as e:
        logger.error(f"启动调度器失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动调度器失败: {str(e)}")

@router.post("/stop/scheduler", summary="停止调度器")
async def stop_scheduler():
    """停止调度器"""
    info = _processes["scheduler"]

    if info["pid"] and info["process"]:
        try:
            kill_process_tree(info["pid"])
            info["pid"] = None
            info["process"] = None
            info["start_time"] = None
            return {"code": 200, "data": {"running": False}, "message": "调度器已停止"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"停止调度器失败: {str(e)}")
    else:
        return {"code": 200, "data": {"running": False}, "message": "调度器未运行"}

@router.post("/restart/backend", summary="重启后端服务")
async def restart_backend():
    """重启后端API服务"""
    info = _processes["backend"]

    if info["pid"] and info["process"]:
        try:
            kill_process_tree(info["pid"])
        except Exception as e:
            logger.error(f"停止后端服务失败: {e}")
    elif is_port_in_use(8000):
        kill_process_by_port(8000)

    info["pid"] = None
    info["process"] = None
    info["start_time"] = None

    await asyncio.sleep(1)

    try:
        proc = subprocess.Popen(
            [str(VENV_PYTHON), "app.py"],
            cwd=str(BACKEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        info["pid"] = proc.pid
        info["process"] = proc
        info["start_time"] = datetime.now().timestamp()

        return {"code": 200, "data": {"running": True, "pid": proc.pid}, "message": "后端服务重启成功"}
    except Exception as e:
        logger.error(f"重启后端服务失败: {e}")
        raise HTTPException(status_code=500, detail=f"重启后端服务失败: {str(e)}")

@router.post("/restart/frontend", summary="重启前端服务")
async def restart_frontend():
    """重启前端开发服务"""
    info = _processes["frontend"]

    if info["pid"] and info["process"]:
        try:
            kill_process_tree(info["pid"])
        except Exception as e:
            logger.error(f"停止前端服务失败: {e}")
    elif is_port_in_use(3000):
        kill_process_by_port(3000)

    info["pid"] = None
    info["process"] = None
    info["start_time"] = None

    await asyncio.sleep(1)

    if not FRONTEND_DIR.exists():
        raise HTTPException(status_code=500, detail="前端目录不存在")

    try:
        proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(FRONTEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        info["pid"] = proc.pid
        info["process"] = proc
        info["start_time"] = datetime.now().timestamp()

        return {"code": 200, "data": {"running": True, "pid": proc.pid}, "message": "前端服务重启成功"}
    except Exception as e:
        logger.error(f"重启前端服务失败: {e}")
        raise HTTPException(status_code=500, detail=f"重启前端服务失败: {str(e)}")

@router.post("/cli", summary="执行CLI命令")
async def run_cli_command(request: CommandRequest) -> Dict[str, Any]:
    """
    执行CLI命令

    支持的命令:
    - init: 初始化股票列表
    - download: 下载股票数据
    - check: 检查数据完整性
    - convert: 格式转换
    """
    valid_commands = ["init", "download", "check", "convert"]
    if request.command not in valid_commands:
        raise HTTPException(status_code=400, detail=f"不支持的命令: {request.command}")

    try:
        cmd = [str(VENV_PYTHON), "cli.py", request.command]
        if request.options:
            for key, value in request.options.items():
                if value is True:
                    cmd.append(f"--{key}")
                elif value is not False and value is not None:
                    cmd.append(f"--{key}={value}")

        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=3600
        )

        output = result.stdout + result.stderr

        return {
            "code": 200,
            "data": {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            },
            "message": "命令执行成功" if result.returncode == 0 else "命令执行失败"
        }

    except subprocess.TimeoutExpired:
        return {
            "code": 200,
            "data": {"success": False, "error": "命令执行超时(5分钟)"},
            "message": "命令执行超时"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"命令执行失败: {str(e)}")

@router.get("/cli/logs", summary="获取CLI命令输出")
async def get_cli_logs() -> Dict[str, Any]:
    """
    获取最近的服务日志（如果实现了日志捕获）
    """
    return {
        "code": 200,
        "data": {"logs": []},
        "message": "success"
    }

@router.post("/cli/stream", summary="异步执行CLI命令并实时推送进度")
async def run_cli_command_stream(request: CommandRequest) -> Dict[str, Any]:
    """
    异步执行CLI命令，通过WebSocket实时推送进度

    支持的命令:
    - init: 初始化股票列表
    - download: 下载股票数据
    - check: 检查数据完整性
    - convert: 格式转换
    """
    valid_commands = ["init", "download", "check", "convert"]
    if request.command not in valid_commands:
        raise HTTPException(status_code=400, detail=f"不支持的命令: {request.command}")

    task_id = f"{request.command}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    channel = request.command

    try:
        cmd = [str(VENV_PYTHON), "cli.py", request.command]
        if request.options:
            for key, value in request.options.items():
                if value is True:
                    cmd.append(f"--{key}")
                elif value is not None:
                    cmd.append(f"--{key}={value}")

        await progress_manager.send_progress(
            channel=channel,
            task_id=task_id,
            progress=0,
            message=f"开始执行: {' '.join(cmd)}",
            status="running"
        )

        # 确保Python输出不被缓冲
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'

        process = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )

        total_lines = 0
        processed_lines = 0
        output_buffer = []

        async def read_output():
            nonlocal total_lines, processed_lines
            try:
                loop = asyncio.get_running_loop()
                
                # 使用线程执行同步读取，避免阻塞事件循环
                def sync_read():
                    nonlocal total_lines, processed_lines
                    for line in iter(process.stdout.readline, ''):
                        if not line:
                            break
                        line = line.strip()
                        if line:
                            output_buffer.append(line)
                            total_lines += 1

                            if _should_send_log(line):
                                level = _get_log_level(line)
                                # 使用 run_coroutine_threadsafe 在子线程中安全调用协程
                                asyncio.run_coroutine_threadsafe(
                                    progress_manager.send_log(channel, task_id, level, line),
                                    loop
                                )
                                processed_lines += 1

                            progress = _calculate_progress(line, total_lines)
                            if progress is not None:
                                # 使用 run_coroutine_threadsafe 在子线程中安全调用协程
                                asyncio.run_coroutine_threadsafe(
                                    progress_manager.send_progress(
                                        channel=channel,
                                        task_id=task_id,
                                        progress=progress,
                                        message=_extract_message(line),
                                        current=processed_lines,
                                        status="running"
                                    ),
                                    loop
                                )

                await asyncio.to_thread(sync_read)

                process.wait()
                returncode = process.returncode

                final_progress = 100 if returncode == 0 else 0
                final_message = "执行成功" if returncode == 0 else f"执行失败 (返回码: {returncode})"

                stats = _parse_stats(output_buffer)

                await progress_manager.send_complete(
                    channel=channel,
                    task_id=task_id,
                    success=(returncode == 0),
                    message=final_message,
                    stats=stats
                )

                return {
                    "code": 200,
                    "data": {
                        "success": returncode == 0,
                        "returncode": returncode,
                        "task_id": task_id,
                        "output": "\n".join(output_buffer[-100:])
                    },
                    "message": final_message
                }

            except Exception as e:
                logger.error(f"CLI执行异常: {e}")
                await progress_manager.send_complete(
                    channel=channel,
                    task_id=task_id,
                    success=False,
                    message=f"执行异常: {str(e)}"
                )
                raise

        return await read_output()

    except Exception as e:
        logger.error(f"启动CLI命令失败: {e}")
        raise HTTPException(status_code=500, detail=f"命令执行失败: {str(e)}")

def _should_send_log(line: str) -> bool:
    """判断是否为重要日志行"""
    # 先排除 tqdm 进度条格式
    tqdm_patterns = [
        r'^\s*\d+%\|',
        r'^\s*\d+%\s*\|',
        r'\|\s*\d+/\d+\s*\[',
        r'\|\s*\d+/\d+\s*\|',
    ]
    for pattern in tqdm_patterns:
        if re.match(pattern, line):
            return False
    
    important_patterns = [
        r"^\d{4}-\d{2}-\d{2}",
        r"^\[.*?\]",
        r"^[📥📊✅❌⚠️🧪🔄🔍📋]",
        r"^开始",
        r"^完成",
        r"^成功",
        r"^失败",
        r"^跳过",
        r"^错误",
        r"^警告",
    ]
    for pattern in important_patterns:
        if re.match(pattern, line):
            return True
    return False

def _get_log_level(line: str) -> str:
    """获取日志级别"""
    if any(x in line for x in ["❌", "错误", "失败", "ERROR", "Failed"]):
        return "error"
    elif any(x in line for x in ["⚠️", "警告", "WARNING", "Warn"]):
        return "warning"
    return "info"

def _calculate_progress(line: str, line_count: int) -> Optional[float]:
    """从日志行计算进度"""
    # 1. 优先使用我们自己的进度日志格式
    progress_match = re.search(r"📊 进度:\s*(\d+)/(\d+)\s*\(([\d.]+)%\)", line)
    if progress_match:
        return float(progress_match.group(3))
    
    # 2. 尝试匹配简单的百分比格式
    percent_match = re.search(r"进度:\s*(\d+)%", line)
    if percent_match:
        return float(percent_match.group(1))
    
    # 3. 尝试匹配批次格式
    batch_match = re.search(r"批次\s*(\d+)/(\d+)", line)
    if batch_match:
        current, total = int(batch_match.group(1)), int(batch_match.group(2))
        if total > 0:
            return (current / total) * 100
    
    # 4. 完全忽略 tqdm 进度条格式
    return None

def _extract_message(line: str) -> str:
    """从日志行提取简洁消息"""
    # 先检查是否是 tqdm 进度条，如果是，直接返回空字符串或者忽略
    tqdm_patterns = [
        r'^\s*\d+%\|',
        r'^\s*\d+%\s*\|',
        r'\|\s*\d+/\d+\s*\[',
        r'\|\s*\d+/\d+\s*\|',
    ]
    for pattern in tqdm_patterns:
        if re.match(pattern, line):
            return ""
    
    # 处理新的进度格式: 📊 进度: 10/100 (10.0%) | ✅成功: 5 | ❌失败: 0 | ⏭️跳过: 5
    if "📊 进度:" in line:
        # 提取关键统计信息
        success = re.search(r"✅成功:\s*(\d+)", line)
        failed = re.search(r"❌失败:\s*(\d+)", line)
        skipped = re.search(r"⏭️跳过:\s*(\d+)", line)
        progress = re.search(r"📊 进度:\s*(\d+)/(\d+)", line)

        parts = []
        if progress:
            parts.append(f"进度: {progress.group(1)}/{progress.group(2)}")
        if success:
            parts.append(f"成功: {success.group(1)}")
        if failed:
            parts.append(f"失败: {failed.group(1)}")
        if skipped:
            parts.append(f"跳过: {skipped.group(1)}")
        return " | ".join(parts) if parts else line[:100]

    # 处理股票代码格式: 📥 000001 | 下载区间: ...
    code_match = re.search(r'[📥📊✅❌⚠️🧪🔄🔍📋]\s*(\d{6})', line)
    if code_match:
        code = code_match.group(1)
        info = line.split(code, 1)[-1] if code in line else line
        return f"股票 {code}: {info.strip()}"

    # 处理总数格式: 📋 总数: 5519 | 跳过: 5000 | 待处理: 519
    if "📋 总数:" in line:
        return line.strip()

    # 移除时间戳前缀
    line = re.sub(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+", "", line)
    line = re.sub(r"^\[.*?\]\s+", "", line)

    if len(line) > 100:
        return line[:100] + "..."
    return line

def _parse_stats(output_buffer: list) -> Dict[str, int]:
    """解析输出缓冲区的统计信息"""
    stats = {"success": 0, "failed": 0, "skipped": 0}
    for line in reversed(output_buffer):
        match = re.search(r"成功[:：]?\s*(\d+)", line)
        if match:
            stats["success"] = int(match.group(1))
        match = re.search(r"失败[:：]?\s*(\d+)", line)
        if match:
            stats["failed"] = int(match.group(1))
        match = re.search(r"跳过[:：]?\s*(\d+)", line)
        if match:
            stats["skipped"] = int(match.group(1))
    return stats
