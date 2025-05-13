import os
import json
import boto3
import requests
from snowflake_provider import Provider
from datetime import datetime, timedelta, timezone

def connect_to_snowflake():
    '''
    Building conenction with snowflake using custom provider class.
    '''
    params = {
        'region_name': os.environ['region_name'],
        'aws_db_creds_secret_id': 'db/currency-echange-rate',
        'aws_db_creds_secret_value': 'fusion_snowflake',    
        'snowflake_db': os.environ['snowflake_db'],
        'snowflake_role': os.environ['snowflake_role'],
        'snowflake_wh':  os.environ['snowflake_wh'],
        'environment': os.environ['environment']
    }

    provider = Provider(**params)

    return provider

def s3_client(json_data,timestamp):
    '''
    Dumping reposne to S3 as json file.
    '''
    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S') 
    year = dt.strftime('%Y')
    month = dt.strftime('%m')
    day = dt.strftime('%d')
    hour = dt.strftime('%H')

    s3_key = f"exchange_rates/{year}/{month}/{day}/exchange-rates-{hour}.json"
    s3_bucket_name = os.environ.get('s3_bucket_name')


    s3 = boto3.client("s3")
    s3.put_object(Bucket=s3_bucket_name, Key=s3_key, Body=json_data)


def insert_exchange_rates_to_snowflake():
    '''
    This function is performing following tasks.
    1. Getting data from API.
    2. Calling s3_client fucntion to dump data into S3
    3. Dumping data to Snowflake
    '''
    provider = connect_to_snowflake()

    base_url = os.environ.get("oer_base_url")
    app_id = os.environ.get("oer_app_id")
    base_currency = os.environ.get("oer_base_currency", "USD")

    url = f"{base_url}?app_id={app_id}&base={base_currency}"

    response = requests.get(url)

    if response.status_code == 200:
            data = response.json()
            timestamp = datetime.fromtimestamp(data['timestamp'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

            schema = "CURRENCY"
            table_name = "EXCHANGE_RATES_RAW"
            json_data = json.dumps(data)
            s3_client(json_data,timestamp)

            query2 = f"""
            CALL {CURRENCY}.SP_EXCHANGE_RATE_LOADING(%s, %s);
            """

            provider.exe_query(query2, (json_data,timestamp,))      

    else:
        raise Exception(f"API request failed with status code {response.status_code}")

def lambda_handler(event, context):
        
    insert_exchange_rates_to_snowflake()

    return {'statusCode': 200}