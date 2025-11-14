# Load Test & Metrics

Load testing helps evaluate how **ATOMS Sensemaking** performs under large-scale data ingestion.
The script generates high-volume batches of:

- Units
- Garrisons (including geo attributes)
- Relationships (Unit -> Garrison)
- Observations

Each batch is pushed through the ATOMS API pipeline and events will await processing in their respective Sensemaking
queue (see: RabbitMQ).

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

Run the load test with default parameters (`limit=100`, `loop=1`):

```
make load-out-of-garrison
```

### Large-scale example

To load 50,000 garrisons in five iterations of 10,000:

```
make load-out-of-garrison limit=10000 loop=5
```

## Monitor the system

### RabbitMQ

Open the [RabbitMQ queue dashboard](http://localhost:15672/#/queues) to watch events accumulate and drain.

This is a good place to observe:

- Incoming event spikes
- Queue buildup
- Active consumer throughput and health

### Grafana

Open the [Sensemaking dashboard in Grafana](http://localhost:3001/d/oms-sensemaking/oms-sensemaking-dashboard) to view graphical panels of throughput and identify any failed events.

Suggested panels to monitor:

- Queue Processing Rate
- Events Processed Rate
- Events Failed Rate

### Practical tips

- For a smoother ramp-up, use multiple loops (e.g., `limit=2500`,`loop=4`) instead of a single iteration (`limit=10000`).
- For stress testing consumer behavior, run the load-test script with the `sensemaking` service temporarily stopped,
  then start the service after the load completes. This forces RabbitMQ to accumulate events and helps simulate a backlog
  scenario.
