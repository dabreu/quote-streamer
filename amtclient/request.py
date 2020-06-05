import requests
import time
import datetime
import json
import configuration


class RequestException(Exception):
    pass


class Request:

    def __init__(self, token_retriever=None, sender=None):
        self.token_retriever = token_retriever
        self.sender = requests if sender is None else sender

    def execute(self, method, url, data, content_type, params={}, requires_auth=True):
        headers = self._headers(content_type, requires_auth)

        if method == 'post':
            response = self.sender.post(url, data=data, headers=headers)
        elif method == 'get':
            response = self.sender.get(url, data=data, headers=headers, params=params)

        if response.status_code != requests.codes.ok:
            raise RequestException(
                f'Error executing request={url}, status_code={response.status_code}, '
                'error: {response.content}')

        return response.json()

    def _headers(self, content_type, requires_auth):
        headers = {}

        if content_type == 'form':
            content_type = 'application/x-www-form-urlencoded'
        else:
            content_type = 'application/json'

        headers['Content-type'] = content_type

        if requires_auth and self.token_retriever:
            token = self.token_retriever.get_access_token()
            headers['Authorization'] = f'Bearer {token}'

        return headers


class TokenRetrieverException(Exception):
    pass


class TokenRetriever:

    def __init__(self):
        cfg = configuration.configuration
        self.client_id = cfg['MT_CLIENT']['consumer_key']
        self.redirect_uri = cfg['MT_CLIENT']['callback_url']
        self.code = cfg['MT_CLIENT']['code']
        self.token_service_url = cfg['MT_CLIENT']['token_service_url']
        self.token_data_file = cfg['MT_CLIENT']['token_data_file']
        self._load_access_token()

    def _load_access_token(self):
        data = self._get_access_token_from_file()
        if data is None:
            data = self._get_access_token_from_provider()
        self._set_state(data)

    def _get_access_token_from_file(self):
        try:
            with open(self.token_data_file) as token_file:
                return json.load(token_file)
        except FileNotFoundError:
            return None

    def _get_access_token_from_provider(self, refresh=False):
        data = self._request_access_token(refresh)
        data['expires_in'] = time.time() + data['expires_in']
        data['refresh_token_expires_in'] = time.time() + data['refresh_token_expires_in']
        with open(self.token_data_file, 'w+') as token_file:
            json.dump(data, token_file)
        return data

    def _set_state(self, data):
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']
        self.access_token_expires_in = data['expires_in']
        self.refresh_token_expires_in = data['refresh_token_expires_in']

    def _request_access_token(self, refresh):
        grant_type = 'authorization_code' if not refresh else 'refresh_token'
        refresh_token = None if not refresh else self.refresh_token
        code = self.code if not refresh else None
        redirect_uri = self.redirect_uri if not refresh else None
        data = {
            'grant_type': grant_type,
            'refresh_token': refresh_token,
            'access_type': 'offline',
            'client_id': self.client_id,
            'code': code,
            'redirect_uri': redirect_uri
        }
        request = Request()
        return request.execute("post", self.token_service_url, data, 'form', requires_auth=False)

    def _refresh_data(self):
        data = self._get_access_token_from_provider(refresh=True)
        self._set_state(data)

    def _is_auth_token_expired(self):
        return self.access_token_expires_in < time.time()

    def _is_refresh_token_expired(self):
        return self.refresh_token_expires_in < time.time()

    def get_access_token(self):
        if not self._is_auth_token_expired():
            return self.access_token

        if not self._is_refresh_token_expired():
            self._refresh_data()
            return self.access_token

        raise TokenRetrieverException("Cannot retrieve token, re-login required")


class UserPrincipalsRetriever:
    def __init__(self):
        cfg = configuration.configuration
        self.user_principals_service_url = cfg['MT_CLIENT']['user_principals_service_url']
        self.token_retriever = TokenRetriever()
        self.data = self._get_data()

    def _get_data(self):
        request = Request(self.token_retriever)
        return request.execute("get", self.user_principals_service_url, data={},
                               content_type='json',
                               params={"fields": "streamerSubscriptionKeys,streamerConnectionInfo"})

    def get_credentials(self):
        data = self.data
        token_timestamp = data['streamerInfo']['tokenTimestamp']
        token_timestamp = datetime.datetime.strptime(token_timestamp, "%Y-%m-%dT%H:%M:%S%z")
        token_timestamp_ms = int(token_timestamp.timestamp()) * 1000
        credentials = {
            'userid': data['accounts'][0]['accountId'],
            'token': data['streamerInfo']['token'],
            'company': data['accounts'][0]['company'],
            'segment': data['accounts'][0]['segment'],
            'cddomain': data['accounts'][0]['accountCdDomainId'],
            'usergroup': data['streamerInfo']['userGroup'],
            'accesslevel': data['streamerInfo']['accessLevel'],
            'authorized': 'Y',
            'timestamp': token_timestamp_ms,
            'appid': data['streamerInfo']['appId'],
            'acl': data['streamerInfo']['acl'],
        }
        return credentials

    def get_streamer_socket_url(self):
        return self.data['streamerInfo']['streamerSocketUrl']
