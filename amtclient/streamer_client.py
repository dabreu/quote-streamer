import websockets
import urllib.parse
import json
from .request import UserPrincipalsRetriever
from .service import get_service_client


class StreamerClient:

    def __init__(self, service_type):
        self.user_principals_retriever = UserPrincipalsRetriever()
        self.service_type = service_type

    def _get_streamer_url(self):
        return "wss://" + self.user_principals_retriever.get_streamer_socket_url() + "/ws"

    def _get_credentials(self):
        return self.user_principals_retriever.get_credentials()

    def _get_login_request(self):
        credentials = self._get_credentials()
        request = {
            "requests": [
                {
                    "service": "ADMIN",
                    "command": "LOGIN",
                    "requestid": 0,
                    "account": credentials['userid'],
                    "source": credentials['appid'],
                    "parameters": {
                        "credential": urllib.parse.urlencode(credentials),
                        "token": credentials['token'],
                        "version": "1.0"
                    }
                }
            ]
        }
        return json.dumps(request)

    @classmethod
    async def _login(cls, websocket):
        login_request = cls._get_login_request()
        await websocket.send(login_request)
        await websocket.recv()

    @classmethod
    async def _execute(cls, websocket, service_client):
        request = service_client.get_request()
        await websocket.send(request)
        async for message in websocket:
            service_client.handle_message(message)

    async def execute(self):
        uri = self._get_streamer_url()
        async with websockets.client.connect(uri) as websocket:
            await self._login(websocket)
            service_client = get_service_client(self.service_type, self._get_credentials())
            await self._execute(websocket, service_client)
