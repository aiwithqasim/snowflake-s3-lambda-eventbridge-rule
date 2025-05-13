# Currency Exchange Rate Pipeline

A serverless ETL pipeline for fetching, storing, and processing currency exchange rates from Open Exchange Rates API to Snowflake, using AWS Lambda and S3.

## Overview

This project provides an automated solution for retrieving real-time currency exchange rates and storing them in a structured format in Snowflake. The pipeline involves:

1. Fetching exchange rates from the Open Exchange Rates API via AWS Lambda
2. Storing the raw JSON response in an S3 bucket
3. Processing and loading the data into Snowflake tables for analysis

## Architecture

![Architecture Diagram](https://github.com/username/snowflake-aws/raw/main/architecture-diagram.png)

- **AWS Lambda**: Executes the main ETL process on a schedule
- **Amazon S3**: Stores raw exchange rate data as JSON files
- **AWS Secrets Manager**: Securely manages database credentials
- **Snowflake**: Stores and processes the exchange rate data

## Prerequisites

- AWS Account with appropriate permissions
- Snowflake account with database creation privileges
- Open Exchange Rates API key (https://openexchangerates.org/)
- Python 3.9

## Setup Instructions

### AWS Setup

1. Create an IAM role with the following permissions:
   - S3FullAccess
   - Lambda execution role
   - EventBridge access
   - Lambda full access

2. Create a Secrets Manager secret with the ID `db/currency-exchange-rate` containing Snowflake credentials:
   ```json
   {
     "fusion_snowflake": {
       "username": "your_username",
       "password": "your_password",
       "account_name": "your_snowflake_account"
     }
   }
   ```

3. Create an S3 bucket for storing the raw exchange rate data

### Snowflake Setup

1. Run the SQL scripts in `code/snowflake.sql` to:
   - Create the `CURRENCY_DB` database and `CURRENCY` schema
   - Create the necessary tables (`EXCHANGE_RATES_RAW`, `EXCHANGE_RATES_STG`, `EXCHANGE_RATES`)
   - Create the stored procedure for data processing

### Lambda Function Setup

1. Create a new Lambda function using Python 3.8+
2. Upload the code from `code/lambda_function.py` and `code/snowflake_provider.py`
3. Set up the following environment variables:
   - `environment`: DEV
   - `oer_app_id`: YOUR-APP-KEY
   - `oer_base_currency`: USD
   - `oer_base_url`: https://openexchangerates.org/api/latest.json
   - `region_name`: us-east-1
   - `s3_bucket_name`: s3-currency-exchange-rate-qh
   - `snowflake_db`: CURRENCY_DB
   - `snowflake_role`: ACCOUNTADMIN
   - `snowflake_wh`: COMPUTE_WH

4. Configure an EventBridge (CloudWatch Events) trigger to run the Lambda function on your desired schedule

## Project Structure

```
.
├── code/
│   ├── lambda_function.py     # Main AWS Lambda function
│   ├── snowflake_provider.py  # Snowflake connection and query utility
│   └── snowflake.sql          # SQL scripts for Snowflake setup
├── environment-variables.txt  # Required environment variables
├── roles.txt                  # Required AWS IAM roles
├── secret-manager.txt         # Instructions for secrets management
└── convention.txt             # Project conventions and guidelines
```

## How It Works

1. The Lambda function is triggered on a schedule
2. It fetches the latest exchange rates from the Open Exchange Rates API
3. The raw JSON response is stored in the S3 bucket with a structured path: `exchange_rates/{year}/{month}/{day}/exchange-rates-{hour}.json`
4. The data is inserted into the `EXCHANGE_RATES_RAW` table in Snowflake
5. A stored procedure (`SP_EXCHANGE_RATE_LOADING`) processes the raw data:
   - Extracts relevant information into the staging table
   - Merges the staging data into the final `EXCHANGE_RATES` table

## Monitoring and Maintenance

- AWS CloudWatch can be used to monitor Lambda function executions
- Snowflake provides query history and usage monitoring
- Check the Snowflake tables regularly to ensure data is being loaded correctly

## License

[MIT License](LICENSE)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request 