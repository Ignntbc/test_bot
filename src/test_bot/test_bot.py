import os
from pyrogram import Client as AsyncClient
from pyrogram import idle
import asyncio
from dotenv import load_dotenv
from db.db import DbManager
from handlers.handlers import define_handlers, get_ready_users

load_dotenv()

async def main():
    app = AsyncClient(
        name=os.getenv("APP_NAME"),
        api_id=os.getenv("APP_API_ID"),
        api_hash=os.getenv("APP_API_HASH")
    )
    await app.start()
    
    asyncio.create_task(get_ready_users(app))
    asyncio.create_task(define_handlers(app))
    # await get_ready_users(app)
    # await define_handlers(app)
    
    await idle() 
if __name__ == "__main__":
    asyncio.run(main())