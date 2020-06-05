import abc
import configuration
import json


class RepositoryException(Exception):
    pass


class AbstractRepository(abc.ABC):

    @abc.abstractmethod
    def add(self, entity):
        raise NotImplementedError


class DBRepository(AbstractRepository):

    def __init__(self, connection_pool):
        self.connection_pool = connection_pool

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

    def _get_connection(self):
        return self.connection_pool.get_connection()

    @classmethod
    def _get_field_mappings(cls, model):
        try:
            config = configuration.configuration[model.name]
            return json.loads(config['repository_field_mappings'])
        except KeyError:
            return None

    def _get_insert_statement(self, entity):
        fields_to_insert = entity.filter_model_fields(self._get_field_mappings(entity.model))
        fields_values = list(zip(*fields_to_insert.items()))
        fields = ",".join(fields_values[0])
        placeholders = ",".join(['%s'] * len(fields_values[0]))
        values = fields_values[1]
        return f'INSERT INTO {entity.model.name} ({fields},created_on) VALUES ({placeholders},CURRENT_TIMESTAMP())', \
               values

    def add(self, entity):
        try:
            insert_stm, args = self._get_insert_statement(entity)
            connection = self._get_connection()
            cursor = connection.cursor()
            cursor.execute(insert_stm, args)
            connection.commit()
        except Exception as e:
            raise RepositoryException(f'Error when adding entity {entity.model.name}')
        finally:
            cursor.close()
            connection.close()

    def close(self):
        pass
