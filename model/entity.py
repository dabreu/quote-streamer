import json
from enum import Enum


class Model(Enum):
    QUOTE = "QUOTE"


models = {
    Model.QUOTE: {
        "fields": ['symbol', 'quote_timestamp', 'bid_price', 'ask_price', 'last_price', 'bid_size', 'ask_size',
                   'ask_id', 'bid_id', 'total_volume', 'last_size', 'trade_time', 'quote_time', 'last_id', 'nav']
    }
}


class EntityException(Exception):
    pass


class Entity:
    MODEL_FIELD = 'model'

    def __init__(self, model, fields_values, field_mappings=None):
        self.model = model
        self.fields_values = self._from_mappings(fields_values, field_mappings)

    @classmethod
    def _from_mappings(cls, fields_values, field_mappings):
        fields = {cls._from_mapping(field, field_mappings): value for field, value in fields_values.items()}
        return fields

    @classmethod
    def _from_mapping(cls, field, field_mappings):
        if field_mappings is None: return field
        return field_mappings[field] if field in field_mappings else field

    def _model_fields(self):
        return models[self.model]['fields']

    def filter_model_fields(self, field_mappings=None):
        model_fields = {}
        for field, value in self.fields_values.items():
            field = self._from_mapping(field, field_mappings)
            if field in self._model_fields():
                model_fields[field] = value
        return model_fields

    def to_json(self):
        fields = dict(item for item in self.fields_values.items())
        fields[self.MODEL_FIELD] = self.model.name
        return json.dumps(fields)

    @classmethod
    def from_json(cls, message):
        try:
            fields = json.loads(message)
            model = Model[fields[cls.MODEL_FIELD]]
            return Entity(model, fields)
        except KeyError:
            raise EntityException(
                f'Invalid json message to build the entity. The "{cls.MODEL_FIELD}" field must included and with a '
                'valid type')

    def __getitem__(self, field):
        return self.fields_values[field]
