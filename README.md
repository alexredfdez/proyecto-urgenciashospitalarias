

## Para iniciar el contenedor:
`docker compose --env-file docker/.env -f docker/docker-compose.yml up -d --build`

## Ejecutar el main
`docker exec -it python python src/main.py`