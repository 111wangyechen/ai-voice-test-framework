"""
后端API主程序 - 集成Workflow多代理编排
"""
import asyncio
import json
import os
import sys
import shutil
import threading
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional
import random
import time
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 导入本地模块
from report_generator import LocalReportGenerator
from device_monitor import DeviceMonitorSession, LogEventParser, PerformanceMonitor
from utils.adb_helper import ADBDevice, ADBManager

# 默认 Claude 模型（可被环境变量 ANTHROPIC_MODEL 覆盖）
DEFAULT_CLAUDE_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def resource_path(relative: str) -> Path:
    """
    解析资源路径，兼容三种运行方式：
    1. PyInstaller 单文件包：资源解压到 sys._MEIPASS
    2. 直接运行 backend/main.py：资源在项目根目录（main.py 的上级）
    3. 当前工作目录回退
    其中 frontend/dist 和 workflows 通过 spec 的 datas 打入包内。
    """
    # PyInstaller 运行时
    base = getattr(sys, "_MEIPASS", None)
    if base:
        candidate = Path(base) / relative
        if candidate.exists():
            return candidate
    # 源码运行：项目根 = backend 的上一级
    project_root = Path(__file__).resolve().parent.parent
    candidate = project_root / relative
    if candidate.exists():
        return candidate
    # 回退到 backend 同级
    return Path(__file__).resolve().parent / relative


def open_browser_when_ready(url: str, delay: float = 1.5) -> None:
    """延迟在后台线程打开默认浏览器，避免阻塞服务启动。"""
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
            logger.info(f"已在默认浏览器打开界面: {url}")
        except Exception as e:
            logger.warning(f"自动打开浏览器失败，请手动访问 {url}: {e}")

    threading.Thread(target=_open, daemon=True).start()

app = FastAPI(title="AI Voice Test Framework - Multi-Agent Edition")

# CORS配置
# 注意：allow_origins=["*"] 与 allow_credentials=True 不能同时使用（浏览器规范禁止）。
# 前端不需要携带凭证(cookie)，因此关闭 credentials 并放开所有来源，最稳健。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Workflow脚本目录
WORKFLOW_DIR = resource_path("workflows")

# 活动的workflow实例
active_workflows: Dict[str, Dict[str, Any]] = {}

# 测试运行状态：控制WebSocket是否推送日志/性能数据
# 由 /api/test/start、/api/monitor/start 置为 True，/api/test/stop 置为 False
test_running: bool = False

# ADB设备管理器
adb_manager = ADBManager()

# 当前监控会话
current_monitor_session: Optional[DeviceMonitorSession] = None

# 配置：是否启用AI增强（需要ANTHROPIC_API_KEY）
AI_ENHANCED_MODE = False  # 默认使用本地分析引擎

# 存储测试数据（用于生成报告）
test_data_storage: Dict[str, Dict[str, Any]] = {}


class TestConfig(BaseModel):
    """测试配置"""
    deviceIP: str = "10.7.187.15:5555"
    duration: int = 300  # 监控时长（秒）
    scenario: str = "fullduplex"  # 测试场景


class ErrorEvent(BaseModel):
    """错误事件"""
    type: str
    timestamp: str
    description: str
    severity: str
    raw_log: Optional[str] = None


class DiagnoseRequest(BaseModel):
    """错误诊断请求"""
    error_event: ErrorEvent
    device_ip: str = "10.7.187.15:5555"


class ReportRequest(BaseModel):
    """报告生成请求"""
    session_id: str
    test_events: list = []
    performance_data: list = []
    test_config: dict = {}


class AIHealthError(Exception):
    """AI 模式不可用时抛出，由调用方决定回退策略或返回前端"""

    def __init__(self, reason: str, code: str):
        super().__init__(reason)
        self.reason = reason
        self.code = code  # missing_key | sdk_unavailable | network | auth | unknown


