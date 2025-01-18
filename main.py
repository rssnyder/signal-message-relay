from os import getenv
from websockets import connect
from asyncio import get_event_loop
from json import loads
from os import getenv
import logging

from requests import post
from tomli import load

with open("config.toml", mode="rb") as fp:
    config = load(fp)

logging.basicConfig(level=config.get("logLevel", "DEBUG").upper())


def send(api: str, number: str, recipient: str, message: str) -> str:
    # send messages

    resp = post(
        f"http://{api}/v2/send",
        json={
            "message": message,
            "number": number,
            "recipients": [recipient],
        },
    )

    if resp.status_code >= 400:
        logging.error(resp.text)
    else:
        logging.info(resp.text)


async def receive():
    # receive messages from signal via json rpc

    try:
        async with connect(
            f"ws://{config['signal']['api']}/v1/receive/{config['signal']['number']}",
            ping_interval=None,
        ) as websocket:
            async for raw_message in websocket:
                yield raw_message
    except Exception as e:
        raise e


async def wait_for_messages():
    # loop through all new messages

    logging.info("waiting for messages...")

    async for raw_message in receive():

        logging.debug("got message")

        # load in message
        try:
            message = loads(raw_message)
        except Exception as e:
            print("unable to load message: ", e)
            continue

        # only watch text messages from individual users
        if ("dataMessage" not in message["envelope"]) or (
            "groupInfo" in message["envelope"]["dataMessage"]
        ):
            logging.debug("not text/direct")
            continue

        # use a name if they have one
        if "sourceName" in message["envelope"]:
            signal_user = message["envelope"]["sourceName"]
        else:
            signal_user = message["envelope"]["source"]

        logging.debug("message from ", signal_user)

        send(
            config["signal"]["api"],
            config["signal"]["number"],
            config["signal"]["recipient"],
            signal_user + ": " + message["envelope"]["dataMessage"]["message"],
        )


if __name__ == "__main__":

    event_loop = get_event_loop()

    event_loop.run_until_complete(wait_for_messages())
