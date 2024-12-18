#!/bin/bash
set -e

docker rm -f seemantic-db
docker build . -t seemantic-db-img
