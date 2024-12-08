port=7997
model1=jinaai/jina-embeddings-v3/onnx
#model1=michaelfeil/bge-small-en-v1.5
volume=$PWD/data
DO_NOT_TRACK=1

docker run -it \
-v $volume:/app/.cache \
-p $port:$port \
--name infinity-container \
michaelf34/infinity:latest \
v2 \
--engine optimum \
--model-id $model1 \
#--engine torch \
--port $port


docker logs infinity-container

