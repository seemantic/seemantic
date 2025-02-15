#!/bin/bash
set -e

./back/postgres_db/rebuild_run_start_db.sh
./back/minio/rebuild_and_run.sh
