from fastapi.responses import PlainTextResponse
from fastapi import FastAPI, HTTPException
import requests
import os
import json
import logging
from pydantic import BaseModel, HttpUrl, ValidationError, validator, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigModel(BaseModel):
    """
    Json example:
    {"sources": ["https://source1.com", "https://source2.com"], "endpoint": "/aggregate-subscriptions"}
    """
    sources: list[HttpUrl]
    endpoint: str = Field(..., pattern=r"^/.*[^/]$")


app = FastAPI()

config_str = os.getenv("AGGREGATOR_CONFIG_JSON")
if not config_str:
    raise Exception("AGGREGATOR_CONFIG_JSON environment variable not set")

logger.info("Loaded config:")
logger.info(config_str)

try:
    config = json.loads(config_str)
except json.JSONDecodeError as e:
    raise Exception(f"Invalid JSON format: {e}")

try:
    config_data = ConfigModel(**config)
except ValidationError as e:
    raise Exception(f"Configuration validation error: {e}")

logger.info(f"Endpoint: {config_data.endpoint}")
logger.info(f"Sources: {" ".join([str(source) for source in config_data.sources])}")


@app.get(config_data.endpoint + "/{user}")
async def get_subscriptions(user: str):
    subscriptions = []
    error_count = 0
    for source_url in config_data.sources:
        try:
            response = requests.get(f"{source_url}/{user}")
            response.raise_for_status()
            subscriptions.extend(response.text.splitlines())
        except requests.RequestException as err:
            error_count += 1
            logger.error(f"Failed fetching from {source_url}: {err}")

    if error_count == len(config_data.sources):
        raise HTTPException(status_code=500, detail="All sources returned an error")

    return PlainTextResponse(content=("\n".join(subscriptions)))
