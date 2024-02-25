import os
from contextlib import asynccontextmanager
from typing import Optional#, AsyncIterator
import asyncpg
import asyncio
from dotenv import load_dotenv

load_dotenv()
MAX_POOL_SIZE = 4
MIN_POOL_SIZE = 2

class DbManager:
    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASS")
        self._pool = None

    async def create_pool(self):
        self._pool = await asyncpg.create_pool(
            host=self.host,
            port=self.port,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
            max_size=MAX_POOL_SIZE,
            min_size=MIN_POOL_SIZE,
        )

    @asynccontextmanager
    async def __transaction(self):
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                try:
                    yield conn
                except Exception as ex:
                    print(ex)
                    raise
    
    async def close(self):
        if self._pool is not None:
            await self._pool.close()

    async def exec_query(
        self,
        command: str,
        *args: tuple,
        fetchval: bool = False,
        fetchall: bool = False,
        fetchone: bool = False,
        response_as_dict: bool = True,
    ) -> Optional[any]:
        async with self.__transaction() as connection:
            result = None
            if fetchval:
                result = await connection.fetchval(command, *args)
            elif fetchall:
                result = await connection.fetch(command, *args)
            elif fetchone:
                result = await connection.fetchrow(command, *args)

            if response_as_dict and result:
                if fetchone:
                    result = dict(result)
                elif fetchall:
                    result = [dict(row) for row in result]
            else:
                await connection.execute(command, *args)
            

            return result

    async def insert_user(self, user_id: int):
        query = "INSERT INTO user_info (user_id_telegram, created_at, status_id, status_updated_at, stage_id) VALUES ($1 , now(), 1, now(), 1)"
        await self.exec_query(query, user_id)

    async def examinate_user(self, user_id: int):
        query = "SELECT user_id_telegram FROM user_info WHERE user_id_telegram = $1"
        return await self.exec_query(query, user_id, fetchone=True)
    
    async def get_ready_users(self):
        query = '''SELECT user_id_telegram, stage_id
                    FROM user_info
                    WHERE status_id = 1
                    AND (
                        CASE
                            WHEN stage_id = 1 AND EXTRACT(EPOCH FROM NOW() - status_updated_at)/60 >= 6 THEN TRUE
                            WHEN stage_id = 2 AND EXTRACT(EPOCH FROM NOW() - status_updated_at)/60 >= 39 THEN TRUE
                            WHEN stage_id = 3 AND EXTRACT(EPOCH FROM NOW() - status_updated_at)/60/60 >= 26 THEN TRUE
                            ELSE FALSE
                        END
                    )'''
        return await self.exec_query(query, fetchall=True)
    async def update_user_status(self, user_id: int, status_id: int):
        query = "UPDATE user_info SET status_id = $1, status_updated_at = now() WHERE user_id_telegram = $2"
        await self.exec_query(query, status_id, user_id)

    async def update_user_stage(self, user_id: int, stage_id: int):
        query = "UPDATE user_info SET stage_id = $1 WHERE user_id_telegram = $2"
        await self.exec_query(query, stage_id, user_id)


async def main():
    db_manager = DbManager()
    await db_manager.create_pool()
    ready_users = await db_manager.get_ready_users()
    result = await db_manager.examinate_user(1234567890)
    result2 = await db_manager.examinate_user(1234567899)
    result3 = await db_manager.insert_user(1234567899)
    result4 = await db_manager.examinate_user(1234567899)
    result5 = await db_manager.insert_user(1234567890)
    await db_manager.close()
    print(ready_users)
    # print(result, result2, result3, result4, result5)

asyncio.run(main())
