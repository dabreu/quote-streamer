import sys
from adapter.database import connection_pool
from model import Entity
from repository import DBRepository

def main():
    with DBRepository(connection_pool) as repo:
        for message in sys.stdin:
            entity = Entity.from_json(message)
            repo.add(entity)


if __name__ == "__main__":
    main()
