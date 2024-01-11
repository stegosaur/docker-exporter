#!/usr/bin/env python3
import docker,time,threading,typing,argparse,prometheus_client

parser = argparse.ArgumentParser()
parser.add_argument("--port", action="store", dest="port", type=int, default=3030)
parser.add_argument("--interval", action="store", dest="interval", type=int, default=1)
args = parser.parse_args()

client = docker.from_env()
prometheus_client.start_http_server(args.port)

docker_used_memory = prometheus_client.Gauge(f"docker_used_memory", "docker container used memory" , ['name','image'])
docker_memory_limit = prometheus_client.Gauge(f"docker_memory_limit", "docker container memory limit", ['name','image'])
docker_memory_usage_pct = prometheus_client.Gauge(f"docker_memory_usage_pct", "docker container memory usage %", ['name','image'])
docker_cpu_usage_pct = prometheus_client.Gauge(f"docker_cpu_usage_pct", "docker container cpu usage %", ['name','image'])
docker_available_cpus = prometheus_client.Gauge(f"docker_cpus_available", "docker container cpus available", ['name','image'])
docker_network_rx_bytes = prometheus_client.Gauge(f"docker_network_rx_bytes", "docker container network rx bytes", ['name','image','interface'])
docker_network_tx_bytes = prometheus_client.Gauge(f"docker_network_tx_bytes", "docker container network tx bytes", ['name','image','interface'])
docker_container_restarts = prometheus_client.Gauge(f"docker_container_restarts","information about containers restarts", labelnames=["name"])
docker_container_info = prometheus_client.Info( "docker_container", "information about containers", labelnames=["name"])

docker_restart_counts: typing.Dict[str, int] = {}
docker_container_ids: typing.Dict[str, str] = {}

print(f"docker-exporter listening on port {args.port} and polling docker every {args.interval} second(s)")

def get_stats(container): 
  results[container.id]=container.stats(stream=False)
  results[container.id]['image']=container.attrs['Config']['Image']

while 2 + 2 == 4:
  results = {}
  threads = []
  try:
    for container in client.containers.list(all=True):
      if not (name := container.attrs.get("Name", "").replace("/", "")):
        continue
        
      if not (prev_container_id := docker_container_ids.get(name, None)):
        docker_container_ids[name] = container.id
        docker_restart_counts[name] = 0
        continue

      if prev_container_id != container.id:
        docker_restart_counts[name] += 1
        docker_container_ids[name] = container.id

      container_restarts = docker_restart_counts[name]
      state = container.attrs.get("State")
      is_running = state.get("Running")
      is_restarting = state.get("Restarting")
      health = state.get("Health", {}).get("Status", "UNKNOWN")
      failing_streak = state.get("Health", {}).get("FailingStreak", 0)
      image = container.attrs.get("Image")
      created = container.attrs.get("Created")
      docker_container_info.labels(name).info(
        {
          "id": str(container.id),
          "restarts": str(container_restarts),
          "is_running": str(is_running),
          "is_restarting": str(is_restarting),
          "health": str(health),
          "failing_streak": str(failing_streak),
          "image": str(image),
          "created": str(created),
        }
      )
      docker_container_restarts.labels(name).set(container_restarts)
  except Exception as e:
    print(f"failure: {e}")

  for container in client.containers.list():
    t=threading.Thread(
        target=get_stats,
        name=container.id,
        args=[container] )
    t.start()
    threads.append(t)
  [ t.join() for t in threads ]

  for result in results.items():
    result = result[1]
    # memory stats
    used_memory = result['memory_stats']['usage'] - result['memory_stats']['stats']['cache']
    available_memory = result['memory_stats']['limit']
    memory_usage_pct = used_memory / available_memory * 100.0
    # cpu stats
    cpu_delta = result['cpu_stats']['cpu_usage']['total_usage'] - result['precpu_stats']['cpu_usage']['total_usage']
    system_cpu_delta = result['cpu_stats']['system_cpu_usage'] - result['precpu_stats']['system_cpu_usage']
    number_cpus = result['cpu_stats']['online_cpus']
    cpu_usage_pct = (cpu_delta / system_cpu_delta) * number_cpus * 100.0
    name = result['name'].replace('/','')
    current_metrics = [ (i[1]['name'].replace('/',''), i[1]['image']) for i in results.items() ]
    docker_used_memory.labels(name=name,image=result['image']).set(used_memory)
    docker_memory_limit.labels(name=name,image=result['image']).set(available_memory)
    docker_memory_usage_pct.labels(name=name,image=result['image']).set(memory_usage_pct)
    docker_cpu_usage_pct.labels(name=name,image=result['image']).set(cpu_usage_pct)
    docker_available_cpus.labels(name=name,image=result['image']).set(number_cpus)
    if result.get('networks'):
      for interface in list(result['networks'].keys()):
        docker_network_rx_bytes.labels(name=name,image=result['image'],interface=interface).set(result['networks'][interface]['rx_bytes'])
        docker_network_tx_bytes.labels(name=name,image=result['image'],interface=interface).set(result['networks'][interface]['tx_bytes'])

  for m in docker_used_memory._metrics.items():
    if m[0] not in current_metrics:
      print("change in running containers detected, repopulating metrics")
      docker_used_memory.clear()
      docker_memory_limit.clear()
      docker_memory_usage_pct.clear()
      docker_cpu_usage_pct.clear()
      docker_available_cpus.clear()
      docker_network_rx_bytes.clear()
      docker_network_tx_bytes.clear()
  time.sleep(args.interval)
