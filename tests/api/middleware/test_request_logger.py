from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from oms_sensemaking.api.middleware.request_logger import RequestLogger

app = FastAPI()
app.add_middleware(RequestLogger)


@app.get("/test")
async def example(request: Request):
    return {"message": "hello"}


client = TestClient(app)


def test_request_logger(mocker: MockerFixture):
    mock_logger = mocker.patch("oms_sensemaking.api.middleware.request_logger.LOGGER.info")
    response = client.get("/test")

    assert response.status_code == 200
    mock_logger.assert_called_once()
