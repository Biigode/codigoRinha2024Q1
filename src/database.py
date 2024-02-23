import psycopg
import os
from dotenv import load_dotenv
import time

load_dotenv()


class DataBaseConnector:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        # self.connect()

    async def execute_query(self, query, multi=False):
        """Executa uma consulta no banco de dados."""

        aconn = await psycopg.AsyncConnection.connect(
            autocommit=True,
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
        )
        if aconn is not None:
            async with aconn:
                acur = aconn.cursor()
                await acur.execute(query)
        if multi:
            result = await acur.fetchall()
        else:
            result = await acur.fetchone()
        return result

    async def execute_insert_query(self, query):
        """Executa uma operação de inserção no banco de dados."""
        aconn = await psycopg.AsyncConnection.connect(
            autocommit=True,
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
        )
        if aconn is not None:
            async with aconn:
                acur = aconn.cursor()
                await acur.execute(query)
        else:
            print("Falha ao conectar ao banco de dados.")
