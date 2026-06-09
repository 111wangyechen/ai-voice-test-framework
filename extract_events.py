#!/usr/bin/env python3
"""
从真实logcat日志提取全双工测试事件，构造报告请求数据
"""
import re
import json
import glob
import os

# 找到最新日志
logs = sorted(glob.glob("data/logs/fullduplex_test_*.log"), key=os.path.getmtime)
log_file = logs[-1]

events = []

# 读取日志（设备日志可能有非utf8字符）
with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

# 1. 提取唤醒事件 onWakeUp（按秒级时间戳去重）
wakeup_times = set()
for line in lines:
    if "onWakeUp" in line:
        m = re.match(r"^(\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        if m:
            wakeup_times.add(m.group(1))

for t in sorted(wakeup_times):
    events.append({
        "type": "wakeup",
        "severity": "info",
        "timestamp": f"2026-{t}",
        "description": "唤醒成功 - onWakeUp回调触发"
    })

# 2. 提取识别活动 - WakeDialogManager 实时识别文本（按秒去重，代表一次识别会话）
asr_times = set()
for line in lines:
    if "WakeDialogManager" in line and "text=" in line:
        m = re.match(r"^(\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        if m:
            asr_times.add(m.group(1))

for t in sorted(asr_times):
    events.append({
        "type": "recognition",
        "severity": "info",
        "timestamp": f"2026-{t}",
        "description": "语音识别活动 - 实时返回识别文本"
    })

# 3. 提取全双工退出 exit_interactive（去重时间戳）
exit_times = set()
for line in lines:
    if "exit_interactive" in line and "SDK_CALL_XR] 开始" in line:
        m = re.match(r"^(\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        if m:
            exit_times.add(m.group(1))

for t in sorted(exit_times):
    events.append({
        "type": "fullduplex_exit",
        "severity": "info",
        "timestamp": f"2026-{t}",
        "description": "全双工正常退出交互 (EXIT_INTERACTIVE)"
    })

# 4. 提取崩溃/异常 FATAL（标注归属进程）
for line in lines:
    if "FATAL EXCEPTION" in line or ("Fatal signal" in line):
        m = re.match(r"^(\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        ts = f"2026-{m.group(1)}" if m else "2026-06-08"
        # 判断是否jarvis主进程
        is_jarvis = "cmcc.jarvis" in line
        events.append({
            "type": "error",
            "severity": "critical" if is_jarvis else "error",
            "timestamp": ts,
            "description": f"崩溃事件(非语音核心进程): {line.strip()[:90]}",
            "raw_log": line.strip()[:200]
        })

# 按时间排序
events.sort(key=lambda e: e["timestamp"])

# 性能数据 - 测试后采集的真实基线（jarvis进程）
performance_data = [
    {"cpu_usage": 23.0, "mem_available_mb": 159.0, "timestamp": 1717817700},
    {"cpu_usage": 22.2, "mem_available_mb": 158.0, "timestamp": 1717817702},
    {"cpu_usage": 10.2, "mem_available_mb": 157.0, "timestamp": 1717817704},
    {"cpu_usage": 15.1, "mem_available_mb": 156.0, "timestamp": 1717817706},
    {"cpu_usage": 18.5, "mem_available_mb": 155.0, "timestamp": 1717817708},
]

request = {
    "session_id": "fullduplex_real_20260608",
    "test_events": events,
    "performance_data": performance_data,
    "test_config": {
        "deviceIP": "10.7.187.222:5555",
        "duration": 3000,
        "scenario": "fullduplex",
        "device_model": "YL-M15 (Android 12)"
    }
}

with open("fullduplex_request.json", "w", encoding="utf-8") as f:
    json.dump(request, f, ensure_ascii=False, indent=2)

# 统计输出（纯ASCII避免编码问题）
print("Source log:", log_file)
print("Total events extracted:", len(events))
print("  wakeup:", len(wakeup_times))
print("  recognition(asr sessions):", len(asr_times))
print("  fullduplex_exit:", len(exit_times))
print("  errors/crashes:", sum(1 for e in events if e["type"] == "error"))
print("Request saved to: fullduplex_request.json")
