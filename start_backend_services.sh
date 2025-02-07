#!/bin/bash
set -e

./back/postgres_db/start_db.sh
./back/minio/rebuild_and_run.sh

cd ./back
python -m main_indexer.py