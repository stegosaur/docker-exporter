# docker-exporter
prometheus exporter for docker container stats

usage: `python3 main.py --port <port> --interval <time>`

if running this exporter in docker, the socket needs to be mounted to the container with the following argument: `-v /var/run/docker.sock:/var/run/docker.sock`

sample output:

```
# HELP docker_used_memory docker container used memory
# TYPE docker_used_memory gauge
docker_used_memory{image="docker-exporter:latest",name="docker-exporter"} 8.0175104e+07
# HELP docker_memory_limit docker container memory limit
# TYPE docker_memory_limit gauge
docker_memory_limit{image="docker-exporter:latest",name="docker-exporter"} 6.584666112e+010
# HELP docker_memory_usage_pct docker container memory usage %
# TYPE docker_memory_usage_pct gauge
docker_memory_usage_pct{image="docker-exporter:latest",name="docker-exporter"} 0.12176031804237973
# HELP docker_cpu_usage_pct docker container cpu usage %
# TYPE docker_cpu_usage_pct gauge
docker_cpu_usage_pct{image="docker-exporter:latest",name="docker-exporter"} 0.05769388012618296
# HELP docker_cpus_available docker container cpus available
# TYPE docker_cpus_available gauge
docker_cpus_available{image="docker-exporter:latest",name="docker-exporter"} 12.0
# HELP docker_network_rx_bytes docker container network rx bytes
# TYPE docker_network_rx_bytes gauge
docker_network_rx_bytes{image="docker-exporter:latest",interface="eth0",name="docker-exporter"} 2.137213e+06
# HELP docker_network_tx_bytes docker container network tx bytes
# TYPE docker_network_tx_bytes gauge
docker_network_tx_bytes{image="docker-exporter:latest",interface="eth0",name="docker-exporter"} 9.684747e+06
```
