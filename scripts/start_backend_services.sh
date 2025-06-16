#!/bin/bash
set -e

# kill front and back services
./scipts/kill_backend_services.sh

./back/postgres_db/start_db.sh
./back/minio/start.sh
cd back
python -m main_indexer &
uvicorn main:app &
cd ..
cd webapp
npm run start &


