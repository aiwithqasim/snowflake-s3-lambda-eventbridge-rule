import os
import json
import boto3
from snowflake import connector

class Provider:
    def __init__(self, **params):
        '''
        Initialize Provider class
        '''
        global app_id 

        # Initialize variables
        self.region_name = params['region_name']
        self.aws_db_creds_secret_id = params['aws_db_creds_secret_id']
        self.aws_db_creds_secret_value = params['aws_db_creds_secret_value']
        self.snowflake_db = params['snowflake_db']
        self.snowflake_role = params['snowflake_role']
        self.snowflake_wh = params['snowflake_wh']
        # self.schema = schema
        
        # Get boto3 client, db credentials
        self.client = self.get_client()
        self.db_creds = self.get_db_creds()
        
        # Set db credentials
        self.username = self.db_creds['username']
        self.password = self.db_creds['password']
        self.account_name = self.db_creds['account_name']
        app_id = self.db_creds.get('app_id')
        

    def get_client(self):
        '''
        Create a boto3 client for secretsmanager
        '''
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager", region_name=self.region_name)
        return client
        

    def get_db_creds(self):
        '''
        Get db credentials from AWS secret manager
        '''
        get_secret_value_response = self.client.get_secret_value(SecretId=self.aws_db_creds_secret_id)
        db_creds = json.loads(get_secret_value_response['SecretString'])[f'{self.aws_db_creds_secret_value}']
        return db_creds
    
    def get_creds_from_secret(self, secret_id):
        '''
        Get credentials from AWS secret manager
        '''
        get_secret_value_response = self.client.get_secret_value(SecretId=secret_id)
        creds = json.loads(get_secret_value_response['SecretString'])
        return creds
        
        
    def get_snowflake_conn(self):
        '''
        Get snowflake connection
        '''
        params = dict(
            user=self.username,
            password=self.password,
            account=self.account_name,
            role=self.snowflake_role,
            warehouse=self.snowflake_wh,
            database=self.snowflake_db,
        )
        conn = connector.connect(**params)
        return conn


    def get_config(self, schema):
        '''
        Get config table values from snowflake database
        '''
        sql_query =f"""select name, value from {self.snowflake_db}.{schema}.CONFIG where type in ('sql','variable') and active_flag = TRUE;"""
        
        self.conn = self.get_snowflake_conn()
        
        with self.conn as ctx:
            cur = ctx.cursor()
            cur.execute(sql_query)
            df_get_sqls = cur.fetch_pandas_all()
            self.conn.close()
        
        # Creating environment variables
        for index, row in df_get_sqls.iterrows():
            os.environ[row['NAME']] = row['VALUE']
        
        return df_get_sqls

    def get_data_from_sql(self,sql_query):
        '''
        Get data from snowflake database
        (Execute DQL query using connection)
        '''    

        self.conn = self.get_snowflake_conn()
        with self.conn as ctx:
            cur = ctx.cursor()
            cur.execute(sql_query)
            df = cur.fetch_pandas_all()
            return df
        
    def get_large_data_from_sql(self,sql_query, chunksize=0):
        '''
        Get data from snowflake database
        (Execute DQL query using connection)
        '''    

        self.conn = self.get_snowflake_conn()
        with self.conn as ctx:
            cur = ctx.cursor()
            cur.execute(sql_query)
            
            # logger.info(f"The query id is: "+cur.sfqid)
            # df = cur.fetch_pandas_batches()
            # return pd.DataFrame.from_records(iter(cur), columns=[x[0] for x in cur.description], nrows=50000)
            if chunksize == 0:
                return "Please provide chunksize"
            yield from cur.fetch_pandas_batches(chunk_size=chunksize)

    
    def exe_query(self, sql_query, params=None):
        '''
        Execute DDL / DML query using connection
        Supports parameter binding
        '''
        self.conn = self.get_snowflake_conn()
        with self.conn as ctx:
            cur = ctx.cursor()
            if params:
                cur.execute(sql_query, params)
            else:
                cur.execute(sql_query)