def check_ai_health(timeout: float = 5.0) -> Dict[str, Any]:
    """
    主动探测 Claude API 是否可用。

    返回:
      {ok, code, reason, latency_ms, model}
      code 取值: ok | missing_key | sdk_unavailable | network | auth | unknown
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "ok": False,
            "code": "missing_key",
            "reason": "未检测到 ANTHROPIC_API_KEY 环境变量",
            "latency_ms": None,
            "model": DEFAULT_CLAUDE_MODEL,
        }

    try:
        from anthropic import Anthropic
    except ImportError as e:
        return {
            "ok": False,
            "code": "sdk_unavailable",
            "reason": f"anthropic SDK 未安装: {e}",
            "latency_ms": None,
            "model": DEFAULT_CLAUDE_MODEL,
        }

    try:
        client = Anthropic(api_key=api_key, timeout=timeout)
    except Exception as e:
        return {
            "ok": False,
            "code": "sdk_unavailable",
            "reason": f"Anthropic 客户端实例化失败: {type(e).__name__}: {e}",
            "latency_ms": None,
            "model": DEFAULT_CLAUDE_MODEL,
        }

    # 用最小代价的请求验证连通性 + key 有效性
    started = time.monotonic()
    try:
        client.messages.create(
            model=DEFAULT_CLAUDE_MODEL,
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        return {
            "ok": True,
            "code": "ok",
            "reason": "Claude API 可用",
            "latency_ms": latency_ms,
            "model": DEFAULT_CLAUDE_MODEL,
        }
    except Exception as e:
        latency_ms = int((time.monotonic() - started) * 1000)
        # 区分 auth / network / 其他
        from anthropic import AuthenticationError, APIConnectionError, APIStatusError
        if isinstance(e, AuthenticationError):
            code, reason = "auth", f"API key 无效或已失效: {e}"
        elif isinstance(e, APIConnectionError):
            code, reason = "network", f"无法连接 api.anthropic.com（可能被网络代理拦截）: {e}"
        elif isinstance(e, APIStatusError):
            code, reason = "unknown", f"API 返回错误: {e.status_code} {e}"
        else:
            code, reason = "unknown", f"{type(e).__name__}: {e}"
        return {
            "ok": False,
            "code": code,
            "reason": reason,
            "latency_ms": latency_ms,
            "model": DEFAULT_CLAUDE_MODEL,
        }


class WorkflowInvoker:
    """Workflow调用器 - 通过 Anthropic SDK 调用 Claude

    注：当前实现并非真正执行 workflows/*.js 脚本，而是按任务类型构造 prompt
    后调用 Claude Messages API。脚本文件存在性仍会校验，避免静默回退。
    """

    @staticmethod
    async def invoke_workflow(
        script_path: Path,
        args: Dict[str, Any],
        workflow_name: str,
    ) -> Dict[str, Any]:
        """
        调用 Workflow 对应的 Claude 任务。

        返回:
          成功: {"success": True, "analysis": str, "result": dict, "workflow_name": str}
          失败: 抛出 AIHealthError 或 RuntimeError，由路由层转成 HTTP 错误
        """
        if not script_path.exists():
            raise FileNotFoundError(f"Workflow脚本不存在: {script_path}")

        # 仅做存在性校验；脚本内容不直接喂给 Claude（普通 SDK 不会执行 .js）
        logger.info(f"[Workflow] 启动 {workflow_name}")

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise AIHealthError("未配置 ANTHROPIC_API_KEY，无法启动 Claude 分析", "missing_key")

        try:
            from anthropic import Anthropic, AuthenticationError, APIConnectionError, APIStatusError
        except ImportError as e:
            raise AIHealthError(f"anthropic SDK 未安装: {e}", "sdk_unavailable")

        try:
            client = Anthropic(api_key=api_key, timeout=30.0)
        except Exception as e:
            raise AIHealthError(
                f"Anthropic 客户端实例化失败: {type(e).__name__}: {e}",
                "sdk_unavailable",
            )

        prompt = f"""你是一个AI辅助语音测试分析专家。

任务：{workflow_name}

输入数据：
{json.dumps(args, indent=2, ensure_ascii=False)}

请根据上述数据进行分析，并以JSON格式返回结果。

要求：
1. 如果是监控任务，分析设备日志和性能数据
2. 如果是错误诊断，给出根因分析和解决方案
3. 如果是报告生成，计算指标并生成Markdown报告
4. 返回格式必须是有效的JSON

返回示例（根据任务类型调整）：
{{
  "success": true,
  "analysis": "分析结果...",
  "result": {{}}
}}
"""

        try:
            # SDK 调用是同步的，丢到线程池避免阻塞事件循环
            response = await asyncio.to_thread(
                client.messages.create,
                model=DEFAULT_CLAUDE_MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
        except AuthenticationError as e:
            raise AIHealthError(f"API key 无效: {e}", "auth")
        except APIConnectionError as e:
            raise AIHealthError(f"网络无法到达 Claude API: {e}", "network")
        except APIStatusError as e:
            raise AIHealthError(f"Claude API 返回错误 {e.status_code}: {e}", "unknown")
        except Exception as e:
            raise AIHealthError(f"调用 Claude 失败: {type(e).__name__}: {e}", "unknown")

        result_text = response.content[0].text if response.content else ""
        logger.info(f"[Workflow] Claude 返回前 200 字符: {result_text[:200]}")

        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    result = {"success": True, "analysis": result_text, "result": {}}
            else:
                result = {"success": True, "analysis": result_text, "result": {}}

        result.setdefault("workflow_name", workflow_name)
        return result


@app.post("/api/test/start")
async def start_test(config: TestConfig):
    """
    启动测试 - 调用主编排Workflow

    这会启动 main-test-orchestrator workflow，它会：
    1. 初始化设备连接
    2. 启动监控workflow（并行监控日志和性能）
    3. 如果发现错误，启动诊断workflow
    4. 生成报告workflow
    5. 等待人工审核
    """
    global test_running

    # 仅在 AI 增强模式下需要 Claude；非 AI 模式直接置位即可，本地分析自负责
    if not AI_ENHANCED_MODE:
        test_running = True
        return {
            "success": True,
            "workflow_id": None,
            "message": "测试已启动（本地模式）",
            "config": config.dict(),
            "mode": "local",
        }

    try:
        test_running = True
        script_path = WORKFLOW_DIR / "main-test-orchestrator.js"

        result = await WorkflowInvoker.invoke_workflow(
            script_path=script_path,
            args={
                "sessionId": f"test_{int(asyncio.get_event_loop().time())}",
                "testConfig": config.dict()
            },
            workflow_name="main-test-orchestrator"
        )

        return {
            "success": True,
            "workflow_id": result.get("workflow_id"),
            "message": "测试已启动",
            "config": config.dict(),
            "mode": "ai_enhanced",
        }

    except AIHealthError as e:
        test_running = False
        raise HTTPException(
            status_code=503,
            detail={"code": e.code, "reason": e.reason, "stage": "ai_invoke"},
        )
    except FileNotFoundError as e:
        test_running = False
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        test_running = False
        logger.error(f"启动测试失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/monitor/start")
async def start_monitoring(config: TestConfig):
    """
    启动监控 - 调用监控Workflow（仅 AI 增强模式可用）
    """
    if not AI_ENHANCED_MODE:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "ai_disabled",
                "reason": "/api/monitor/start 仅在 AI 增强模式下可用，请先开启 AI 模式",
            },
        )

    global test_running
    try:
        test_running = True
        script_path = WORKFLOW_DIR / "test-monitoring.js"

        result = await WorkflowInvoker.invoke_workflow(
            script_path=script_path,
            args={
                "deviceIP": config.deviceIP,
                "duration": config.duration,
                "testConfig": config.dict()
            },
            workflow_name="test-monitoring"
        )

        return {
            "success": True,
            "workflow_id": result.get("workflow_id"),
            "message": "监控已启动"
        }

    except AIHealthError as e:
        test_running = False
        raise HTTPException(
            status_code=503,
            detail={"code": e.code, "reason": e.reason, "stage": "ai_invoke"},
        )
    except Exception as e:
        test_running = False
        logger.error(f"启动监控失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/test/stop")
async def stop_test():
    """
    停止测试 - 停止WebSocket的日志/性能数据推送

    将 test_running 置为 False，两个WebSocket端点会停止推送数据
    （连接保持，下次开始测试时无需重连）。
    """
    global test_running, current_monitor_session
    test_running = False

    # 停止监控会话
    if current_monitor_session:
        current_monitor_session.stop()

    logger.info("[API] 测试已停止，WebSocket推送暂停")
    return {
        "success": True,
        "message": "测试已停止"
    }


@app.post("/api/device/connect")
async def connect_device(config: TestConfig):
    """
    连接ADB设备

    Args:
        config: 包含deviceIP的配置
    """
    global current_monitor_session

    try:
        device_ip = config.deviceIP
        logger.info(f"尝试连接设备: {device_ip}")

        # 添加设备到管理器
        success = await adb_manager.add_device(device_ip)

        if success:
            # 创建监控会话
            device = adb_manager.get_current_device()
            if device:
                current_monitor_session = DeviceMonitorSession(device)
                logger.info(f"设备连接成功: {device_ip}")

                return {
                    "success": True,
                    "message": f"设备 {device_ip} 连接成功",
                    "device_ip": device_ip
                }

        return {
            "success": False,
            "message": f"设备 {device_ip} 连接失败"
        }

    except Exception as e:
        logger.error(f"连接设备失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/device/disconnect")
async def disconnect_device(config: TestConfig):
    """断开设备连接"""
    global current_monitor_session

    try:
        device_ip = config.deviceIP

        # 停止监控会话
        if current_monitor_session:
            current_monitor_session.stop()
            current_monitor_session = None

        # 从管理器移除设备
        await adb_manager.remove_device(device_ip)

        logger.info(f"设备断开: {device_ip}")
        return {
            "success": True,
            "message": f"设备 {device_ip} 已断开"
        }

    except Exception as e:
        logger.error(f"断开设备失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/device/list")
async def list_devices():
    """列出已连接的设备"""
    devices = adb_manager.get_all_devices()
    current = adb_manager.get_current_device()

    return {
        "devices": devices,
        "current_device": current.device_ip if current else None
    }


@app.post("/api/config/ai-mode")
async def set_ai_mode(mode: dict):
    """
    设置AI增强模式

    Args:
        mode: {"enabled": true/false}

    若开启时检测到 AI 不可用，会返回 ai_health 详情但仍按用户意愿置位，
    前端可据此提示用户。
    """
    global AI_ENHANCED_MODE

    enabled = bool(mode.get("enabled", False))
    AI_ENHANCED_MODE = enabled

    health = check_ai_health() if enabled else {"ok": True, "code": "ok", "reason": "AI 模式关闭"}
    logger.info(f"AI增强模式: {'开启' if enabled else '关闭'} ai_health={health['code']}")

    return {
        "success": True,
        "ai_enhanced_mode": AI_ENHANCED_MODE,
        "ai_health": health,
        "message": f"AI增强模式已{'开启' if enabled else '关闭'}",
    }


@app.get("/api/config")
async def get_config():
    """获取当前配置（含运行环境自检）"""
    adb_path = shutil.which("adb")
    return {
        "ai_enhanced_mode": AI_ENHANCED_MODE,
        "has_api_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "claude_model": DEFAULT_CLAUDE_MODEL,
        "adb_available": adb_path is not None,
        "adb_path": adb_path,
        "connected_devices": adb_manager.get_all_devices(),
        "test_running": test_running,
    }


@app.get("/api/config/ai-health")
async def get_ai_health():
    """主动探测 Claude API 是否可用（实例化 client + 一次最小请求）"""
    return check_ai_health()


@app.get("/api/test/status")
async def get_test_status():
    """获取当前测试运行状态"""
    return {
        "running": test_running
    }


@app.post("/api/error/diagnose")
async def diagnose_error(req: DiagnoseRequest):
    """
    诊断错误 - 调用错误诊断Workflow（仅 AI 增强模式可用）
    """
    if not AI_ENHANCED_MODE:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "ai_disabled",
                "reason": "错误诊断需要开启 AI 增强模式",
            },
        )

    try:
        script_path = WORKFLOW_DIR / "error-diagnosis.js"

        result = await WorkflowInvoker.invoke_workflow(
            script_path=script_path,
            args={
                "errorEvent": req.error_event.dict(),
                "deviceIP": req.device_ip
            },
            workflow_name="error-diagnosis"
        )

        return {
            "success": True,
            "workflow_id": result.get("workflow_id"),
            "diagnosis": result.get("result", {})
        }

    except AIHealthError as e:
        raise HTTPException(
            status_code=503,
            detail={"code": e.code, "reason": e.reason, "stage": "ai_invoke"},
        )
    except Exception as e:
        logger.error(f"错误诊断失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/report/generate")
async def generate_report(req: ReportRequest):
    """
    生成测试报告 - 支持本地分析和AI增强模式

    本地模式：直接计算指标并生成报告，无需API key
    AI增强模式：使用Claude API进行深度分析（需要ANTHROPIC_API_KEY）
                若 Claude 不可用，自动回退到本地模式并在响应中标注 fallback。
    """
    logger.info(f"生成报告: session={req.session_id}, 模式={'AI增强' if AI_ENHANCED_MODE else '本地分析'}")

    if AI_ENHANCED_MODE:
        try:
            script_path = WORKFLOW_DIR / "report-generation.js"
            result = await WorkflowInvoker.invoke_workflow(
                script_path=script_path,
                args={
                    "sessionId": req.session_id,
                    "testEvents": req.test_events,
                    "performanceData": req.performance_data,
                    "testConfig": req.test_config,
                },
                workflow_name="report-generation",
            )
            return {
                "success": True,
                "workflow_id": result.get("workflow_id"),
                "report": result.get("result", {}),
                "mode": "ai_enhanced",
            }
        except AIHealthError as e:
            # AI 不可用时回退到本地，避免用户拿不到报告
            logger.warning(f"AI 模式不可用，回退本地报告: {e.code} {e.reason}")
            report_data = LocalReportGenerator.generate_markdown_report(
                session_id=req.session_id,
                test_events=req.test_events,
                performance_data=req.performance_data,
                test_config=req.test_config,
            )
            return {
                "success": True,
                "workflow_id": None,
                "report": report_data,
                "mode": "local_fallback",
                "ai_health": {"ok": False, "code": e.code, "reason": e.reason},
            }
        except Exception as e:
            logger.error(f"AI 报告生成失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # 本地分析模式
    try:
        report_data = LocalReportGenerator.generate_markdown_report(
            session_id=req.session_id,
            test_events=req.test_events,
            performance_data=req.performance_data,
            test_config=req.test_config,
        )
        return {
            "success": True,
            "workflow_id": None,
            "report": report_data,
            "mode": "local",
        }
    except Exception as e:
        logger.error(f"生成报告失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """获取Workflow执行状态"""
    # TODO: 实现状态查询
    # 需要通过Claude Code API查询workflow状态
    return {
        "workflow_id": workflow_id,
        "status": "running",  # running, completed, failed
        "progress": 0.5
    }


@app.get("/api/workflow/{workflow_id}/result")
async def get_workflow_result(workflow_id: str):
    """获取Workflow执行结果"""
    # TODO: 实现结果查询
    # 需要通过Claude Code API获取workflow结果
    return {
        "workflow_id": workflow_id,
        "result": {}
    }


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket端点 - 实时推送日志

    支持真实设备监控和mock模式
    """
    await websocket.accept()
    logger.info("[WS] /ws/logs 客户端已连接")

    # mock事件模板（用于无设备时的演示）
    mock_events = [
        ("wakeup", "info", "唤醒成功 - 检测到唤醒词", "green"),
        ("recognition", "info", "语音识别开始 (onVadStart)", "blue"),
        ("recognition", "info", "语音识别结束 (onVadEnd)", "blue"),
        ("fullduplex_exit", "info", "全双工正常退出", "gray"),
        ("error", "critical", "检测到异常事件", "red"),
        ("performance_warning", "warning", "CPU占用偏高", "orange"),
    ]

    try:
        # 如果有设备监控会话，使用真实数据
        if current_monitor_session:
            logger.info("[WS] 使用真实设备日志")
            async for log_event in current_monitor_session.start_log_monitoring():
                if not test_running:
                    await asyncio.sleep(0.5)
                    continue

                await websocket.send_json(log_event)
        else:
            # Mock模式
            logger.info("[WS] 使用Mock日志数据")
            while True:
                if not test_running:
                    await asyncio.sleep(0.5)
                    continue

                evt_type, severity, desc, color = random.choice(mock_events)
                log_event = {
                    "timestamp": time.strftime("%m-%d %H:%M:%S"),
                    "type": evt_type,
                    "severity": severity,
                    "description": desc,
                    "annotation": f"[mock] {desc}",
                    "color": color,
                    "raw_log": f"{time.strftime('%m-%d %H:%M:%S')} mock log line for {evt_type}",
                }
                await websocket.send_json(log_event)
                await asyncio.sleep(3)

    except WebSocketDisconnect:
        logger.info("[WS] /ws/logs 客户端断开连接")
    except Exception as e:
        logger.error(f"[WS] /ws/logs 错误: {e}", exc_info=True)


@app.websocket("/ws/performance")
async def websocket_performance(websocket: WebSocket):
    """WebSocket端点 - 实时推送性能数据

    支持真实设备监控和mock模式
    """
    await websocket.accept()
    logger.info("[WS] /ws/performance 客户端已连接")

    try:
        # 如果有设备监控会话，使用真实数据
        if current_monitor_session:
            logger.info("[WS] 使用真实设备性能数据")
            async for perf_metric in current_monitor_session.start_performance_monitoring(interval=2.0):
                if not test_running:
                    await asyncio.sleep(0.5)
                    continue

                await websocket.send_json(perf_metric)
        else:
            # Mock模式
            logger.info("[WS] 使用Mock性能数据")
            while True:
                if not test_running:
                    await asyncio.sleep(0.5)
                    continue

                cpu_usage = round(random.uniform(3.0, 45.0), 1)
                metric = {
                    "timestamp": time.time(),
                    "cpu_usage": cpu_usage,
                    "cpu_idle": round(100.0 - cpu_usage, 1),
                    "mem_available_mb": round(random.uniform(200.0, 260.0), 2),
                    "processes": {
                        "com.cmcc.jarvis": {
                            "cpu": round(random.uniform(0.0, 40.0), 1),
                            "mem_mb": round(random.uniform(17.0, 22.0), 1),
                        },
                        "media.swcodec": {
                            "cpu": round(random.uniform(0.0, 5.0), 1),
                            "mem_mb": 11.0,
                        },
                        "audioserver": {
                            "cpu": round(random.uniform(0.0, 5.0), 1),
                            "mem_mb": 11.0,
                        },
                    },
                }
                await websocket.send_json(metric)
                await asyncio.sleep(2)

    except WebSocketDisconnect:
        logger.info("[WS] /ws/performance 客户端断开连接")
    except Exception as e:
        logger.error(f"[WS] /ws/performance 错误: {e}", exc_info=True)


@app.get("/api")
async def api_info():
    """API信息（前端页面挂载在 / ，API文档移到 /api）"""
    return {
        "name": "AI Voice Test Framework - Multi-Agent Edition",
        "version": "2.0.0",
        "description": "基于Workflow多代理编排的智能语音测试框架 - 优化版",
        "features": {
            "local_report_generation": "本地报告生成（无需API key）",
            "ai_enhanced_mode": "可选AI增强分析（需要ANTHROPIC_API_KEY）",
            "real_device_monitoring": "真实设备ADB监控",
            "mock_mode": "Mock数据模式（无设备时演示）"
        },
        "endpoints": {
            "test": {
                "start": "/api/test/start",
                "stop": "/api/test/stop",
                "status": "/api/test/status"
            },
            "device": {
                "connect": "/api/device/connect",
                "disconnect": "/api/device/disconnect",
                "list": "/api/device/list"
            },
            "monitor": "/api/monitor/start",
            "diagnose": "/api/error/diagnose",
            "report": "/api/report/generate",
            "config": {
                "get": "/api/config",
                "set_ai_mode": "/api/config/ai-mode"
            },
            "websocket": {
                "logs": "/ws/logs",
                "performance": "/ws/performance"
            }
        }
    }


# ============================================================
# 静态前端托管（必须在所有 API/WS 路由定义之后挂载，
# 否则 "/" 的 catch-all 会拦截 API 请求）
# ============================================================
_frontend_dir = resource_path("frontend/dist")
if _frontend_dir.exists() and (_frontend_dir / "index.html").exists():
    # html=True 使其在访问目录时返回 index.html，支持 SPA
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
    logger.info(f"前端静态文件已挂载: {_frontend_dir}")
else:
    logger.warning(
        f"未找到前端构建产物 ({_frontend_dir})，仅提供 API。"
        f"请先在 frontend 目录执行 npm run build。"
    )


if __name__ == "__main__":
    import uvicorn

    PORT = int(os.environ.get("PORT", "8000"))
    url = f"http://localhost:{PORT}"

    # 打包后（前端已挂载）才自动打开浏览器；纯 API 开发模式不打扰
    if _frontend_dir.exists():
        print(f"\n{'='*50}\n  AI 语音测试工具已启动\n  界面地址: {url}\n  正在打开浏览器...\n{'='*50}\n")
        open_browser_when_ready(url)

    # 打包环境下关闭 uvicorn 的彩色/重载日志噪音
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
