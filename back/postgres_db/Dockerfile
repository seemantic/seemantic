# To keep synchronized with clou sql version
FROM postgres:17.0-alpine

# password for root user 'postgres'
ENV POSTGRES_PASSWORD seematic-db-root-pwd
# container will execute scripts on docker-entrypoint-initdb.d folder by alphabetical order
# cf. https://hub.docker.com/_/postgres/, initialize a fresh instance
COPY sql_init /docker-entrypoint-initdb.d
