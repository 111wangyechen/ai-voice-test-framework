#!/bin/bash
# 实时监控Android设备性能指标
# 用于诊断全双工语音测试中的唤醒卡顿问题

DEVICE="10.7.187.15:5555"
LOG_FILE="performance_monitor_$(date +%Y%m%d_%H%M%S).log"

echo "=== 开始实时监控设备 $DEVICE ===" | tee -a "$LOG_FILE"
echo "日志文件: $LOG_FILE"
echo "按 Ctrl+C 停止监控"
echo ""

# 获取语音相关进程名（根据实际情况调整）
# 常见的进程：com.android.bluetooth, mediaserver, audioserver, 语音助手包名等
VOICE_PROCESSES="mediaserver|audioserver|bluetooth|voice|assistant"

# 监控循环
COUNTER=0
while true; do
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    COUNTER=$((COUNTER + 1))

    echo "========== [$TIMESTAMP] 监控轮次 #$COUNTER ==========" | tee -a "$LOG_FILE"

    # 1. CPU使用率
    echo "" | tee -a "$LOG_FILE"
    echo "--- CPU使用率 ---" | tee -a "$LOG_FILE"
    adb -s "$DEVICE" shell "top -n 1 -m 10 | head -20" 2>&1 | tee -a "$LOG_FILE"

    # 2. 内存使用情况
    echo "" | tee -a "$LOG_FILE"
    echo "--- 内存使用情况 ---" | tee -a "$LOG_FILE"
    adb -s "$DEVICE" shell "dumpsys meminfo | grep -A 5 'Total RAM'" 2>&1 | tee -a "$LOG_FILE"
    adb -s "$DEVICE" shell "cat /proc/meminfo | grep -E 'MemTotal|MemFree|MemAvailable|Cached'" 2>&1 | tee -a "$LOG_FILE"

    # 3. 语音相关进程状态
    echo "" | tee -a "$LOG_FILE"
    echo "--- 语音相关进程 ---" | tee -a "$LOG_FILE"
    adb -s "$DEVICE" shell "ps -A | grep -E '$VOICE_PROCESSES'" 2>&1 | tee -a "$LOG_FILE"

    # 4. 音频服务状态
    echo "" | tee -a "$LOG_FILE"
    echo "--- 音频服务状态 ---" | tee -a "$LOG_FILE"
    adb -s "$DEVICE" shell "dumpsys audio | grep -A 3 'Audio Routing:'" 2>&1 | tee -a "$LOG_FILE"

    # 5. 蓝牙连接状态（如果使用蓝牙）
    echo "" | tee -a "$LOG_FILE"
    echo "--- 蓝牙连接状态 ---" | tee -a "$LOG_FILE"
    adb -s "$DEVICE" shell "dumpsys bluetooth_manager | grep -A 5 'Bluetooth Status'" 2>&1 | tee -a "$LOG_FILE"

    # 6. 最近的logcat日志（包含唤醒、语音相关）
    echo "" | tee -a "$LOG_FILE"
    echo "--- 最近5秒日志（唤醒/语音相关）---" | tee -a "$LOG_FILE"
    adb -s "$DEVICE" shell "logcat -d -t '5 seconds ago' | grep -i -E 'wakeup|wake|voice|audio|speech|recognition'" 2>&1 | tail -50 | tee -a "$LOG_FILE"

    # 7. CPU频率（用于检测降频）
    echo "" | tee -a "$LOG_FILE"
    echo "--- CPU频率 ---" | tee -a "$LOG_FILE"
    adb -s "$DEVICE" shell "cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq" 2>&1 | head -8 | tee -a "$LOG_FILE"

    # 8. 温度（可能导致降频）
    echo "" | tee -a "$LOG_FILE"
    echo "--- 设备温度 ---" | tee -a "$LOG_FILE"
    adb -s "$DEVICE" shell "dumpsys battery | grep temperature" 2>&1 | tee -a "$LOG_FILE"

    echo "" | tee -a "$LOG_FILE"
    echo "================================================" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"

    # 每5秒采集一次
    sleep 5
done
