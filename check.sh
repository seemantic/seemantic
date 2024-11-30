set -e

cd ./back
echo "run black..." 
black .
echo "run pyright..."
pyright
echo "run ruff..."
ruff check . --fix
