docker build --pull --rm -f "Dockerfile" -t codigorinha2024:0.0.7 "."
docker tag codigorinha2024:0.0.7 victoraf/codigorinha2024:0.0.7
docker push victoraf/codigorinha2024:0.0.7

2024/02/17 15:23:33 [error] 29#29: \*1 no live upstreams while connecting to upstream, client: 172.23.0.1, server: , request: "GET /clientes/1/extrato HTTP/1.1", upstream: "http://api/clientes/1/extrato", host: "localhost:9999"

2024/02/17 15:25:28 [alert] 29#29: 2000 worker_connections are not enough
