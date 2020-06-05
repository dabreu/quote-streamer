import pytest
import json
import configuration
from unittest.mock import Mock
from model import Model, Entity
from repository import DBRepository, RepositoryException


@pytest.fixture()
def quote():
    quote = Entity(Model.QUOTE, json.loads("""
    {
      "key": "MSFT",
      "delayed": false,
      "assetMainType": "EQUITY",
      "cusip": "594918104",
      "bid_price": 183.7,
      "ask_price": 183.88,
      "last_price": 183.7,
      "bid_size": 8,
      "ask_size": 1,
      "ask_id": "P",
      "bid_id": "P",
      "total_volume": 42146720,
      "trade_time": 71997,
      "quote_time": 71985,
      "last_id": "D",
      "timestamp": 1590879805110,
      "formated_timestamp": "2020-05-30 20:03:25.110000"
    }
    """))
    return quote


def test_db_repository_add_entity_calls_commit_if_no_error(quote):
    connection_pool = Mock()
    connection = Mock()
    cursor = Mock()
    connection.cursor.return_value = cursor
    connection_pool.get_connection.return_value = connection
    repository = DBRepository(connection_pool)
    repository.add(quote)
    connection.commit.assert_called_once()


def test_db_repository_add_entity_throws_exception_if_error(quote):
    connection_pool = Mock()
    connection = Mock()
    cursor = Mock()
    connection.cursor.return_value = cursor
    cursor.execute.side_effect = Exception()
    connection_pool.get_connection.return_value = connection
    repository = DBRepository(connection_pool)
    with pytest.raises(RepositoryException):
        repository.add(quote)


def test_db_repository_add_entity_inserts_only_the_fields_defined_by_model(quote, monkeypatch):
    connection_pool = Mock()
    connection = Mock()
    cursor = Mock()
    connection.cursor.return_value = cursor
    connection.commit.return_value = 0
    connection_pool.get_connection.return_value = connection

    mock_config = {}
    mock_config['DATABASE'] = {}
    monkeypatch.setattr(configuration, 'configuration', mock_config)

    repository = DBRepository(connection_pool)
    repository.add(quote)

    stm = 'INSERT INTO QUOTE (bid_price,ask_price,last_price,bid_size,ask_size,' \
          'ask_id,bid_id,total_volume,trade_time,quote_time,last_id,created_on) ' \
          'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP())'
    args = (183.7, 183.88, 183.7, 8, 1, 'P', 'P', 42146720, 71997, 71985, 'D')
    cursor.execute.assert_called_once_with(stm, args)


def test_db_repository_add_entity_supports_field_mapping(quote, monkeypatch):
    connection_pool = Mock()
    connection = Mock()
    cursor = Mock()
    connection.cursor.return_value = cursor
    connection.commit.return_value = 0
    connection_pool.get_connection.return_value = connection

    mock_config = {}
    mock_config['QUOTE'] = {}
    mock_config['QUOTE']['repository_field_mappings'] = '{"key": "symbol"}'
    monkeypatch.setattr(configuration, 'configuration', mock_config)

    repository = DBRepository(connection_pool)
    repository.add(quote)

    stm = 'INSERT INTO QUOTE (symbol,bid_price,ask_price,last_price,bid_size,ask_size,' \
          'ask_id,bid_id,total_volume,trade_time,quote_time,last_id,created_on) ' \
          'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP())'
    args = ('MSFT', 183.7, 183.88, 183.7, 8, 1, 'P', 'P', 42146720, 71997, 71985, 'D')
    cursor.execute.assert_called_once_with(stm, args)
    cursor.execute.assert_called_once_with(stm, args)
