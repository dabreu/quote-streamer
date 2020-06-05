import json
import abc
from datetime import datetime
from enum import Enum
import configuration
from model import Model, Entity


class ServiceType(Enum):
    QUOTE = "QUOTE"


class ServiceCommand(Enum):
    SUBS = "SUBS"


service_client_registry = {}


class ServiceClientException(Exception):
    pass


def register_client(service_client):
    service_client_registry[service_client.type()] = service_client
    return service_client


def get_service_client(service_type, credentials):
    try:
        service = service_client_registry[service_type]
        return service(credentials)
    except KeyError:
        raise ServiceClientException(f'Service type {service_type} not supported')


class ServiceClient(abc.ABC):

    def __init__(self, credentials):
        self.credentials = credentials

    def get_request(self):
        request = {
            "requests": [
                {
                    "service": self.request_service(),
                    "requestid": "2",
                    "command": self.request_command(),
                    "account": self.credentials['userid'],
                    "source": self.credentials['appid'],
                    "parameters": self.request_parameters()
                }
            ]
        }
        return json.dumps(request)

    @staticmethod
    @abc.abstractmethod
    def type():
        raise NotImplementedError

    @abc.abstractmethod
    def request_service(self):
        raise NotImplementedError

    @abc.abstractmethod
    def request_command(self):
        raise NotImplementedError

    @abc.abstractmethod
    def request_parameters(self):
        raise NotImplementedError

    def handle_message(self, message):
        result = json.loads(f"{message}")
        entities = []
        if 'data' in result:
            data = result['data']
            timestamp = data[0]['timestamp']
            content = data[0]['content']
            entities = [self._to_entity(element, timestamp) for element in content]
            for entity in entities:
                self._handle_entity(entity)
        return entities

    def _to_entity(self, element, timestamp):
        element['timestamp'] = timestamp
        element['formated_timestamp'] = str(datetime.fromtimestamp(float(timestamp / 1000)))
        return self._create_entity(element)

    @abc.abstractmethod
    def _create_entity(self, element):
        raise NotImplementedError

    @abc.abstractmethod
    def _handle_entity(self, entity):
        raise NotImplementedError


@register_client
class QuoteServiceClient(ServiceClient):

    def __init__(self, credentials):
        super().__init__(credentials)
        config = configuration.configuration[Model.QUOTE.name]
        self.keys = config['service_keys']
        self.mappings = json.loads(config['service_field_mappings'])

    @staticmethod
    def type():
        return ServiceType.QUOTE

    def request_service(self):
        return self.type().value

    def request_command(self):
        return ServiceCommand.SUBS.value

    def request_parameters(self):
        return {
            "keys": self.keys,
            "fields": ",".join(self.mappings)
        }

    def _create_entity(self, element):
        return Entity(Model.QUOTE, element, self.mappings)

    def _handle_entity(self, entity):
        print(entity.to_json(), flush=True)
