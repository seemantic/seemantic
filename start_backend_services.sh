#!/bin/bash
set -e

./back/postgres_db/start_db.sh
./back/minio/start.sh

