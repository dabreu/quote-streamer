CREATE DATABASE trade;

DROP USER tradeuser@localhost;
FLUSH PRIVILEGES;

CREATE USER tradeuser@localhost IDENTIFIED BY 'tradeuser.1';

GRANT ALL ON trade.* to 'tradeuser'@'localhost';

USE trade;

CREATE TABLE quote (
	created_on TIMESTAMP,
	quote_timestamp TIMESTAMP,
	symbol VARCHAR(20),
	bid_price FLOAT,
	ask_price FLOAT,
	last_price FLOAT,
	bid_size FLOAT,
	ask_size FLOAT,
	ask_id CHAR(10),
	bid_id CHAR(10),
	total_volume BIGINT,
	last_size FLOAT,
	trade_time INT,
	quote_time INT,
	last_id CHAR(10),
	nav FLOAT
);
