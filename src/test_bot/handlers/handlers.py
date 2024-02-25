import logging
from pyrogram import filters
from db.db import DbManager
from asyncio import sleep
from pyrogram.errors import UserIsBlocked, UserDeactivated, UserNotParticipant, PeerIdInvalid

logging.debug("A DEBUG Message")
logging.info("An INFO")
logging.warning("A WARNING")
logging.error("An ERROR")
logging.critical("A message of CRITICAL severity")


message_scripts = {1: "Текст 1", 2: "Текст 2", 3: "Текст 3"}
timing_sec = 60
triger_words = ["Прекрасно", "Ожидать"]


async def define_handlers(app):
    @app.on_message(filters.private)
    async def new_user_message(client, message):
        try:
            db_manager = DbManager()
            await db_manager.create_pool()
            examinate_result = await db_manager.examinate_user(message.from_user.id)

            if examinate_result and not any(word in message.text for word in triger_words):
                await message.reply_text("Вы уже зарегистрированы")

            elif any(word in message.text for word in triger_words):
                await message.reply_text("Спасибо, что поделились")
                await db_manager.update_user_status(message.from_user.id, 3)

            else:
                await db_manager.insert_user(message.from_user.id)
                await message.reply_text("Вы зарегистрированы")
        except Exception:
            logging.exception('Ошибка при обработке сообщения пользователя')

async def get_ready_users(app):
    db_manager = DbManager()
    await db_manager.create_pool()
    while True:
        ready_users = await db_manager.get_ready_users()
        for _,user in enumerate(ready_users):
            print(user)
            try:
                await app.send_message(user["user_id_telegram"], message_scripts[user["stage_id"]])
                if user["stage_id"] == 3:
                    await db_manager.update_user_status(user["user_id_telegram"], 3)
                else:
                    await db_manager.update_user_stage(user["user_id_telegram"], user["stage_id"] + 1)

            except (UserIsBlocked, UserDeactivated, UserNotParticipant, PeerIdInvalid):
                await db_manager.update_user_status(user["user_id_telegram"], 2)
            except Exception:
                logging.exception('Ошибка при отправке сообщения пользователю')

        await sleep(timing_sec)
