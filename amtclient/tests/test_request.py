import pytest
import time
import json
from unittest.mock import Mock
from amtclient.request import Request, RequestException, TokenRetriever, TokenRetrieverException
import configuration


@pytest.fixture()
def token_srv_url():
    return 'https://api.tdameritrade.com/v1/oauth2/token'


@pytest.fixture()
def config(tmpdir, monkeypatch, token_srv_url):
    mock_config = {}
    mock_config['MT_CLIENT'] = {}
    mock_config['MT_CLIENT']['consumer_key'] = "123456"
    mock_config['MT_CLIENT']['code'] = 'secretcode'
    mock_config['MT_CLIENT']['callback_url'] = 'http://localhost/test'
    mock_config['MT_CLIENT']['token_service_url'] = token_srv_url
    mock_config['MT_CLIENT']['token_data_file'] = tmpdir + 'token.json'
    monkeypatch.setattr(configuration, 'configuration', mock_config)

@pytest.fixture()
def token_response():
    response = {
        "access_token": "token_value",
        "refresh_token": "refresh_token_value",
        "token_type": "type",
        "expires_in": 1800,
        "scope": "scope",
        "refresh_token_expires_in": 3600
    }
    return response

@pytest.fixture()
def token_request(token_srv_url, token_response, requests_mock):
    requests_mock.post(token_srv_url, json=token_response, status_code=200)


def test_request_execute_get_calls_sender():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "value"}
    mock_request = Mock()
    mock_request.get.return_value = mock_response
    request = Request()
    request.sender = mock_request
    request.execute('get', 'http://test_url', 'sql_data', 'json', requires_auth=False)
    mock_request.get.assert_called_once_with('http://test_url', data='sql_data',
                                             headers={'Content-type': 'application/json'}, params={})


def test_request_execute_post_calls_sender():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "value"}
    mock_request = Mock()
    mock_request.post.return_value = mock_response
    request = Request()
    request.sender = mock_request
    request.execute('post', 'http://test_url', 'sql_data', 'json', requires_auth=False)
    mock_request.post.assert_called_once_with('http://test_url', data='sql_data',
                                              headers={'Content-type': 'application/json'})


def test_request_execute_get_returns_sender_response(requests_mock):
    requests_mock.get('http://test_url', json={'id': 'value'})
    request = Request()
    response = request.execute('get', 'http://test_url', 'sql_data', 'json', requires_auth=False)
    assert response == {'id': 'value'}


def test_request_execute_post_returns_sender_response(requests_mock):
    requests_mock.post('http://test_url', json={'id': 'value'})
    request = Request()
    response = request.execute('post', 'http://test_url', 'sql_data', 'json', requires_auth=False)
    assert response == {'id': 'value'}


def test_request_execute_throws_exception_on_status_code_not_ok(requests_mock):
    requests_mock.post('http://test_url', status_code=400)
    request = Request()
    with pytest.raises(RequestException):
        request.execute('post', 'http://test_url', 'sql_data', 'json', requires_auth=False)


def test_request_execute_sets_auth_header_by_default():
    mock_token_retriever = Mock()
    mock_token_retriever.get_access_token.return_value = "TOKEN_VALUE"
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "value"}
    mock_request = Mock()
    mock_request.post.return_value = mock_response
    request = Request()
    request.token_retriever = mock_token_retriever
    request.sender = mock_request
    request.execute('post', 'http://test_url', 'sql_data', 'json')
    mock_request.post.assert_called_once_with('http://test_url', data='sql_data',
                                              headers={'Content-type': 'application/json',
                                                       "Authorization": "Bearer TOKEN_VALUE"})


def test_token_retriever_state_after_initialization_when_token_file_not_exists(config, token_request, requests_mock):
    token_retriever = TokenRetriever()
    assert token_retriever.get_access_token() == "token_value"
    assert token_retriever.access_token == "token_value"
    assert token_retriever.refresh_token == "refresh_token_value"
    assert token_retriever.access_token_expires_in <= time.time() + 1800
    assert token_retriever.refresh_token_expires_in <= time.time() + 3600
    assert requests_mock.call_count == 1


