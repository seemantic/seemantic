# install bacend
cd ./back
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r ./requirements.txt

cd ..

# install frontend
cd ./webapp
npm install
