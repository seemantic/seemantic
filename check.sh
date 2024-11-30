set -e

cd ./back
black .
pyright
ruff check . --fix
