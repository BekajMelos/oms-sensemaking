# Load Test & Metrics

Load testing helps evaluate how **ATOMS Sensemaking** performs under large-scale data ingestion.
The script generates high-volume batches of:

- Units
- Garrisons (including geo attributes)
- Relationships (Unit -> Garrison)
- Observations

Each batch flows through the ATOMS API pipeline and its associated events queue inside RabbitMQ, where the Sensemaking 
consumers pick them up for processing. 

## Setup

Activate the Python environment:

```
source .venv/bin/activate
```

Enable the metrics profile in `.env`:

```
COMPOSE_PROFILES=local,metrics
```

Start the stack with metrics services:

```
make up
```

## Run a load test

### Default

Run the load test with default parameters (`limit=100`, `loop=1`, `loop_wait=0`):

```
make load-out-of-garrison
```

### Large-scale example

To load 50,000 garrisons in five iterations of 10,000:

```
make load-out-of-garrison limit=10000 loop=5
```

### Sustained load pattern example

To keep steady ingestion pressure over time:

```
make load-out-of-garrison limit=2500 loop=20 loop_wait=3
```

This creates 20 batches of 2,500 with a 3-minute pause between each batch. 

## Monitor the system

### Grafana

Open the [Sensemaking dashboard in Grafana](http://localhost:3001/d/oms-sensemaking/oms-sensemaking-dashboard) to view graphical panels of throughput and identify any failed events.

Suggested panels to monitor:

- Events Processed (per second)
- Queue Length (Ready messages)
- Queue Processing Latency (95th percentile)
- Event Failures (per second)

### RabbitMQ

Open the [RabbitMQ queue dashboard](http://localhost:15672/#/queues) to watch events accumulate and drain.

This is a good place to observe:

- Incoming event spikes
- Queue buildup
- Active consumer throughput and health

### Practical tips

- For a quicker ramp-up, use multiple loops (e.g., `limit=2500`,`loop=4`) instead of a single iteration (`limit=10000`).
- For a sustained long-running load test, combine multiple loops with `loop_wait`  (e.g., `limit=2500`,`loop=20`, `loop_wait=3`). 
- For stress testing consumer behavior, run the load-test script with the `sensemaking` service temporarily stopped,
  then start the service after the load completes. This forces RabbitMQ to accumulate events and helps simulate a backlog
  scenario.
