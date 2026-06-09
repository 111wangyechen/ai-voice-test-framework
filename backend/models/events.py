"""
数据模型 - 事件定义
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """事件类型"""
    WAKEUP = "wakeup"                      # 唤醒
    WAKEUP_ATTEMPT = "wakeup_attempt"      # 唤醒尝试
    RECOGNITION = "recognition"            # 识别
    FULLDUPLEX_EXIT = "fullduplex_exit"    # 全双工退出
    ERROR = "error"                        # 错误
    PERFORMANCE_WARNING = "performance_warning"  # 性能警告
    TEST_START = "test_start"              # 测试开始
    TEST_END = "test_end"                  # 测试结束
    APPROVAL_REQUEST = "approval_request"  # 审核请求


class EventSeverity(str, Enum):
    """事件严重程度"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Event(BaseModel):
    """事件基类"""
    id: str = Field(default_factory=lambda: f"evt_{datetime.now().timestamp()}")
    type: EventType
    severity: EventSeverity
    timestamp: datetime = Field(default_factory=datetime.now)
    annotation: str  # AI标注文本
    color: str  # 前端显示颜色
    details: Dict[str, Any] = Field(default_factory=dict)
    raw_log: Optional[str] = None  # 原始日志行

    class Config:
        use_enum_values = True


class WakeupEvent(Event):
    """唤醒事件"""
    type: EventType = EventType.WAKEUP
    success: bool
    confidence: Optional[float] = None

    def __init__(self, **data):
        if 'severity' not in data:
            data['severity'] = EventSeverity.INFO
        if 'annotation' not in data:
            data['annotation'] = "✓ 唤醒成功" if data.get('success') else "✗ 唤醒失败"
        if 'color' not in data:
            data['color'] = "green" if data.get('success') else "red"
        super().__init__(**data)


class RecognitionEvent(Event):
    """识别事件"""
    type: EventType = EventType.RECOGNITION
    text: str  # 识别文本
    expected_text: Optional[str] = None  # 预期文本
    is_correct: Optional[bool] = None  # 是否正确
    confidence: Optional[float] = None

    def __init__(self, **data):
        if 'severity' not in data:
            data['severity'] = EventSeverity.INFO
        if 'annotation' not in data:
            data['annotation'] = f"🎤 识别: {data.get('text', '')}"
        if 'color' not in data:
            data['color'] = "blue"
        super().__init__(**data)


class FullDuplexExitEvent(Event):
    """全双工退出事件"""
    type: EventType = EventType.FULLDUPLEX_EXIT
    unexpected: bool  # 是否为非预期退出
    reason: Optional[str] = None
    context_logs: list[str] = Field(default_factory=list)  # 上下文日志

    def __init__(self, **data):
        if 'severity' not in data:
            data['severity'] = EventSeverity.CRITICAL if data.get('unexpected') else EventSeverity.INFO
        if 'annotation' not in data:
            data['annotation'] = "⚠ 全双工非预期退出" if data.get('unexpected') else "ℹ 全双工正常退出"
        if 'color' not in data:
            data['color'] = "red" if data.get('unexpected') else "gray"
        super().__init__(**data)


class PerformanceWarningEvent(Event):
    """性能警告事件"""
    type: EventType = EventType.PERFORMANCE_WARNING
    warning_type: str  # cpu_overload, low_memory, swcodec_overload
    metric_value: float
    threshold: float

    def __init__(self, **data):
        if 'severity' not in data:
            data['severity'] = EventSeverity.WARNING
        if 'annotation' not in data:
            data['annotation'] = f"⚡ {data.get('warning_type', 'performance')}: {data.get('metric_value')}"
        if 'color' not in data:
            data['color'] = "orange"
        super().__init__(**data)


class PerformanceMetrics(BaseModel):
    """性能指标"""
    timestamp: float
    cpu_usage: float  # CPU使用率 (%)
    cpu_idle: float   # CPU空闲率 (%)
    mem_total: int    # 总内存 (KB)
    mem_available: int  # 可用内存 (KB)
    mem_used: int     # 已用内存 (KB)
    swap_total: int   # 总Swap (KB)
    swap_free: int    # 可用Swap (KB)
    processes: Dict[str, 'ProcessMetrics'] = Field(default_factory=dict)


class ProcessMetrics(BaseModel):
    """进程指标"""
    pid: int
    name: str
    cpu: float  # CPU占用 (%)
    mem: float  # 内存占用 (%)
    mem_rss: int  # RSS内存 (KB)


class TestMetrics(BaseModel):
    """测试指标"""
    session_id: str
    wakeup_rate: float  # 唤醒率
    recognition_rate: float  # 识别率
    fullduplex_stability: float  # 全双工稳定性
    avg_response_time: Optional[float] = None  # 平均响应时延(ms)
    total_wakeup_attempts: int = 0
    successful_wakeups: int = 0
    total_recognitions: int = 0
    correct_recognitions: int = 0
    unexpected_exits: int = 0
    dialog_rounds: int = 0
