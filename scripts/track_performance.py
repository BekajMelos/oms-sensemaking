#!/usr/bin/env python3

import json
import subprocess
import time
from datetime import UTC, datetime
from typing import Dict

import requests

RABBITMQ_API = "http://localhost:15672/api/queues"
RABBITMQ_AUTH = ("oms-bridge", "BugsBunny24")
PROMETHEUS_URL = "http://localhost:9090/api/v1/query"
CONTAINER_NAME = "atoms-sensemaking"
QUEUE_NAMES = [
    "mil-symbol-trigger",
    "geo-sensemaker-trigger",
    "infer-sensemaker-trigger",
    "object-standards-trigger",
    "resolution-trigger",
]
POLL_INTERVAL_SECONDS = 2
OUTPUT_FILE = "track-performance.json"


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "unknown"


def get_queue_depths() -> Dict[str, int]:
    """Fetch queue sizes from RabbitMQ."""
    resp = requests.get(RABBITMQ_API, auth=RABBITMQ_AUTH)
    resp.raise_for_status()

    queues = resp.json()

    result = {}
    for q in queues:
        name = q["name"]
        if name in QUEUE_NAMES:
            result[name] = q["messages"]

    return result


def get_prometheus_counters() -> Dict[str, float]:
    """Fetch prometheus counters."""
    query = "events_processed_total"

    resp = requests.get(PROMETHEUS_URL, params={"query": query})
    resp.raise_for_status()

    data = resp.json()["data"]["result"]

    result: Dict[str, float] = {}

    for item in data:
        queue = item["metric"].get("queue_name")
        if not queue:
            continue

        value = float(item["value"][1])

        # Aggregate just in case multiple series exist
        result[queue] = result.get(queue, 0.0) + value

    return result


def is_container_running(container_name: str) -> bool:
    output = subprocess.check_output(["docker", "inspect", container_name])
    data = json.loads(output)
    return data[0]["State"]["Running"]


def ensure_container_stopped(container_name: str):
    if is_container_running(container_name):
        print(
            "\nThe atoms-sensemaking service is running.\n"
            "Please pause the service, load the queues by ingesting data, and run the script again.\n"
        )
        exit(1)


def get_container_name() -> str:
    """
    Find the container that contains the CONTAINER_NAME value.
    Assumes exactly one match.
    """
    result = subprocess.check_output(["docker", "ps", "-a", "--format", "{{.Names}}"]).decode().splitlines()

    matches = [name for name in result if CONTAINER_NAME in name]

    if not matches:
        raise RuntimeError(f"No container found containing '{CONTAINER_NAME}'")

    return matches[0]


def start_container():
    container_name = get_container_name()
    ensure_container_stopped(container_name)
    print(f"Starting container: {container_name}")
    subprocess.run(["docker", "start", container_name], check=True, capture_output=True, text=True)


def all_queues_empty(depths: Dict[str, int]) -> bool:
    return all(v == 0 for v in depths.values())


def capture_start_state():
    print("Capturing start state")

    state = {
        "timestamp": datetime.now(UTC).isoformat(),
        "commit": get_git_commit(),
        "queue_depths": get_queue_depths(),
        "counters": get_prometheus_counters(),
        "start_time": time.time(),
    }

    print("Queue lengths:")
    for queue, depth in state["queue_depths"].items():
        print(f"  {queue:<30} {depth}")

    return state


def wait_for_completion(start_time: float):
    print("Processing queues")

    queue_completion_times = {}
    seen_non_zero = {q: False for q in QUEUE_NAMES}

    while True:
        now = time.time()
        depths = get_queue_depths()

        for queue, depth in depths.items():
            # Track if we've seen work in this queue
            if depth > 0:
                seen_non_zero[queue] = True

            # Record first time queue reaches 0 AFTER having work
            if depth == 0 and seen_non_zero[queue] and queue not in queue_completion_times:
                queue_completion_times[queue] = now
                print(f"✅ Queue completed: {queue}")

        if all_queues_empty(depths):
            print("All queues empty")
            return queue_completion_times

        time.sleep(POLL_INTERVAL_SECONDS)


def capture_end_state():
    print("Capturing end state")

    state = {
        "queue_depths": get_queue_depths(),
        "counters": get_prometheus_counters(),
        "end_time": time.time(),
    }

    return state


def compute_metrics(start, end, queue_completion_times):
    print("Computing metrics")

    duration = end["end_time"] - start["start_time"]

    results = {
        "timestamp": start["timestamp"],
        "commit": start["commit"],
        "duration_seconds": round(duration, 2),
        "queues": {},
    }

    for queue in QUEUE_NAMES:
        initial = start["queue_depths"].get(queue, 0)

        start_count = start["counters"].get(queue, 0)
        end_count = end["counters"].get(queue, 0)

        processed = max(0, end_count - start_count)

        completion_time = queue_completion_times.get(queue)
        completion_duration = round(completion_time - start["start_time"], 2) if completion_time else None

        # Calculate average throughput for each queue
        throughput = processed / completion_duration if completion_duration and completion_duration > 0 else 0

        results["queues"][queue] = {
            "queue_length": initial,
            "processed": int(processed),
            "average_throughput_events_per_second": round(throughput, 2),
            "completion_seconds": completion_duration,
        }

    return results


def write_results(results):
    import os

    os.makedirs("track_performance", exist_ok=True)

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(results)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def main():
    start = capture_start_state()
    start_container()
    queue_completion_times = wait_for_completion(start["start_time"])
    end = capture_end_state()
    results = compute_metrics(start, end, queue_completion_times)
    write_results(results)

    print(f"Results written to '{OUTPUT_FILE}'")


if __name__ == "__main__":
    main()
