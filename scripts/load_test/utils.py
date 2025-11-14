import random
import uuid

from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    CreateOriginatorInput,
    CreateProviderInput,
    CreateSourceInput,
    OriginatorQuery,
    ProviderQuery,
    SourceQuery,
)
from oms_sdk.generated.generated_graphql_client.exceptions import GraphQLClientGraphQLMultiError

from scripts.load_test.atoms_client import atoms_client


def progress(label: str, i: int, total: int):
    """Single-line progress indicator."""
    print(f"{label}: {i+1}/{total}", end="\r")
    if i + 1 == total:
        print()  # newline at the end


def create_with_progress(label: str, count: int, create_fn):
    """
    Create `count` items with a create_fn(i) factory and progress logs.
    Returns a list of results.
    """
    results = []
    for i in range(count):
        results.append(create_fn(i))
        progress(label, i, count)
    return results


def run_progressive_step(label: str, iterable, fn):
    """
    Run fn(item) over an iterable with progress logs.
    """
    total = len(iterable)
    for i, item in enumerate(iterable):
        fn(item)
        progress(label, i, total)


def gen_random_location():
    return {
        "type": "Point",
        "coordinates": [
            random.randint(-170, 170),
            random.randint(-70, 70),
        ],
    }


class Sourcing:
    def __init__(self, originator, provider, source):
        self.originator = originator
        self.provider = provider
        self.source = source


def create_sourcing():
    suffix = uuid.uuid4().hex[:8]
    client = atoms_client.client

    try:
        orig = client.create_originator(
            CreateOriginatorInput(
                name=f"originator-{suffix}",
                description="descr",
                tags=[],
                acm=DEFAULT_ACM,
            )
        )
    except GraphQLClientGraphQLMultiError:
        orig = client.originators(OriginatorQuery()).data[0]

    try:
        prov = client.create_provider(
            CreateProviderInput(
                name=f"provider-{suffix}",
                description="descr",
                originatorId=orig.id,
                acm=DEFAULT_ACM,
            )
        )
    except GraphQLClientGraphQLMultiError:
        prov = client.providers(ProviderQuery()).data[0]

    try:
        src = client.create_source(
            CreateSourceInput(
                name="source",
                providerId=prov.id,
                acm=DEFAULT_ACM,
                identifier=f"https://dev.com/loadtest/{suffix}",
                dataAcm=DEFAULT_ACM,
                dateOfReport="2023-01-01T00:00:00+00:00",
                dateOfInformation="2023-01-01T00:00:00+00:00",
            )
        )
    except GraphQLClientGraphQLMultiError:
        src = client.sources(SourceQuery()).data[0]

    return Sourcing(orig, prov, src)
