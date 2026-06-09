#!/usr/bin/env python3
import re
import json
import sys

def parse_performance_data(file_path):
    metrics = []
    warnings = []

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Split into samples
    samples = re.split(r'===SAMPLE_START:(\d+)===', content)

    for i in range(1, len(samples), 2):
        if i+1 >= len(samples):
            break

        timestamp = int(samples[i])
        sample_data = samples[i+1]

        metric = {
            'timestamp': timestamp,
            'cpu_usage': 0,
            'cpu_idle': 0,
            'mem_available_mb': 0,
            'processes': {}
        }

        # Parse CPU line (multi-core system)
        cpu_match = re.search(r'(\d+)%cpu\s+(\d+)%user.*?(\d+)%idle', sample_data)
        if cpu_match:
            total_cpu = int(cpu_match.group(1))  # Total across all cores (e.g., 400% for 4 cores)
            cpu_idle_pct = int(cpu_match.group(3))  # Idle percentage across all cores

            # Calculate actual idle and usage percentages
            # Normalize to per-core basis if total > 100%
            if total_cpu > 100:
                num_cores = total_cpu // 100
                metric['cpu_idle'] = round(cpu_idle_pct / num_cores, 1)
                metric['cpu_usage'] = round(100 - metric['cpu_idle'], 1)
            else:
                metric['cpu_idle'] = cpu_idle_pct
                metric['cpu_usage'] = 100 - cpu_idle_pct

        # Parse memory info
        mem_match = re.search(r'MemFree:\s*(\d+)\s*kB', sample_data)
        if mem_match:
            mem_free_kb = int(mem_match.group(1))
            metric['mem_available_mb'] = round(mem_free_kb / 1024, 2)

        # Parse processes
        processes_to_track = ['com.cmcc.jarvis', 'media.swcodec', 'audioserver']

        # Find process lines
        for proc_name in processes_to_track:
            pattern = rf'(\d+)\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+([\d.]+)\s+([\d.]+).*?{re.escape(proc_name)}'
            matches = re.findall(pattern, sample_data)

            if matches:
                cpu_total = sum(float(m[1]) for m in matches)
                mem_total = sum(float(m[2]) for m in matches)

                metric['processes'][proc_name] = {
                    'cpu': round(cpu_total, 2),
                    'mem_mb': round(mem_total, 2)
                }

        metrics.append(metric)

    # Detect warnings
    for metric in metrics:
        # CPU idle < 10%
        if metric['cpu_idle'] < 10:
            warnings.append({
                'timestamp': metric['timestamp'],
                'type': 'cpu_overload',
                'severity': 'high',
                'message': f"CPU idle at {metric['cpu_idle']}% (threshold: <10%)"
            })

        # Available memory < 200MB
        if metric['mem_available_mb'] < 200:
            warnings.append({
                'timestamp': metric['timestamp'],
                'type': 'memory_low',
                'severity': 'high',
                'message': f"Available memory at {metric['mem_available_mb']}MB (threshold: <200MB)"
            })

        # media.swcodec CPU > 350%
        if 'media.swcodec' in metric['processes']:
            swcodec_cpu = metric['processes']['media.swcodec']['cpu']
            if swcodec_cpu > 350:
                warnings.append({
                    'timestamp': metric['timestamp'],
                    'type': 'swcodec_overload',
                    'severity': 'critical',
                    'message': f"media.swcodec CPU at {swcodec_cpu}% (threshold: >350%)"
                })

    return metrics, warnings


def analyze_trends(metrics):
    if not metrics:
        return "No data available for trend analysis."

    # Calculate averages
    avg_cpu_usage = sum(m['cpu_usage'] for m in metrics) / len(metrics)
    avg_cpu_idle = sum(m['cpu_idle'] for m in metrics) / len(metrics)
    avg_mem = sum(m['mem_available_mb'] for m in metrics) / len(metrics)

    trend_lines = []
    trend_lines.append(f"Monitored {len(metrics)} samples over 60 seconds (2-second intervals).")
    trend_lines.append(f"Average CPU usage: {avg_cpu_usage:.1f}% (idle: {avg_cpu_idle:.1f}%)")
    trend_lines.append(f"Average available memory: {avg_mem:.1f}MB")

    # Process-specific trends
    for proc_name in ['com.cmcc.jarvis', 'media.swcodec', 'audioserver']:
        cpu_values = [m['processes'].get(proc_name, {}).get('cpu', 0) for m in metrics]
        non_zero_cpus = [c for c in cpu_values if c > 0]

        if non_zero_cpus:
            avg_proc_cpu = sum(non_zero_cpus) / len(non_zero_cpus)
            max_proc_cpu = max(non_zero_cpus)
            trend_lines.append(f"{proc_name}: avg CPU {avg_proc_cpu:.1f}%, peak {max_proc_cpu:.1f}%")

    # CPU trend
    first_half_cpu = sum(m['cpu_idle'] for m in metrics[:len(metrics)//2]) / (len(metrics)//2)
    second_half_cpu = sum(m['cpu_idle'] for m in metrics[len(metrics)//2:]) / (len(metrics) - len(metrics)//2)

    if second_half_cpu < first_half_cpu - 5:
        trend_lines.append("CPU load is increasing over time.")
    elif second_half_cpu > first_half_cpu + 5:
        trend_lines.append("CPU load is decreasing over time.")
    else:
        trend_lines.append("CPU load remains stable.")

    # Memory trend
    first_half_mem = sum(m['mem_available_mb'] for m in metrics[:len(metrics)//2]) / (len(metrics)//2)
    second_half_mem = sum(m['mem_available_mb'] for m in metrics[len(metrics)//2:]) / (len(metrics) - len(metrics)//2)

    if second_half_mem < first_half_mem - 10:
        trend_lines.append("Available memory is decreasing over time.")
    elif second_half_mem > first_half_mem + 10:
        trend_lines.append("Available memory is increasing over time.")
    else:
        trend_lines.append("Memory usage remains stable.")

    return " ".join(trend_lines)


if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'output.txt'

    metrics, warnings = parse_performance_data(input_file)
    trend_analysis = analyze_trends(metrics)

    result = {
        'metrics': metrics,
        'warnings': warnings,
        'trend_analysis': trend_analysis
    }

    print(json.dumps(result, indent=2))

