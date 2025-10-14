# Load Test & Metrics

Load Testing is a process of seeing how well the application performs with more than just a handful of test records.  This helps us verify the queues process data at a reasonable pace and helps us identify slow parts of the system.

## Setup

Activate Python:
```shell
  source .venv/bin/activate
```
Add the `metrics` profile to `.env`:

```
COMPOSE_PROFILES=local,metrics
```

Run `make up` to ensure the Prometheus and Grafana services spin up.

## Run a load test

```shell
  make load-incursions
```

## View performance metrics

In [Grafana](http://localhost:3001/d/oms-sensemaking/oms-sensemaking-dashboard), open the dashboard to view the following:
- Request Rate
- 95th Percentile Response Time
- Queue Processing Rate
- Events Processed Rate
- Events Failed Rate