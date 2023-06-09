import time

from aiogram import Bot, Dispatcher, executor, types

from config import *
from keyboards import *
from dms import *

telegram_bot = Bot(token=tg_token)
dp = Dispatcher(telegram_bot)


def get_params(call):
    params = {}
    for i in call.data.split("&"):
        params[i.split(":")[0]] = i.split(":")[1]
    return params


@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    await telegram_bot.send_message(text="Главное меню:", reply_markup=main_page_kb, chat_id=message.chat.id)


@dp.callback_query_handler(lambda x: x.data == "main_menu")
async def main_menu(call: types.callback_query):
    await telegram_bot.send_message(text="Главное меню:", reply_markup=main_page_kb, chat_id=call.message.chat.id)


# кнопка смотреть схемы
@dp.callback_query_handler(lambda x: x.data == "look_schemes")
async def look_schemes(call: types.callback_query):
    await telegram_bot.send_message(text="Что делаем?)", reply_markup=look_schemes_kb, chat_id=call.message.chat.id)


# кнопка новые схемы
@dp.callback_query_handler(lambda x: x.data == "new_schemes")
async def new_schemes(call: types.callback_query):
    keyboard = InlineKeyboardMarkup()
    new_line = True
    for i in db_request("SELECT id, name FROM schemes WHERE schemes.state <> -1 ORDER BY post_date DESC LIMIT 10").fetchall():
        button = InlineKeyboardButton(text=i[1], callback_data=f"view_id:{i[0]}&back:new_schemes")
        if new_line:
            keyboard.add(button)
        else:
            keyboard.insert(button)
        new_line = not new_line
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="look_schemes"))
    await telegram_bot.send_message(text="Последние загруженные схемы:", reply_markup=keyboard,
                                    chat_id=call.message.chat.id)


# кнопка лучшие схемы
@dp.callback_query_handler(lambda x: x.data == "best_schemes")
async def new_schemes(call: types.callback_query):
    keyboard = InlineKeyboardMarkup()
    new_line = True
    for i in db_request(
            "SELECT id, name FROM schemes WHERE schemes.state <> -1 ORDER BY (SELECT count(*) as likes_count FROM likes WHERE scheme = "
            "schemes.id) DESC LIMIT 10 ").fetchall():
        button = InlineKeyboardButton(text=i[1], callback_data=f"view_id:{i[0]}&back:best_schemes")
        if new_line:
            keyboard.add(button)
        else:
            keyboard.insert(button)
        new_line = not new_line
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="look_schemes"))
    await telegram_bot.send_message(text="Лучшие схемы по рейтингу:", reply_markup=keyboard,
                                    chat_id=call.message.chat.id)


# кнопка мои схемы
@dp.callback_query_handler(lambda x: x.data == "my_schemes")
async def new_schemes(call: types.callback_query):
    keyboard = InlineKeyboardMarkup()
    new_line = True

    schemes = db_request(
        f"SELECT id, name FROM schemes WHERE author = {call.message.chat.id} ORDER BY "
        f"post_date DESC LIMIT 10 AND schemes.state <> -1").fetchall()
    if len(schemes) != 0:
        for i in schemes:
            button = InlineKeyboardButton(text=i[1], callback_data=f"edit_id:{i[0]}&back:my_schemes")
            if new_line:
                keyboard.add(button)
            else:
                keyboard.insert(button)
            new_line = not new_line
    else:
        await telegram_bot.send_message(text="У тебя пока нет схем(", reply_markup=look_schemes_kb,
                                        chat_id=call.message.chat.id)
        return
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="look_schemes"))
    await telegram_bot.send_message(text="Твои схемы:", reply_markup=keyboard,
                                    chat_id=call.message.chat.id)


