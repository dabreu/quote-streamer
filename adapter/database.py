import mysql.connector.pooling
from configuration import configuration as config

connection_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="trade_pool",
                                                              pool_size=5,
                                                              pool_reset_session=True,
                                                              host=config['DATABASE']['host'],
                                                              port=config['DATABASE']['port'],
                                                              database=config['DATABASE']['name'],
                                                              user=config['DATABASE']['user'],
                                                              password=config['DATABASE']['password'])
