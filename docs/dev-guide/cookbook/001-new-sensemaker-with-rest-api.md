# How To Add a New Sensemaker With a REST Interface

## Problem

You need to add a new Sensemaker to the ATOMS Sensemaking Service that includes a
REST Interface.


## Solution

This problem can be broken into two distinct tasks, implementing the Sensemaker
and exposing the Sensemaker's functionality through a REST interface.

In both cases, it is best to begin with a plan for what you are trying to
accomplish. For examples sake, let's create a simple *Sensemaker* that will
receive text as input and perform analysis of that text (e.g. word count). The
results of running the sensemaker should be stored in the *findings* table
in the `oms_sensemaking` database.

### Part 1: Developing the Sensemaker

#### Step 1: Planning

Following the word count analysis example, we know that we will need a new
Sensemaker that receives *text* and returns a *word count*. To implement this,
we will need to create a subclass of
`oms_sensemaking.core.sensemakers.Sensemaker` that wraps the algorithm for
calculating the word count.


#### Step 2: Create The New Sensemaker

> :material-tooltip:
> The existing sensemakers have been grouped by category in the package
> hierarchy (e.g. the geospatial sensemakers can be found in
> `oms_sensemaking/geospatial/sensemakers.py`). Following this convention, the
> new sensemaker we are creating in this example might fit in
> `oms_sensemaking/text/sensemakers.py`. You could also argue that this is an
> NLP sensemaker and the words are "tokens" `¯\_(ツ)_/¯`.

1. Create a new package for *text* processing Sensemakers

    ```sh
    mkdir -p src/oms_sensemaking/text
    echo '"""Text processing."""\n' > src/oms_sensemaking/text/__init__.py
    ```

2. Create a *WordCountSensemaker*

    Edit `sensemakers.py` and create a new class, *WordCountSensemaker*, that
    extends [oms_sensemaking.core.sensemakers.Sensemaker]:

    ```{.python title="src/oms_sensemaking/text/sensemakers.py" hl_lines="3 6 12 16" linenums="1"}
    """Text Processing sensemakers."""

    from oms_sensemaking.core.sensemakers import Sensemaker


    class WordCountSensemaker(Sensemaker):
        """Provides a sensemaker for calculating word count in a body of text."""

        def __init__(self) -> None:
            """Create a new instance of WordCountSensemaker."""
            super().__init__()
            self.version = (1, 0, 0)

        def process_data(self, text: str) -> int:
            """Calculate the word count in the given text."""
            return len(text.split())
    ```

    In this example, first note that there are *module*, *class*, and *method*
    level docstrings. In addition to informing you, or anyone else reading this
    code, what the intention of each component is, the docstrings can also be
    processed by API documentation generators as well as "smart" IDEs and LSPs
    to provide inline docs.

    Since the *WordCountSensemaker* is extending the *Sensemaker* base class, we
    need to import that class. Next the we have the implementation of the
    *WordCountSensemaker*. Subclasses of *Sensemaker* should override two
    methods: `Sensemaker#__init__()` and `Sensemaker#process_data()`.

    The `__init__()` method offers and opportunity to declard the version of the
    algorithm. This feature was introduced to allow for tracking of notable
    algorithm changes. The version follows the semantic versioning conventions.
    Overriding this method is technically optional (i.e. the default version is
    `0.0.0`), but it is recommended that you override it and set the version
    beginning at `1.0.0` as in this example.

    The `process_data()` method must be overridden and is where the algorithm
    should be implemented. This method receives data as input and returns the
    results of running the algorithm. In this example, the algorithm is a
    oneliner, but in a real world use case, this would servce as the entry point
    to a more complicated workflow.

    > ***CONTEXT***: The `process_data()` method is intended to be called from
    > `Sensemaker#execute()`, which handles running an optional `setup()` method
    > before *process_data* is run and `teardown()` after *process_data* is run.

    You can quickly verify that the sensemaker is working by opening a Python
    REPL and testing it out:

    ```{.pycon title="WordCountSensemaker"}
    >>> from oms_sensemaking.text.sensemakers import WordCountSensemaker
    >>> WordCountSensemaker().execute("Look, Ma! some text")
    4
    ```

#### Step 3. Add Unit Tests

At this point, we have a standalone Sensemaker that is ready to be integrated
into the ATOMS Sensemaking service. Before we do that, it is worth taking the time
to create some basic unit tests for the new sensemaker.

The oms_sensemaking unit tests are located in the `tests` directory. They
hierarchy in the tests directory follows the application's hierarchy. Continuing
with the example above, create a new directory for the "text" sensemaker unit
tests and add a new file for the `WordCountSensemaker` test.

```sh
mkdir -p tests/text
echo '"""Text Sensemaker tests."""\n' > tests/text/test_sensemakers.py
```

Now consider what tests can be run against the algorithm. Following the
simple algorithm in this example, it might be worth while to test the
algorithm against a few differents strings with varying word counts as well
as an empty string and a `None` value.

