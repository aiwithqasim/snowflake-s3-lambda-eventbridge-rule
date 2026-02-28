------------------------------------------- DB/SCHEMA -------------------------------------------------------

CREATE DATABASE IF NOT EXISTS CURRENCY_DB;
DROP SCHEMA CURRENCY_DB.CURRENCY_SCHEMA;
CREATE SCHEMA IF NOT EXISTS CURRENCY_DB.CURRENCY;

------------------------------------------- DDLS ------------------------------------------------------------

CREATE OR REPLACE TABLE CURRENCY.EXCHANGE_RATES_RAW (
    id STRING DEFAULT UUID_STRING(),
    load_timestamp TIMESTAMP_NTZ,
    response_raw VARIANT
);

CREATE OR REPLACE TABLE CURRENCY.EXCHANGE_RATES_STG (
    timestamp_utc TIMESTAMP_NTZ,         -- UTC timestamp of the exchange rate
    base_currency VARCHAR(10),           -- Base currency (e.g., USD)
    target_currency VARCHAR(10),         -- Target currency (e.g., EUR, BTC)
    exchange_rate FLOAT                  -- Exchange rate value
);

CREATE OR REPLACE TABLE CURRENCY.EXCHANGE_RATES (
    timestamp_utc TIMESTAMP_NTZ,
    base_currency VARCHAR(10),
    target_currency VARCHAR(10),
    exchange_rate FLOAT
);

------------------------------------------- MAIN Procedure --------------------------------------------------
CALL CURRENCY.SP_EXCHANGE_RATE_LOADING();

CREATE OR REPLACE PROCEDURE CURRENCY_DB.CURRENCY.SP_EXCHANGE_RATE_LOADING( p_json_data STRING, p_datetime TIMESTAMP_NTZ)
RETURNS NUMBER(8, 0)
LANGUAGE SQL
AS
$$ 
BEGIN
-- ------------------------------------------------------------------------
-- -- Truncating Raw Table
-- ------------------------------------------------------------------------
TRUNCATE TABLE CURRENCY.EXCHANGE_RATES_RAW;

------------------------------------------------------------------------
-- Inserting received JSON and timestamp into RAW table
------------------------------------------------------------------------
INSERT INTO CURRENCY.EXCHANGE_RATES_RAW (load_timestamp,RESPONSE_RAW)
SELECT :p_datetime,PARSE_JSON(:p_json_data);

------------------------------------------------------------------------
-- Truncating Stage Table
------------------------------------------------------------------------
TRUNCATE TABLE CURRENCY.EXCHANGE_RATES_STG;

------------------------------------------------------------------------
-- Insert into STG table from RAW based on matching DATE (UTC)
------------------------------------------------------------------------
INSERT INTO CURRENCY.EXCHANGE_RATES_STG (
    TIMESTAMP_UTC, BASE_CURRENCY, TARGET_CURRENCY, EXCHANGE_RATE
)
SELECT
    TO_TIMESTAMP_NTZ(r.RESPONSE_RAW:timestamp::NUMBER) AS TIMESTAMP_UTC,
    r.RESPONSE_RAW:base::STRING AS BASE_CURRENCY,
    f.key::STRING AS TARGET_CURRENCY,
    f.value::FLOAT AS EXCHANGE_RATE
FROM CURRENCY.EXCHANGE_RATES_RAW r,
     LATERAL FLATTEN(input => r.RESPONSE_RAW:rates) f
WHERE TO_TIMESTAMP_NTZ(r.RESPONSE_RAW:timestamp::NUMBER) = :p_datetime;

-------------------------------------------------------------------------
-- Dumping data from stage to main tbale
-------------------------------------------------------------------------
MERGE INTO CURRENCY.EXCHANGE_RATES AS TARGET
USING CURRENCY.EXCHANGE_RATES_STG AS SOURCE
ON TARGET.TIMESTAMP_UTC = SOURCE.TIMESTAMP_UTC
   AND TARGET.BASE_CURRENCY = SOURCE.BASE_CURRENCY
   AND TARGET.TARGET_CURRENCY = SOURCE.TARGET_CURRENCY  
WHEN NOT MATCHED THEN
    INSERT (
        TIMESTAMP_UTC,
        BASE_CURRENCY,
        TARGET_CURRENCY,
        EXCHANGE_RATE
    ) VALUES (
        SOURCE.
        TIMESTAMP_UTC,
        SOURCE.BASE_CURRENCY,
        SOURCE.TARGET_CURRENCY,
        SOURCE.EXCHANGE_RATE
    );


RETURN 1;

END;
$$;

------------------------------------------- Valdiation CODE --------------------------------------------------

TRUNCATE TABLE CURRENCY.EXCHANGE_RATES_STG;
TRUNCATE TABLE CURRENCY.EXCHANGE_RATES;
TRUNCATE TABLE CURRENCY.EXCHANGE_RATES_RAW;

select * from CURRENCY.EXCHANGE_RATES_RAW;
select * from CURRENCY.EXCHANGE_RATES_STG;
select * from CURRENCY.EXCHANGE_RATES;

select timestamp_utc, count(*) 
from CURRENCY.EXCHANGE_RATES 
group by timestamp_utc
order by timestamp_utc;

