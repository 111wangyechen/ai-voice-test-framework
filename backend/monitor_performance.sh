#!/bin/bash

DEVICE="10.7.187.15:5555"
DURATION=60
INTERVAL=2
ITERATIONS=$((DURATION / INTERVAL))

echo "Starting performance monitoring for $DURATION seconds..."

for i in $(seq 1 $ITERATIONS); do
    TIMESTAMP=$(date +%s)
    echo "===SAMPLE_START:$TIMESTAMP==="

    # Get CPU stats using top
    adb -s $DEVICE shell "top -n 1 -b" 2>/dev/null

    echo "===MEMINFO==="
    # Get memory info
    adb -s $DEVICE shell "cat /proc/meminfo" 2>/dev/null

    echo "===SAMPLE_END:$TIMESTAMP==="

    if [ $i -lt $ITERATIONS ]; then
        sleep $INTERVAL
    fi
done

echo "Monitoring complete."
