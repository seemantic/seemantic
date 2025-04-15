#!/bin/bash
set -e

./back/postgres_db/start_db.sh
./back/minio/start.sh
cd back
python -m main_indexer &
uvicorn main:app --reload &
cd ..
cd webapp
npm run start &


