"""
本地报告生成器 - 不依赖外部API
直接从测试数据计算指标并生成Markdown报告
"""
from typing import List, Dict, Any
from datetime import datetime
import statistics


class LocalReportGenerator:
    """本地报告生成器"""

    @staticmethod
    def generate_markdown_report(
        session_id: str,
        test_events: List[Dict[str, Any]],
        performance_data: List[Dict[str, Any]],
        test_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成完整的测试报告

        Args:
            session_id: 测试会话ID
            test_events: 测试事件列表
            performance_data: 性能数据列表
            test_config: 测试配置

        Returns:
            包含markdown内容和统计数据的字典
        """
        # 计算各项指标
        stats = LocalReportGenerator._calculate_statistics(test_events, performance_data)

        # 生成Markdown内容
        markdown = LocalReportGenerator._format_markdown(
            session_id, test_config, stats, test_events, performance_data
        )

        return {
            "markdown": markdown,
            "statistics": stats,
            "summary": {
                "total_events": len(test_events),
                "test_duration": stats.get("test_duration", 0),
                "overall_score": LocalReportGenerator._calculate_score(stats)
            }
        }

    @staticmethod
    def _calculate_statistics(
        test_events: List[Dict[str, Any]],
        performance_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算测试统计数据"""

        # 初始化计数器
        event_counts = {
            "wakeup": 0,
            "wakeup_failed": 0,
            "recognition": 0,
            "recognition_failed": 0,
            "fullduplex_exit": 0,
            "fullduplex_crash": 0,
            "error": 0,
            "warning": 0,
            "critical": 0
        }

        # 统计事件
        for event in test_events:
            event_type = event.get("type", "")
            severity = event.get("severity", "")

            if event_type in event_counts:
                event_counts[event_type] += 1

            if severity in ["error", "warning", "critical"]:
                event_counts[severity] += 1

        # 计算唤醒率
        total_wakeup_attempts = event_counts["wakeup"] + event_counts["wakeup_failed"]
        wakeup_rate = (event_counts["wakeup"] / total_wakeup_attempts * 100) if total_wakeup_attempts > 0 else 0

        # 计算识别率
        total_recognition_attempts = event_counts["recognition"] + event_counts["recognition_failed"]
        recognition_rate = (event_counts["recognition"] / total_recognition_attempts * 100) if total_recognition_attempts > 0 else 0

        # 计算全双工稳定性
        total_fullduplex = event_counts["fullduplex_exit"] + event_counts["fullduplex_crash"]
        fullduplex_stability = (event_counts["fullduplex_exit"] / total_fullduplex * 100) if total_fullduplex > 0 else 100

        # 性能统计
        cpu_usages = [d.get("cpu_usage", 0) for d in performance_data if "cpu_usage" in d]
        mem_available = [d.get("mem_available_mb", 0) for d in performance_data if "mem_available_mb" in d]

        perf_stats = {}
        if cpu_usages:
            perf_stats["cpu_avg"] = statistics.mean(cpu_usages)
            perf_stats["cpu_max"] = max(cpu_usages)
            perf_stats["cpu_min"] = min(cpu_usages)

        if mem_available:
            perf_stats["mem_avg"] = statistics.mean(mem_available)
            perf_stats["mem_min"] = min(mem_available)

        # 计算测试时长
        test_duration = 0
        if test_events and len(test_events) > 1:
            try:
                first_time = datetime.fromisoformat(test_events[0].get("timestamp", ""))
                last_time = datetime.fromisoformat(test_events[-1].get("timestamp", ""))
                test_duration = (last_time - first_time).total_seconds()
            except:
                test_duration = len(test_events) * 3  # 粗略估算

        return {
            **event_counts,
            "wakeup_rate": round(wakeup_rate, 2),
            "recognition_rate": round(recognition_rate, 2),
            "fullduplex_stability": round(fullduplex_stability, 2),
            "test_duration": round(test_duration, 2),
            **perf_stats
        }

    @staticmethod
    def _calculate_score(stats: Dict[str, Any]) -> int:
        """计算总体评分 (0-100)"""
        score = 100

        # 唤醒率影响 (-30分)
        wakeup_rate = stats.get("wakeup_rate", 100)
        if wakeup_rate < 95:
            score -= (95 - wakeup_rate) * 0.6

        # 识别率影响 (-30分)
        recognition_rate = stats.get("recognition_rate", 100)
        if recognition_rate < 95:
            score -= (95 - recognition_rate) * 0.6

        # 全双工稳定性影响 (-20分)
        fullduplex_stability = stats.get("fullduplex_stability", 100)
        if fullduplex_stability < 95:
            score -= (95 - fullduplex_stability) * 0.4

        # 错误数量影响 (-20分)
        error_count = stats.get("error", 0) + stats.get("critical", 0) * 2
        score -= min(error_count * 2, 20)

        return max(0, min(100, int(score)))

    @staticmethod
    def _format_markdown(
        session_id: str,
        test_config: Dict[str, Any],
        stats: Dict[str, Any],
        test_events: List[Dict[str, Any]],
        performance_data: List[Dict[str, Any]]
    ) -> str:
        """生成Markdown格式的报告"""

        report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        device_ip = test_config.get("deviceIP", "未知")
        scenario = test_config.get("scenario", "未知")
        duration = test_config.get("duration", 0)
        overall_score = LocalReportGenerator._calculate_score(stats)

        # 评级
        if overall_score >= 90:
            grade = "优秀 ✅"
        elif overall_score >= 75:
            grade = "良好 ⚠️"
        elif overall_score >= 60:
            grade = "及格 ⚠️"
        else:
            grade = "不及格 ❌"

        markdown = f"""# 语音测试报告

## 基本信息

- **测试会话ID**: {session_id}
- **生成时间**: {report_time}
- **测试设备**: {device_ip}
- **测试场景**: {scenario}
- **测试时长**: {stats.get('test_duration', duration)}秒
- **总体评分**: {overall_score}/100 ({grade})

---

## 核心指标

### 1. 唤醒性能

| 指标 | 数值 | 评价 |
|------|------|------|
| 唤醒成功次数 | {stats.get('wakeup', 0)} | - |
| 唤醒失败次数 | {stats.get('wakeup_failed', 0)} | - |
| **唤醒率** | **{stats.get('wakeup_rate', 0):.2f}%** | {'✅ 优秀' if stats.get('wakeup_rate', 0) >= 95 else '⚠️ 需改进' if stats.get('wakeup_rate', 0) >= 85 else '❌ 较差'} |

### 2. 语音识别性能

| 指标 | 数值 | 评价 |
|------|------|------|
| 识别成功次数 | {stats.get('recognition', 0)} | - |
| 识别失败次数 | {stats.get('recognition_failed', 0)} | - |
| **识别率** | **{stats.get('recognition_rate', 0):.2f}%** | {'✅ 优秀' if stats.get('recognition_rate', 0) >= 95 else '⚠️ 需改进' if stats.get('recognition_rate', 0) >= 85 else '❌ 较差'} |

### 3. 全双工稳定性

| 指标 | 数值 | 评价 |
|------|------|------|
| 正常退出次数 | {stats.get('fullduplex_exit', 0)} | - |
| 异常崩溃次数 | {stats.get('fullduplex_crash', 0)} | - |
| **稳定性** | **{stats.get('fullduplex_stability', 0):.2f}%** | {'✅ 稳定' if stats.get('fullduplex_stability', 0) >= 95 else '⚠️ 需关注' if stats.get('fullduplex_stability', 0) >= 85 else '❌ 不稳定'} |

---

## 设备性能分析

"""

        # 性能数据
        if stats.get("cpu_avg"):
            cpu_status = "正常" if stats.get("cpu_avg", 0) < 50 else "偏高" if stats.get("cpu_avg", 0) < 70 else "过高"
            cpu_icon = "✅" if stats.get("cpu_avg", 0) < 50 else "⚠️" if stats.get("cpu_avg", 0) < 70 else "❌"

            markdown += f"""### CPU使用情况

| 指标 | 数值 | 状态 |
|------|------|------|
| 平均CPU占用 | {stats.get('cpu_avg', 0):.1f}% | {cpu_icon} {cpu_status} |
| 峰值CPU占用 | {stats.get('cpu_max', 0):.1f}% | - |
| 最低CPU占用 | {stats.get('cpu_min', 0):.1f}% | - |

"""

        if stats.get("mem_avg"):
            mem_status = "充足" if stats.get("mem_avg", 0) > 200 else "紧张" if stats.get("mem_avg", 0) > 150 else "不足"
            mem_icon = "✅" if stats.get("mem_avg", 0) > 200 else "⚠️" if stats.get("mem_avg", 0) > 150 else "❌"

            markdown += f"""### 内存使用情况

| 指标 | 数值 | 状态 |
|------|------|------|
| 平均可用内存 | {stats.get('mem_avg', 0):.1f} MB | {mem_icon} {mem_status} |
| 最小可用内存 | {stats.get('mem_min', 0):.1f} MB | - |

"""

        # 问题汇总
        markdown += f"""---

## 问题汇总

### 错误统计

| 级别 | 数量 |
|------|------|
| 严重错误 (Critical) | {stats.get('critical', 0)} |
| 一般错误 (Error) | {stats.get('error', 0)} |
| 警告 (Warning) | {stats.get('warning', 0)} |

"""

        # 关键问题列表
        critical_events = [e for e in test_events if e.get("severity") in ["critical", "error"]]
        if critical_events:
            markdown += "### 关键问题列表\n\n"
            for i, event in enumerate(critical_events[:10], 1):  # 最多显示10条
                markdown += f"{i}. **[{event.get('severity', '').upper()}]** {event.get('description', '未知错误')} - {event.get('timestamp', '')}\n"

            if len(critical_events) > 10:
                markdown += f"\n*...还有 {len(critical_events) - 10} 条错误未显示*\n"
        else:
            markdown += "### ✅ 未发现严重问题\n"

        markdown += f"""
---

## 建议与总结

"""

        # 根据问题给出建议
        suggestions = []

        if stats.get('wakeup_rate', 100) < 90:
            suggestions.append("- ⚠️ **唤醒率偏低**：检查唤醒词配置、麦克风灵敏度和环境噪声")

        if stats.get('recognition_rate', 100) < 90:
            suggestions.append("- ⚠️ **识别率偏低**：检查语音模型版本、网络连接和音频质量")

        if stats.get('fullduplex_stability', 100) < 90:
            suggestions.append("- ⚠️ **全双工不稳定**：检查音频焦点管理、播放器状态和系统资源")

        if stats.get('cpu_avg', 0) > 60:
            suggestions.append("- ⚠️ **CPU占用过高**：优化算法、减少后台任务或升级硬件")

        if stats.get('mem_avg', 0) < 180:
            suggestions.append("- ⚠️ **内存紧张**：关闭不必要的应用、检查内存泄漏")

        if stats.get('critical', 0) > 0:
            suggestions.append(f"- ❌ **发现{stats.get('critical', 0)}个严重错误**：需要立即排查和修复")

        if not suggestions:
            suggestions.append("- ✅ **测试表现良好**：所有指标均在正常范围内")

        markdown += "\n".join(suggestions)

        markdown += f"""

---

## 数据汇总

- 总事件数: {len(test_events)}
- 性能采样点: {len(performance_data)}
- 报告生成方式: 本地分析引擎 (无需API)

*本报告由AI辅助语音测试框架自动生成*
"""

        return markdown
