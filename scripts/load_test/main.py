import argparse
import time

from scripts.load_test.services.garrisons import GarrisonService
from scripts.load_test.services.observations import observe_all
from scripts.load_test.services.relationships import assign_garrisons
from scripts.load_test.services.units import UnitService
from scripts.load_test.utils import create_sourcing, create_with_progress, run_progressive_step


def main():
    parser = argparse.ArgumentParser(description="Load-test generator for OMS Sensemaking")

    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--loop", type=int, default=1)
    parser.add_argument("--loop-wait", type=int, default=0, help="Minutes to wait between each loop iteration")

    args = parser.parse_args()

    print(f"[Load Script] limit={args.limit}, loop={args.loop}, loop_wait={args.loop_wait}")

    sourcing = create_sourcing()
    unit_service = UnitService()
    garrison_service = GarrisonService()
    for n in range(args.loop):
        if args.loop > 1:
            print(f"[Load Script] Loop {n + 1}/{args.loop}")
        # Units
        units = create_with_progress("Creating units", args.limit, lambda i: unit_service.create(f"Unit-{i}"))

        # Garrisons (+ base geo attributes)
        garrisons = create_with_progress(
            "Creating garrisons",
            args.limit,
            lambda i: garrison_service.create(f"Garrison-{i}", sourcing),
        )

        # Assign garrisons to units
        run_progressive_step(
            "Assigning garrisons",
            units,
            lambda u, garrisons=garrisons, sourcing=sourcing: assign_garrisons(
                [u],
                garrisons,
                sourcing,
            ),
        )

        # Observations
        run_progressive_step(
            "Creating observations",
            units,
            lambda u, sourcing=sourcing: observe_all([u], sourcing),
        )

        # Wait before next loop (but not after the final one)
        if args.loop_wait > 0 and n < args.loop - 1:
            print(f"[Load Script] Waiting {args.loop_wait} minute(s) before next loop...")
            time.sleep(args.loop_wait * 60)

    print("Load test complete")


if __name__ == "__main__":
    main()
