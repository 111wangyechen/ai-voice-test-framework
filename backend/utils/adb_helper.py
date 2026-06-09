"""
ADB设备管理工具 - 使用subprocess调用adb命令
"""
import asyncio
import re
import logging
import subprocess
from typing import Optional, List

logger = logging.getLogger(__name__)


class ADBDevice:
    """ADB设备封装类"""

    def __init__(self, device_ip: str):
        """
        初始化ADB设备

        Args:
            device_ip: 设备IP地址（格式: ip:port，如 10.7.187.15:5555）
        """
        self.device_ip = device_ip
        self.is_connected = False

    async def connect(self) -> bool:
        """连接设备"""
        try:
            # 连接设备
            result = await asyncio.create_subprocess_exec(
                'adb', 'connect', self.device_ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            output = stdout.decode('utf-8', errors='ignore')

            if "connected" in output.lower() or "already connected" in output.lower():
                self.is_connected = True
                logger.info(f"已连接到设备: {self.device_ip}")
                return True
            else:
                logger.error(f"连接设备失败: {output}")
                return False

        except Exception as e:
            logger.error(f"连接设备异常: {e}")
            return False

    async def disconnect(self):
        """断开设备连接"""
        try:
            result = await asyncio.create_subprocess_exec(
                'adb', 'disconnect', self.device_ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            self.is_connected = False
            logger.info(f"已断开设备: {self.device_ip}")
        except Exception as e:
            logger.error(f"断开设备异常: {e}")

    async def shell(self, command: str) -> str:
        """
        执行shell命令

        Args:
            command: shell命令

        Returns:
            命令输出
        """
        if not self.is_connected:
            raise RuntimeError("设备未连接")

        try:
            result = await asyncio.create_subprocess_exec(
                'adb', '-s', self.device_ip, 'shell', command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            return stdout.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"执行shell命令失败: {command}, 错误: {e}")
            return ""

    async def get_pid(self, package_name: str) -> Optional[int]:
        """
        获取应用进程PID

        Args:
            package_name: 应用包名

        Returns:
            进程PID，未找到返回None
        """
        output = await self.shell(f"ps -A | grep {package_name}")
        if output:
            # 解析第一列的PID
            match = re.search(r'^\s*(\d+)', output)
            if match:
                return int(match.group(1))
        return None

    async def logcat_stream(self):
        """
        启动logcat流（异步生成器）

        Yields:
            日志行
        """
        if not self.is_connected:
            raise RuntimeError("设备未连接")

        # 使用asyncio.create_subprocess_exec执行logcat
        process = await asyncio.create_subprocess_exec(
            'adb', '-s', self.device_ip, 'logcat', '-v', 'time',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break

                decoded_line = line.decode('utf-8', errors='ignore').strip()
                if decoded_line:
                    yield decoded_line

        except asyncio.CancelledError:
            logger.info("Logcat流已取消")
            process.kill()
            await process.wait()
        except Exception as e:
            logger.error(f"Logcat流异常: {e}")
            process.kill()
            await process.wait()

    async def get_top_info(self) -> str:
        """获取top信息（CPU和内存）"""
        return await self.shell("top -n 1 -b | head -20")

    async def get_meminfo(self) -> str:
        """获取内存信息"""
        return await self.shell("cat /proc/meminfo")

    async def get_dumpsys_meminfo(self, package_name: str) -> str:
        """
        获取应用内存详情

        Args:
            package_name: 应用包名
        """
        return await self.shell(f"dumpsys meminfo {package_name}")


class ADBManager:
    """ADB设备管理器（支持多设备扩展）"""

    def __init__(self):
        self.devices: dict[str, ADBDevice] = {}
        self.current_device: Optional[ADBDevice] = None

    async def add_device(self, device_ip: str) -> bool:
        """
        添加设备

        Args:
            device_ip: 设备IP

        Returns:
            是否成功
        """
        if device_ip in self.devices:
            logger.warning(f"设备已存在: {device_ip}")
            return True

        device = ADBDevice(device_ip)
        success = await device.connect()

        if success:
            self.devices[device_ip] = device
            if self.current_device is None:
                self.current_device = device
            return True
        return False

    async def remove_device(self, device_ip: str):
        """移除设备"""
        if device_ip in self.devices:
            await self.devices[device_ip].disconnect()
            del self.devices[device_ip]

            if self.current_device and self.current_device.device_ip == device_ip:
                self.current_device = next(iter(self.devices.values()), None)

    async def switch_device(self, device_ip: str) -> bool:
        """
        切换当前设备

        Args:
            device_ip: 目标设备IP

        Returns:
            是否成功
        """
        if device_ip not in self.devices:
            logger.error(f"设备不存在: {device_ip}")
            return False

        self.current_device = self.devices[device_ip]
        logger.info(f"已切换到设备: {device_ip}")
        return True

    def get_current_device(self) -> Optional[ADBDevice]:
        """获取当前设备"""
        return self.current_device

    def get_all_devices(self) -> List[str]:
        """获取所有设备IP列表"""
        return list(self.devices.keys())
