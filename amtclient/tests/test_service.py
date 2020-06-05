import pytest
import json
import configuration
from amtclient.service import QuoteServiceClient, get_service_client, ServiceType, ServiceClientException


@pytest.fixture()
def credentials():
    return {'userid': 'theuserid', 'appid': 'theappid'}


@pytest.fixture()
def config(monkeypatch):
    mock_config = {}
    mock_config['QUOTE'] = {}
    mock_config['QUOTE']['service_keys'] = 'key1,key2,key3'
    mock_config['QUOTE']['service_field_mappings'] = '{"1": "bid_price","2": "ask_price"}'
    monkeypatch.setattr(configuration, 'configuration', mock_config)


def test_quote_service_generates_request_message(credentials, config):
    service = QuoteServiceClient(credentials)
    request = service.get_request()
    expected_request = {
        "requests": [
            {
                "service": "QUOTE",
                "requestid": "2",
                "command": "SUBS",
                "account": "theuserid",
                "source": "theappid",
                "parameters": {
                    "keys": "key1,key2,key3",
                    "fields": "1,2"
                }
            }
        ]
    }

    assert request == json.dumps(expected_request)


def test_quote_service_handle_message_returns_empty_if_not_response_message(credentials):
    service = QuoteServiceClient(credentials)
    message = '{"notify":[{"heartbeat":"1590872458085"}]}'
    assert service.handle_message(message) == []


def test_quote_service_handle_message_translates_fields(credentials, config):
    service = QuoteServiceClient(credentials)
    message = """
       {
         "data": [
           {
             "service": "QUOTE",
             "timestamp": 1590872446764,
             "command": "SUBS",
             "content": [
               {
                 "1": 183.7,
                 "2": 184.88,
                 "3": 185.7,
                 "key": "MSFT",
                 "delayed": false,
                 "assetMainType": "EQUITY",
                 "cusip": "594918104"
               }
             ]
           }
         ]
       }
       """
    quotes = service.handle_message(message)
    assert len(quotes) == 1
    assert quotes[0]['key'] == "MSFT"
    assert quotes[0]['bid_price'] == 183.7
    assert quotes[0]['ask_price'] == 184.88
    assert quotes[0]['3'] == 185.7


def test_quote_service_handle_message_supports_multikey_message(credentials):
    service = QuoteServiceClient(credentials)
    message = """
    {
      "data": [
        {
          "service": "QUOTE",
          "timestamp": 1590872446764,
          "command": "SUBS",
          "content": [
            {
              "1": 183.7,
              "2": 183.88,
              "3": 183.7,
              "4": 8,
              "5": 1,
              "6": "P",
              "7": "P",
              "8": 42146720,
              "10": 71997,
              "11": 71985,
              "26": "D",
              "key": "MSFT",
              "delayed": false,
              "assetMainType": "EQUITY",
              "cusip": "594918104"
            },
            {
              "1": 8.3,
              "2": 8.55,
              "3": 8.35,
              "4": 3,
              "5": 6,
              "6": "Q",
              "7": "K",
              "8": 14391807,
              "9": 2,
              "10": 71299,
              "11": 71299,
              "26": "K",
              "key": "GGAL",
              "delayed": false,
              "assetMainType": "EQUITY",
              "assetSubType": "ADR",
              "cusip": "399909100"
            }
          ]
        }
      ]
    }
    """
    quotes = service.handle_message(message)
    assert len(quotes) == 2


def test_get_service_from_registry_returns_the_service_client_if_found(credentials, config):
    service = get_service_client(ServiceType.QUOTE, credentials)
    assert isinstance(service, QuoteServiceClient)


def test_get_service_from_registry_throws_error_if_service_not_found(credentials, config):
    with pytest.raises(ServiceClientException):
        get_service_client('unknown', credentials)
