"""
设备实时监控模块 - 解析logcat和性能数据
"""
import re
import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from utils.adb_helper import ADBDevice

logger = logging.getLogger(__name__)


class LogEventParser:
    """日志事件解析器"""

    # 关键日志模式
    PATTERNS = {
        "wakeup": [
            (r"唤醒成功|wakeup.*success|检测到唤醒词", "info", "唤醒成功"),
            (r"唤醒失败|wakeup.*fail", "error", "唤醒失败"),
        ],
        "recognition": [
            (r"onVadStart|开始识别", "info", "语音识别开始"),
            (r"onVadEnd|识别结束", "info", "语音识别结束"),
            (r"识别失败|recognition.*error", "error", "语音识别失败"),
        ],
        "fullduplex": [
            (r"全双工退出|exitFullduplex", "info", "全双工正常退出"),
            (r"全双工异常|fullduplex.*crash|fullduplex.*error", "critical", "全双工异常退出"),
        ],
        "error": [
            (r"E\/AudioFlinger|E\/AudioTrack", "error", "音频系统错误"),
            (r"MediaSessionManager.*error", "error", "媒体会话管理错误"),
            (r"ANR|Application Not Responding", "critical", "应用无响应"),
            (r"FATAL|Fatal Exception", "critical", "严重异常"),
        ],
    }

    @staticmethod
    def parse_log_line(log_line: str) -> Optional[Dict[str, Any]]:
        """
        解析单行日志

        Args:
            log_line: 原始日志行

        Returns:
            解析后的事件字典，无匹配则返回None
        """
        # 提取时间戳（logcat -v time格式: 06-05 18:30:45.123）
        time_match = re.match(r'^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', log_line)
        timestamp = time_match.group(1) if time_match else datetime.now().strftime("%m-%d %H:%M:%S")

        # 匹配各类事件
        for event_type, patterns in LogEventParser.PATTERNS.items():
            for pattern, severity, description in patterns:
                if re.search(pattern, log_line, re.IGNORECASE):
                    return {
                        "timestamp": timestamp,
                        "type": event_type,
                        "severity": severity,
                        "description": description,
                        "annotation": f"[{event_type}] {description}",
                        "color": LogEventParser._get_color(severity),
                        "raw_log": log_line[:200],  # 限制长度
                    }

        return None

    @staticmethod
    def _get_color(severity: str) -> str:
        """根据严重程度返回颜色"""
        color_map = {
            "info": "blue",
            "warning": "orange",
            "error": "red",
            "critical": "red",
        }
        return color_map.get(severity, "gray")


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, device: ADBDevice):
        self.device = device
        self.target_processes = [
            "com.cmcc.jarvis",
            "media.swcodec",
            "audioserver",
            "com.android.bluetooth",
        ]

    async def get_performance_snapshot(self) -> Dict[str, Any]:
        """
        获取性能快照

        Returns:
            性能指标字典
        """
        try:
            # 获取CPU和内存信息
            top_output = await self.device.get_top_info()
            meminfo_output = await self.device.get_meminfo()

            # 解析CPU使用率
            cpu_usage, cpu_idle = self._parse_cpu_usage(top_output)

            # 解析可用内存
            mem_available = self._parse_memory(meminfo_output)

            # 解析进程信息
            processes = self._parse_process_info(top_output)

            return {
                "timestamp": datetime.now().timestamp(),
                "cpu_usage": cpu_usage,
                "cpu_idle": cpu_idle,
                "mem_available_mb": mem_available,
                "processes": processes,
            }

        except Exception as e:
            logger.error(f"获取性能数据失败: {e}")
            return self._get_fallback_metric()

    def _parse_cpu_usage(self, top_output: str) -> tuple[float, float]:
        """解析CPU使用率"""
        # 匹配类似: %Cpu(s):  5.2 us,  2.1 sy,  0.0 ni, 92.7 id
        # 或 Android top格式
        match = re.search(r'(\d+\.?\d*)%cpu\s+(\d+\.?\d*)%idle', top_output, re.IGNORECASE)
        if match:
            cpu_usage = float(match.group(1))
            cpu_idle = float(match.group(2))
            return cpu_usage, cpu_idle

        # 尝试另一种格式
        match = re.search(r'idle\s+(\d+)%', top_output, re.IGNORECASE)
        if match:
            cpu_idle = float(match.group(1))
            cpu_usage = 100.0 - cpu_idle
            return cpu_usage, cpu_idle

        return 0.0, 100.0

    def _parse_memory(self, meminfo_output: str) -> float:
        """解析可用内存（MB）"""
        # 匹配 MemAvailable 或 MemFree
        match = re.search(r'MemAvailable:\s+(\d+)\s+kB', meminfo_output)
        if match:
            return float(match.group(1)) / 1024  # KB to MB

        match = re.search(r'MemFree:\s+(\d+)\s+kB', meminfo_output)
        if match:
            return float(match.group(1)) / 1024

        return 0.0

    def _parse_process_info(self, top_output: str) -> Dict[str, Dict[str, float]]:
        """解析进程信息"""
        processes = {}

        for line in top_output.split('\n'):
            for proc_name in self.target_processes:
                if proc_name in line:
                    # 解析CPU和内存（top输出格式可能不同，这里做通用解析）
                    # 典型格式: PID USER  PR NI CPU% MEM   TIME+ NAME
                    parts = line.split()
                    if len(parts) >= 9:
                        try:
                            cpu_pct = float(parts[8].rstrip('%'))
                            mem_mb = float(parts[5]) / 1024 if parts[5].isdigit() else 0.0

                            processes[proc_name] = {
                                "cpu": round(cpu_pct, 1),
                                "mem_mb": round(mem_mb, 1),
                            }
                        except (ValueError, IndexError):
                            pass

        return processes

    def _get_fallback_metric(self) -> Dict[str, Any]:
        """返回fallback性能数据"""
        return {
            "timestamp": datetime.now().timestamp(),
            "cpu_usage": 0.0,
            "cpu_idle": 100.0,
            "mem_available_mb": 0.0,
            "processes": {},
        }


class DeviceMonitorSession:
    """设备监控会话"""

    def __init__(self, device: ADBDevice):
        self.device = device
        self.performance_monitor = PerformanceMonitor(device)
        self.log_task: Optional[asyncio.Task] = None
        self.perf_task: Optional[asyncio.Task] = None
        self.running = False

    async def start_log_monitoring(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        启动日志监控（异步生成器）

        Yields:
            解析后的日志事件
        """
        self.running = True
        logger.info(f"开始监控设备日志: {self.device.device_ip}")

        try:
            async for log_line in self.device.logcat_stream():
                if not self.running:
                    break

                # 解析日志行
                event = LogEventParser.parse_log_line(log_line)
                if event:
                    yield event

        except asyncio.CancelledError:
            logger.info("日志监控已停止")
        except Exception as e:
            logger.error(f"日志监控异常: {e}")
        finally:
            self.running = False

    async def start_performance_monitoring(
        self, interval: float = 2.0
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        启动性能监控（异步生成器）

        Args:
            interval: 采样间隔（秒）

        Yields:
            性能快照
        """
        self.running = True
        logger.info(f"开始监控设备性能: {self.device.device_ip}")

        try:
            while self.running:
                snapshot = await self.performance_monitor.get_performance_snapshot()
                yield snapshot
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            logger.info("性能监控已停止")
        except Exception as e:
            logger.error(f"性能监控异常: {e}")
        finally:
            self.running = False

    def stop(self):
        """停止监控"""
        self.running = False
        logger.info(f"停止设备监控: {self.device.device_ip}")