```{.python title="tests/text/test_sensemakers.py" hl_lines="16 23" linenums="1"}
"""WordCountSensemaker tests."""
import pytest
from oms_sensemaking.text.sensemakers import WordCountSensemaker


def test_word_count():
    data: dict[str, int] = {
        "Look, Ma! some text": 4,
        "test": 1,
        "   test   ": 1,
        "": 0
    }

    word_count: WordCountSensemaker = WordCountSensemaker()
    for text, expected_result in data.items():
        assert word_count.execute(text) == expected_result


def test_word_count_with_none_value():
    word_count: WordCountSensemaker = WordCountSensemaker()

    # this is an example of how to check to expected exceptions
    with pytest.raises(AttributeError):
        # The naive implementation of the word count algorithm above
        # does not handle None values and will raise an AttributeError
        # when the algorithm tries to call `None.split()`
        word_count.execute(None)
```

These tests can be organized in anyway that makes sense. In the example
above they are split across two separate unit tests; one that runs tests
expected to succeed (i.e. `test_word_count()`) and the other for running a
test that is expected to fail (i.e. `test_word_count_with_none_value()`).

You can run this unit test directly with: `pytest
tests/text/test_sensemakers.py` or with the rest of the application's unit
tests via `make test`


### Part 2: Creating a REST Interface to the Sensemaker

To setup a new REST interface in FastAPI, begin with planning out what
functionality you are intending on exposing through the interface and what
endpoints you will need to implement that functionality.


#### Step 1: Planning

Before you add a REST interface for a new sensemaker, it is worthwhile to come
up with a plan for what functionality you are intending on exposing through the
REST API, taking into consideration how an external component will be
interacting with the API. This includes coming up with an initial idea of what
the input, if any, to the API looks like and defining what the output will be.
You should also consider if the endpoints will be synchronous (i.e. they wait
for the sensemaker returns a value) of if they should be asynchronus (i.e. they
start a process task, but return a response to the caller immediately).

Based on the information we are working with in the word count example, the
algorithm could be exposed as a single synchronous endpoint that receives some
text and returns the results of running the algorithm on that text.

| HTTP Method | Endpoint   | Description                          |
|-------------|------------|--------------------------------------|
| `POST`      | `/analyze` | Performs analysis on a body of text. |

Since we are working in the OMS ecosystem, it is safe to assume that in addition
to a block of text, the input will also need to include an ACM and possibly
other metadata. Because of this, JSON is the preferred format for modeling the
input.

```json
{
  "acm": { ... },
  "text": "Look Ma, some text!"
}
```

