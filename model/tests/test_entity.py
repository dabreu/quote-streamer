import pytest
import json

from model import Model, Entity, EntityException


def test_entity_is_created_without_mappings():
    fields = {"field1": "value1", "field2": 2}
    entity = Entity(Model.QUOTE, fields)
    assert entity['field1'] == "value1"
    assert entity['field2'] == 2


def test_entity_is_created_with_mappings():
    fields = {"field1": "value1", "field2": 2, "field3": "value3"}
    mappings = {"field1": "mapped_field1", "field3": "mapped_field3"}
    entity = Entity(Model.QUOTE, fields, mappings)
    assert entity['mapped_field1'] == "value1"
    assert entity['field2'] == 2
    assert entity['mapped_field3'] == "value3"
    with pytest.raises(KeyError):
        entity['field1']


def test_entity_to_json_includes_fields_and_model():
    fields = {"field1": "value1", "field2": 2}
    entity = Entity(Model.QUOTE, fields)
    json_str = entity.to_json()
    entity_from_json = json.loads(json_str)
    assert entity_from_json['field1'] == "value1"
    assert entity_from_json['field2'] == 2
    assert entity_from_json['model'] == Model.QUOTE.name


def test_entity_from_json_includes_fields_and_model():
    json_str = '{"model": "QUOTE", "field1": "value1", "field2": 2}'
    entity_from_json = Entity.from_json(json_str)
    assert entity_from_json['field1'] == "value1"
    assert entity_from_json['field2'] == 2
    assert entity_from_json['model'] == Model.QUOTE.name


def test_entity_from_json_throws_error_when_invalid_model():
    json_str = '{"model": "unknown", "field1": "value1", "field2": 2}'
    with pytest.raises(EntityException):
        Entity.from_json(json_str)


def test_entity_filter_model_fields_returns_only_fields_on_model():
    fields = {"symbol": "QQQ", "last_id": 1200, "field1": "value1", "field2": 2}
    entity = Entity(Model.QUOTE, fields)
    filtered_fields = entity.filter_model_fields()
    assert len(filtered_fields) == 2
    assert filtered_fields['symbol'] == "QQQ"
    assert filtered_fields['last_id'] == 1200


def test_entity_filter_model_fields_applies_mapping_before_filtering():
    fields = {"symbol": "QQQ", "last_id": 1200, "field1": 1234, "field2": 2}
    mappings = {"field1": "ask_id"}
    entity = Entity(Model.QUOTE, fields, mappings)
    filtered_fields = entity.filter_model_fields()
    assert len(filtered_fields) == 3
    assert filtered_fields['symbol'] == "QQQ"
    assert filtered_fields['last_id'] == 1200
    assert filtered_fields['ask_id'] == 1234
