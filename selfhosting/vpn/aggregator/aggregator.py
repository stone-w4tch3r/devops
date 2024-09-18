import json5
import logging
import os

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, HttpUrl, ValidationError, field_validator, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigModel(BaseModel):
    """
    Json example:
    {
        "sources_plain": [
            "http://source1:8000/sub",
            "http://source2:8000/sub"
        ],
        "sources_json": [
            "http://source1:8000/json",
            "http://source2:8000/json"
        ],
        "endpoint_plain": "/subs",
        "endpoint_json": "/subs-json"
    }
    """
    sources_plain: list[HttpUrl]
    sources_json: list[HttpUrl]
    endpoint_plain: str = Field(..., pattern=r"^/.*[^/]$")
    endpoint_json: str = Field(..., pattern=r"^/.*[^/]$")

    # noinspection PyNestedDecorators
    @field_validator("sources_plain", "sources_json")
    @classmethod
    def validate_no_trailing_slash(cls, urls: list[HttpUrl]) -> list[HttpUrl]:
        for url in urls:
            if str(url).endswith("/"):
                raise ValueError(f"Trailing slash not allowed in source URL: {url}")
        return urls


app = FastAPI()

config_str = os.getenv("AGGREGATOR_CONFIG_JSON")
if not config_str:
    raise Exception("AGGREGATOR_CONFIG_JSON environment variable not set")

logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG") else logging.INFO, format='%(levelname)s: %(message)s')
logger.debug("Debug mode enabled")

logger.info("Config value:")
logger.info(config_str)

try:
    config = json5.loads(config_str)
except json5.JSONDecodeError as e:
    raise Exception(f"Invalid JSON format: {e}")

try:
    config_data = ConfigModel(**config)
except ValidationError as e:
    raise Exception(f"Configuration validation error: {e}")

logger.info(f"Config loaded successfully")
logger.info(f"Endpoints: {config_data.endpoint_plain} {config_data.endpoint_json}")
logger.info(f"Sources: {" ".join([str(source) for source in [*config_data.sources_plain, *config_data.sources_json]])}")


@app.get(config_data.endpoint_plain + "/{user}")
async def get_subscriptions(user: str):
    subscriptions = []
    error_count = 0
    logger.debug(f"Fetching subscriptions for user {user}")
    for url in config_data.sources_plain:
        try:
            logger.debug(f"Fetching plain subscriptions from {url} for user {user}")
            response = requests.get(f"{url}/{user}")
            response.raise_for_status()
            logger.debug(f"Received: {response.text}")
            subscriptions.extend(response.text.splitlines())
        except Exception as err:
            error_count += 1
            logger.error(f"Failed fetching plain subscriptions from {url} for {user}: {err}")

    if error_count == len(config_data.sources_plain):
        raise HTTPException(status_code=500, detail="All sources returned an error")

    return PlainTextResponse(content=("\n".join(subscriptions)))


@app.get(config_data.endpoint_json + "/{user}")
async def get_subscriptions(user: str):
    subscriptions: list[dict] = []
    error_count = 0
    for url in config_data.sources_json:
        try:
            logger.debug(f"Fetching json subscriptions from {url} for user {user}")
            response = requests.get(f"{url}/{user}")
            response.raise_for_status()
            logger.debug(f"Received: {response.text}")
            received_json = json5.loads(response.text)
            subscriptions.extend(received_json if isinstance(received_json, list) else [received_json])
        except Exception as err:
            error_count += 1
            logger.error(f"Failed fetching json subscriptions from {url} for {user}: {err}")

    if error_count == len(config_data.sources_json):
        raise HTTPException(status_code=500, detail="All sources returned an error")

    # return formatted json
    return PlainTextResponse(content=json5.dumps(subscriptions, indent=4))