In this example, the algorithm's output is a single integer. Similar to the
input, this will also need an ACM associated with it, so a reasonable output
format might be an enriched copy of the input (i.e. the calculated word count
along with the *acm* and *text* from the input.

```json
{
  "acm": { ... },
  "text": "Look Ma, some text!",
  "word_count": 4
}
```


#### Step 2: Define Input and Output Formats

The service input and outputs are defined using Pydantic schemas. These classes
provide validation and are used to generated API documentation.

Continuing with the word count example, the inbound data can be defined as a
Pydantic schema that extends the BaseModel and adds two fields for the *acm* and
*text*. The output can be defined as an extension of the input with an
additional field to hold the calculated *word count*.

```{.python title="oms_sensemaking/api/schemas/word_count.py" hl_lines="7 23" linenums="1"}
"""Schemas representing the input and output formats for the "word count" sensemaker."""
from pydantic import BaseModel, Field

from oms_sdk import DEFAULT_ACM


class WordCountRequest(BaseModel):
    """Represents a request to the "word count" sensemaker."""

    acm: dict = Field(
        ...,
        description="The ACM for the associated data.",
        examples=[DEFAULT_ACM]
    )

    text: str = Field(
        ...,
        description="The text to analyze.",
        examples=["The quick brown fox jumps over the lazy dog."]
    )


class WordCountResponse(WordCountRequest):
    """Represents a request to the "word count" sensemaker."""

    word_count: int = Field(
        ...,
        description="The calculated word count of the associated text.",
        examples=[9]
    )
```

The class level docstring as well as the field level *description* and
*examples* attributes will all be extracted and used in the generated API docs.


#### Step 3: Create a new FastAPI Router

1. Create a new router

    The API endpoints for the sensemaker should be defined in a new file in
    `oms_sensemaking/api/routers`. This new file will be responsible for
    instantiating a FastAPI router, which is then used to annotate the
    functions that define the REST API.

    > :material-tooltip:
    > Keeping the sensemaker's REST API separated in it's own file allows for
    > clean separation between the different sensemakers and other API endpoints
    > that the microservice provides.

    ```{.python title="oms_sensemaking/api/routers/text.py (iteration 1/3)"}
    """The *text* module defines the "word count" REST API."""
    from fastapi import APIRouter

    router: APIRouter = APIRouter()
    ```

2. Create the API scaffolding

    Add annotated functions for each endpoint. Based on the plan above, we will
    need just a single endpoint that receives a JSON object with an ACM and a
    block of text.

    ```{.python title="oms_sensemaking/api/routers/text.py (iteration 2/3)"}
    """The *text* module defines the "word count" REST API."""
    from fastapi import APIRouter

    from oms_sensemaking.api.schemas.text import WordCountRequest, WordCountResponse

    router: APIRouter = APIRouter()


    @router.post("/")
    def word_count(request: WordCountRequest) -> WordCountResponse:
        pass
    ```

    For now, the function definition is just a placeholder, but this is enough
    to register the router with the service and see the new API show up in the
    autogenerated documentation.

3. Register the new router

    Routers are register with the app in `oms_sensemaking/api/service.py`:

    ```{.python title="oms_sensemaking/service.py" hl_lines="7-11" linenums="1"}
    from oms_sensemaking.api.routers import about, text

    def create_app(config: Settings) -> FastAPI:
        application: FastAPI = FastAPIOffline(...)
        ...

        application.include_router(
            text.router,
            prefix="/text",
            tags=["text", "word count"]
        )

        ...
        return application
    ```


#### Step 4: Integrate The Sensemaker

Now that all of the scaffolding is in place, the sensemaker can be integrated.
In this simple example, the *business logic* of setting up and calling the
sensemaker is defined in the router, however if your use case is more involved,
you may want to move the business logic into a separate module.

> :material-tooltip: Some frameworks might call the module with the business
> logic a "controller" or "service". Both of those terms are currently in-use
> in other parts of the oms_sensemaking app.

Running the *WordCountSensemaker* is as simpled as creating an instance of it
and calling *WordCountSensemaker#execute()* with the inbound text.

```{.python title="oms_sensemaking/api/routers/text.py (iteration 3/3)"}
    """The *text* module defines the "word count" REST API."""
    from fastapi import APIRouter

    from oms_sensemaking.api.schemas.text import WordCountRequest, WordCountResponse
    from oms_sensemaking.text.sensemakers import WordCountSensemaker

    router: APIRouter = APIRouter()


    @router.post("/")
    def word_count(request: WordCountRequest) -> WordCountResponse:
        word_count: int = WordCountSensemaker().execute(request.text)

        return WordCountResponse(
            **request.model_dump(),
            word_count=word_count
        )

```

#### Step 5: Add Unit Tests

FastAPI provides a test client for unit testing API endpoints. There is a
fixture in `tests/api/routers/conftest.py` that yields test client configured
with the oms_sensemaking app. This can be used to inject a client into unit
tests simply by defining a parameter with the name `client`.

> :material-tooltip: The FastAPI test client extends httpx (see the [Testing]
> section of the FastAPI docs).

To write tests for you API:

1. Come up with a plan for what you can/should test

    Following the word count sensemaker example, testing with a few different
    text inputs including an empty string and a null value would be worthwhile.

    > :material-tooltip: For brevity, tests related to the presense or
    > correctness of the *acm* field will be omitted, but those would also be
    > reasonable in a real world use case.

2. Create a new file in *tests/api/routers* for you unit tests

   ```sh
   echo '"""Tests for the "word count" router."""\n' \
        > tests/api/routers/test_text.py
   ```

3. Add two tests, similar to the sensemaker unit test above

    ```{.python title="tests/api/routers/test_text.py" hl_lines="9 18-24 25 28-29" linenums="1"}
    """Tests for the "text" router."""
    from fastapi.testclient import TestClient
    from httpx import Response

    from oms_sdk import DEFAULT_ACM
    from oms_sensemaking.api.schemas.text import WordCountRequest, WordCountResponse


    def test_word_count(client: TestClient):
        data: dict[str, int] = {
            "Look, Ma! some text": 4,
            "test": 1,
            "   test   ": 1,
            "": 0
        }

        for text, expected_result in data.items():
            response: Response = client.post(
                "/text",
                json=WordCountRequest(
                    acm=DEFAULT_ACM,
                    text=text
                ).model_dump()
            )
            assert response.status_code == 200

            wc_resp: WordCountResponse = WordCountResponse(**response.json())
            assert wc_resp.acm == DEFAULT_ACM
            assert wc_resp.word_count == expected_result


    def test_word_count_with_none_value(client: TestClient):
        response: Response = client.post(
            "/text",
            json=dict(  # using a dict here to avoid early validation with the WordCountRequest schema
                acm=DEFAULT_ACM,
                text=None
            )
        )

        assert resposne.status_code == 422  # validation error
    ```

In this example, the test client is inject into both unit tests, since they both
declare a input parameter named "client". on lines 18-24 an HTTP post request is
being made to the "word count" API inside a loop. Each iteration of the loop
checks that the services returned a successful status code (line 25) before
going on to validate that the response contains the expected results (lines 25
and 26).

[Testing]: https://fastapi.tiangolo.com/tutorial/testing/


## Resources

- <https://fastapi.tiangolo.com/tutorial/bigger-applications/>
- <https://fastapi.tiangolo.com/tutorial/testing/>
