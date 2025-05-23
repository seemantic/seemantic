#!/bin/bash
set -e

# Kill front and back services
pkill -f vite || true
pkill -f uvicorn || true
# kill main_indexer.py
ps ux | grep main_indexer | grep -v grep | awk '{print $2}' | xargs -r -I{} sh -c 'echo "Killing PID {}"; kill -9 {}'
