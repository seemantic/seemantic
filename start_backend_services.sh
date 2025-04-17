#!/bin/bash
set -e

# Kill front and back services
pkill -f vite || true
pkill -f uvicorn || true
# kill main_indexer.py
ps ux | grep main_indexer | grep -v grep | awk '{print $2}' | xargs -r -I{} sh -c 'echo "Killing PID {}"; kill -9 {}'

./back/postgres_db/start_db.sh
./back/minio/start.sh
cd back
python -m main_indexer &
uvicorn main:app --reload &
cd ..
cd webapp
npm run start &


