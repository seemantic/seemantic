#!/bin/bash
set -e

cd "$(dirname "$0")"

./rebuild_db.sh
./run_db.sh
./start_db.sh
