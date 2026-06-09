#!/usr/bin/env python3
"""
WebSocket客户端测试 - 接收真实设备数据
"""
import asyncio
import websockets
import json
import signal
import sys

# 全局标志
should_exit = False

def signal_handler(sig, frame):
    global should_exit
    print('\n[中断] 正在退出...')
    should_exit = True

signal.signal(signal.SIGINT, signal_handler)

async def test_logs_websocket():
    """测试日志WebSocket"""
    uri = "ws://localhost:8000/ws/logs"
    print(f"[日志] 连接到 {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("[日志] 已连接，等待数据...")
            count = 0

            while not should_exit and count < 10:  # 接收10条日志
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    count += 1

                    print(f"\n[日志 #{count}]")
                    print(f"  时间: {data.get('timestamp')}")
                    print(f"  类型: {data.get('type')}")
                    print(f"  严重程度: {data.get('severity')}")
                    print(f"  描述: {data.get('description')}")
                    print(f"  原始日志: {data.get('raw_log', '')[:80]}...")

                except asyncio.TimeoutError:
                    print("[日志] 等待超时，继续...")
                    continue

    except Exception as e:
        print(f"[日志] 错误: {e}")

async def test_performance_websocket():
    """测试性能WebSocket"""
    uri = "ws://localhost:8000/ws/performance"
    print(f"\n[性能] 连接到 {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("[性能] 已连接，等待数据...")
            count = 0

            while not should_exit and count < 5:  # 接收5条性能数据
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    count += 1

                    print(f"\n[性能 #{count}]")
                    print(f"  CPU使用: {data.get('cpu_usage')}%")
                    print(f"  CPU空闲: {data.get('cpu_idle')}%")
                    print(f"  可用内存: {data.get('mem_available_mb')} MB")

                    processes = data.get('processes', {})
                    if processes:
                        print(f"  关键进程:")
                        for proc_name, proc_info in list(processes.items())[:3]:
                            print(f"    - {proc_name}: CPU {proc_info.get('cpu')}%, MEM {proc_info.get('mem_mb')} MB")

                except asyncio.TimeoutError:
                    print("[性能] 等待超时，继续...")
                    continue

    except Exception as e:
        print(f"[性能] 错误: {e}")

async def main():
    """主函数"""
    print("=" * 60)
    print("WebSocket客户端测试 - 真实设备数据")
    print("设备: 10.7.187.34:5555 (ZXWT LS02)")
    print("按 Ctrl+C 退出")
    print("=" * 60)

    # 并行测试两个WebSocket
    await asyncio.gather(
        test_logs_websocket(),
        test_performance_websocket()
    )

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已退出")
        sys.exit(0)
