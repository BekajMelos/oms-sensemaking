import argparse

from scripts.load_test.services.garrisons import GarrisonService
from scripts.load_test.services.observations import observe_all
from scripts.load_test.services.relationships import assign_garrisons
from scripts.load_test.services.units import UnitService
from scripts.load_test.utils import create_sourcing, create_with_progress, run_progressive_step


def main():
    parser = argparse.ArgumentParser(description="Load-test generator for OMS Sensemaking")

    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--loop", type=int, default=1)

    args = parser.parse_args()

    print(f"[Load Script] limit={args.limit}, " f"loop={args.loop}")

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

    print("Load test complete")


if __name__ == "__main__":
    main()
