from fastapi import FastAPI, HTTPException
import requests
import os

app = FastAPI()

# Extracting parameters from environment variables
HOST1 = "3x-ui-host"
PORT1 = 2096
PATH1 = os.getenv("PATH_XPANEL_SUB")
METHOD1 = "http"

HOST2 = os.getenv("HOST2")
PORT2 = os.getenv("PORT2")
PATH2 = os.getenv("PATH2")
METHOD2 = os.getenv("METHOD2")

if not HOST1 or not PORT1 or not PATH1 or not METHOD1 or not HOST2 or not PORT2 or not PATH2 or not METHOD2:
    raise Exception("Environment variables not set")
if METHOD1 not in ["http", "https"] or METHOD2 not in ["http", "https"]:
    raise Exception("Invalid method")

if isinstance(PORT2, str):
    try:
        PORT2 = int(PORT2)
    except ValueError:
        raise Exception("PORT2 is not a valid integer")
if not isinstance(PORT1, int) or not isinstance(PORT2, int) or PORT1 < 1 or PORT2 < 1 or PORT1 > 65535 or PORT2 > 65535:
    raise Exception("Invalid port")


@app.get(f"/{PATH1}/{{user}}")
async def get_subscriptions(user: str):
    try:
        # First request to HOST1
        response1 = requests.get(f"{METHOD1}://{HOST1}:{PORT1}/{PATH1}/{user}")
        response1.raise_for_status()
        subscriptions1 = response1.text.splitlines()

        # Second request to HOST2
        response2 = requests.get(f"{METHOD2}://{HOST2}:{PORT2}/{PATH2}/{user}")
        response2.raise_for_status()
        subscriptions2 = response2.text.splitlines()

        # Combine both responses as plaintext, separated by newline
        combined_subscriptions = "\n".join(subscriptions1 + subscriptions2)
        return combined_subscriptions

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
