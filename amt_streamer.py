import asyncio
import logging
from websockets.exceptions import ConnectionClosedError

from amtclient import StreamerClient, ServiceType


async def main():
    while True:
        try:
            logging.debug("Connecting to streamer service")
            service = StreamerClient(ServiceType.QUOTE)
            await service.execute()
        except ConnectionClosedError:
            logging.warning("Connection closed error, reconnecting...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())