# просмотр схемы
@dp.callback_query_handler(lambda x: "view_id:" in x.data)
async def look_scheme(call: types.callback_query):
    params = get_params(call)
    is_like = db_request(
        f'SELECT count(*) FROM likes WHERE user = "{call.from_user.id}" AND scheme = {params["view_id"]}').fetchone()
    keyboard = InlineKeyboardMarkup()
    if is_like[0] != 0:
        keyboard.add(InlineKeyboardButton(text="Убрать лайк",
                                          callback_data=f"delete_like:{params['view_id']}&view_id:{params['view_id']}"))
    else:
        keyboard.add(InlineKeyboardButton(text="Поставить лайк",
                                          callback_data=f"add_like:{params['view_id']}&view_id:{params['view_id']}"))
    keyboard.insert(InlineKeyboardButton(text="Назад", callback_data=params['back']))

    stats = list(db_request(
        f'SELECT schemes.id, schemes.name, schemes.author, schemes.img, schemes.txt, schemes.state, '
        f'likes_tbl.likes_count, comments_tbl.comments_count, categories_tbl.category_name, '
        f'material_tbl.material_name, schemes.post_date FROM schemes LEFT JOIN (SELECT scheme, count(*) as '
        f'likes_count FROM likes WHERE scheme = {params["view_id"]}) as likes_tbl ON schemes.id = likes_tbl.scheme '
        f'LEFT JOIN (SELECT id as category_id, name as category_name FROM categories) as categories_tbl ON '
        f'schemes.category = categories_tbl.category_id LEFT JOIN (SELECT id as material_id, name as material_name '
        f'FROM materials) as material_tbl ON schemes.material = material_tbl.material_id LEFT JOIN (SELECT scheme, '
        f'count(*) as comments_count FROM comments WHERE scheme = {params["view_id"]}) as comments_tbl ON schemes.id '
        f'= comments_tbl.scheme WHERE schemes.id = {params["view_id"]} AND categories_tbl.category_id = '
        f'schemes.category AND material_tbl.material_id = schemes.material AND schemes.state <> -1').fetchone())

    if not stats[6]:
        stats[6] = 0
    if not stats[7]:
        stats[7] = 0
    stats[10] = time.strftime('%d-%m-%y', time.gmtime(stats[10]))
    await telegram_bot.send_message(
        text=f"Название: {stats[1]}\nID Автора: {stats[2]}\nКатегория: "
             f"{stats[8]}\nДата: {stats[10]}\nЛайков: {stats[6]}\nКомментариев: {stats[7]}\n",
        reply_markup=keyboard,
        chat_id=call.message.chat.id)
    for from_chat_id, message_id in db_request(
            f"SELECT chat, message FROM comments WHERE scheme = {params['view_id']}"):
        await telegram_bot.forward_message(chat_id=params['view_id'], from_chat_id=from_chat_id, message_id=message_id)


# редактирование схемы
@dp.callback_query_handler(lambda x: "edit_id:" in x.data)
async def edit_scheme(call: types.callback_query):
    params = get_params(call)
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Изменить", callback_data=f"change:{params['edit_id']}"))
    keyboard.insert(InlineKeyboardButton(text="Удалить", callback_data=f"submit_delete:{params['edit_id']}&back:{params['back']}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data=params['back']))
    stats = list(db_request(
        f'SELECT schemes.id, schemes.name, schemes.author, schemes.img, schemes.txt, '
        f'likes_tbl.likes_count, comments_tbl.comments_count, categories_tbl.category_name, '
        f'material_tbl.material_name, schemes.post_date FROM schemes LEFT JOIN (SELECT scheme, count(*) as '
        f'likes_count FROM likes WHERE scheme = {params["edit_id"]}) as likes_tbl ON schemes.id = likes_tbl.scheme '
        f'LEFT JOIN (SELECT id as category_id, name as category_name FROM categories) as categories_tbl ON '
        f'schemes.category = categories_tbl.category_id LEFT JOIN (SELECT id as material_id, name as material_name '
        f'FROM materials) as material_tbl ON schemes.material = material_tbl.material_id LEFT JOIN (SELECT scheme, '
        f'count(*) as comments_count FROM comments WHERE scheme = {params["edit_id"]}) as comments_tbl ON schemes.id '
        f'= comments_tbl.scheme WHERE schemes.id = {params["edit_id"]} AND categories_tbl.category_id = '
        f'schemes.category AND material_tbl.material_id = schemes.material AND schemes.state <> -1').fetchone())
    print(stats)
    if not stats[5]:
        stats[5] = 0
    if not stats[6]:
        stats[6] = 0
    stats[9] = time.strftime('%d-%m-%y', time.gmtime(stats[9]))

    await telegram_bot.send_message(
        text=f"Название: {stats[1]}\nID Автора: {stats[2]}\nКатегория: {stats[7]}\nДата: "
             f"{stats[9]}\nЛайков: {stats[5]}\nКомментариев: {stats[6]}\n",
        reply_markup=keyboard,
        chat_id=call.message.chat.id)
    for from_chat_id, message_id in db_request(
            f"SELECT chat, message FROM comments WHERE scheme = {params['edit_id']}"):
        await telegram_bot.forward_message(chat_id=params['edit_id'], from_chat_id=from_chat_id, message_id=message_id)


@dp.callback_query_handler(lambda x: "submit_delete:" in x.data)
async def submit_delete(call: types.callback_query):
    params = get_params(call)
    name = db_request(f"SELECT name FROM schemes WHERE id = {params['submit_delete']}").fetchone()[0]

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Да", callback_data=f"delete:{params['submit_delete']}"))
    keyboard.insert(InlineKeyboardButton(text="Нет", callback_data=f"edit_id:{params['submit_delete']}&back:{params['back']}"))

    await telegram_bot.send_message(text=f"Вы уверенны что хотите удалить схему {name}?", chat_id=call.message.chat.id, reply_markup=keyboard)


@dp.callback_query_handler(lambda x: "delete:" in x.data)
async def delete(call: types.callback_query):
    params = get_params(call)
    db_request(f"UPDATE schemes SET state = -1 WHERE id = {params['delete']}")
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Обратно в меню", callback_data=f"look_schemes"))
    await telegram_bot.send_message(text=f"Схема удалена", chat_id=call.message.chat.id, reply_markup=keyboard)


@dp.message_handler(content_types=["text"])
async def on_message(msg: types.Message):
    print(msg.from_user.id)


executor.start_polling(dp, skip_updates=True)
