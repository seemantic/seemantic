#!/bin/bash
set -e

# kill front and back services
./scipts/kill_backend_services.sh

cd back
python -m main_indexer &
uvicorn main:app &
cd ..
cd webapp
npm run start &


