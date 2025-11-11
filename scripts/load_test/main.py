import argparse

from scripts.load_test.services.garrisons import GarrisonService
from scripts.load_test.services.noise import (
    add_noise_attributes,
    add_noise_relationships,
)
from scripts.load_test.services.observations import observe_all
from scripts.load_test.services.relationships import assign_garrisons
from scripts.load_test.services.units import UnitService
from scripts.load_test.utils import create_sourcing, create_with_progress, run_progressive_step


def main():
    parser = argparse.ArgumentParser(description="Load-test generator for OMS Sensemaking")

    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--garrisons-per-unit", type=int, default=1)
    parser.add_argument("--locations-per-garrison", type=int, default=1)
    parser.add_argument("--noise-relationships-per-unit", type=int, default=0)
    parser.add_argument("--noise-attributes-per-garrison", type=int, default=0)

    args = parser.parse_args()

    print(
        f"[Load Script] limit={args.limit}, "
        f"garrisons_per_unit={args.garrisons_per_unit}, "
        f"locations_per_garrison={args.locations_per_garrison}, "
        f"noise_relationships_per_unit={args.noise_relationships_per_unit}, "
        f"noise_attributes_per_garrison={args.noise_attributes_per_garrison}"
    )

    sourcing = create_sourcing()
    unit_service = UnitService()
    garrison_service = GarrisonService()

    # Units
    units = create_with_progress("Creating units", args.limit, lambda i: unit_service.create(f"Unit-{i}"))

    # Garrisons (+ base geo attributes)
    garrisons = create_with_progress(
        "Creating garrisons",
        args.limit,
        lambda i: garrison_service.create(f"Garrison-{i}", sourcing, args.locations_per_garrison),
    )

    # Noise Attributes for Garrisons
    if args.noise_attributes_per_garrison > 0:
        run_progressive_step(
            "Adding noise attributes",
            garrisons,
            lambda g: add_noise_attributes([g], sourcing, args.noise_attributes_per_garrison),
        )

    # Assign garrisons to units
    run_progressive_step(
        "Assigning garrisons", units, lambda u: assign_garrisons([u], garrisons, sourcing, args.garrisons_per_unit)
    )

    # Noise relationships between units + random nodes
    if args.noise_relationships_per_unit > 0:
        run_progressive_step(
            "Adding noise relationships",
            units,
            lambda u: add_noise_relationships([u], garrisons, sourcing, args.noise_relationships_per_unit),
        )

    # Observations
    run_progressive_step("Creating observations", units, lambda u: observe_all([u], sourcing))

    print("Load test complete")


if __name__ == "__main__":
    main()
