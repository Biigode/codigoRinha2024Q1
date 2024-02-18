import asyncpg
import os
import asyncio


class DataBaseConnector:
    def __init__(self):
        self.pool = None
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.max_retries = 100
        self.wait_interval = 2  # segundos

    async def create_pool(self):
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                self.pool = await asyncpg.create_pool(
                    host=self.db_host,
                    port=self.db_port,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password,
                )
                print("Conexão com o banco de dados estabelecida com sucesso.")
                break  # Sai do loop após a conexão bem-sucedida
            except Exception as e:
                retry_count += 1
                print(f"Falha ao conectar com o banco de dados: {e}")
                print(
                    f"Tentando novamente em {self.wait_interval} segundos... (Tentativa {retry_count}/{self.max_retries})"
                )
                await asyncio.sleep(self.wait_interval)

        if retry_count == self.max_retries:
            print("Não foi possível conectar ao banco de dados após várias tentativas.")
            raise Exception("Falha ao estabelecer conexão com o banco de dados.")

    async def close_pool(self):
        await self.pool.close()

    async def execute_query(self, query, multi=False):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                if multi:
                    return await connection.fetch(query)
                else:
                    return await connection.fetchrow(query)

    async def execute_insert_query(self, query):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(query)
