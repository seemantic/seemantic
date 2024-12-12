docker stop seemantic-minio
docker rm seemantic-minio

docker run -d -p 9000:9000 -p 9001:9001 --name seemantic-minio \
  -e "MINIO_ROOT_USER=dev_minio_root_user" \
  -e "MINIO_ROOT_PASSWORD=dev_minio_root_password" \
  quay.io/minio/minio server /data \
  --console-address ":9001"