def test_token_retriever_state_after_initialization_when_token_file_exists(tmpdir, config, token_request,
                                                                           requests_mock):
    atime = time.time()
    file_data = {
        "access_token": "file_token_value",
        "refresh_token": "file_refresh_token_value",
        "token_type": "type",
        "expires_in": atime + 3600,
        "scope": "scope",
        "refresh_token_expires_in": atime + 3600
    }
    tmp_file = tmpdir + "/sql_data.json"
    with open(tmp_file, 'w+') as file:
        json.dump(file_data, file)

    configuration.configuration['MT_CLIENT']['token_data_file'] = tmp_file
    token_retriever = TokenRetriever()
    assert token_retriever.get_access_token() == "file_token_value"
    assert token_retriever.access_token == "file_token_value"
    assert token_retriever.refresh_token == "file_refresh_token_value"
    assert token_retriever.access_token_expires_in <= time.time() + 3600
    assert token_retriever.refresh_token_expires_in <= time.time() + 3600
    assert requests_mock.call_count == 0


def test_token_retriever_returns_current_access_token_if_not_expired(config, token_request, requests_mock):
    token_retriever = TokenRetriever()
    assert token_retriever.get_access_token() == "token_value"
    assert requests_mock.call_count == 1
    assert token_retriever.get_access_token() == "token_value"
    assert requests_mock.call_count == 1


def test_token_retriever_refreshes_token_when_access_token_is_expired(config, token_srv_url, token_response,
                                                                      requests_mock):
    exp_response = {
        "access_token": "exp_token_value",
        "refresh_token": "exp_refresh_token_value",
        "token_type": "type",
        "expires_in": -1,
        "scope": "scope",
        "refresh_token_expires_in": 3600
    }
    requests_mock.post(token_srv_url, json=exp_response, status_code=200)
    token_retriever = TokenRetriever()
    assert requests_mock.call_count == 1
    requests_mock.post(token_srv_url, json=token_response, status_code=200)
    assert token_retriever.get_access_token() == "token_value"
    assert requests_mock.call_count == 2
    assert token_retriever.get_access_token() == "token_value"
    assert requests_mock.call_count == 2


def test_token_retriever_throws_exception_when_both_tokens_are_expired(config, token_srv_url, requests_mock):
    auth_response = {
        "access_token": "token_value",
        "refresh_token": "refresh_token_value",
        "token_type": "type",
        "expires_in": -1,
        "scope": "scope",
        "refresh_token_expires_in": -1
    }
    requests_mock.post(token_srv_url, json=auth_response, status_code=200)
    token_retriever = TokenRetriever()
    with pytest.raises(TokenRetrieverException):
        token_retriever.get_access_token()


def test_token_retriever_refresh_request(config, token_srv_url, token_response, requests_mock):
    exp_response = {
        "access_token": "exp_token_value",
        "refresh_token": "refresh_token_value",
        "token_type": "type",
        "expires_in": -1,
        "scope": "scope",
        "refresh_token_expires_in": 3600
    }
    requests_mock.post(token_srv_url, json=exp_response, status_code=200)
    token_retriever = TokenRetriever()
    assert requests_mock.call_count == 1
    requests_mock.post(token_srv_url, json=token_response, status_code=200)
    assert token_retriever.get_access_token() == "token_value"
    assert requests_mock.call_count == 2
    elements = requests_mock.last_request.text.split('&')
    refresh_req_data = dict(element.split('=') for element in elements)
    assert len(refresh_req_data) == 4
    assert refresh_req_data['grant_type'] == 'refresh_token'
    assert refresh_req_data['refresh_token'] == 'refresh_token_value'
    assert refresh_req_data['access_type'] == 'offline'
    assert refresh_req_data['client_id'] == '123456'
