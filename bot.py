import time

from aiogram import Bot, Dispatcher, executor, types

from math import ceil
from config import *
from keyboards import *
from dms import *

telegram_bot = Bot(token=tg_token)
dp = Dispatcher(telegram_bot)

user_last_action = {}


def get_params(call):
    params = {}
    for i in call.data.split("&"):
        split_text = i.split(":")
        if len(split_text) == 2:
            params[split_text[0]] = split_text[1]
    return params


def get_user_state(user):
    if user in user_last_action:
        return user_last_action[user]


def user_page_change(user, page):
    user_last_action[user] = page


@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    await telegram_bot.send_message(text="Главное меню:", reply_markup=main_page_kb, chat_id=message.chat.id)


@dp.callback_query_handler(lambda x: x.data == "main_menu")
async def main_menu(call: types.callback_query):
    user_page_change(call.message.chat.id, "main_menu")
    await telegram_bot.send_message(text="Главное меню:", reply_markup=main_page_kb, chat_id=call.message.chat.id)


# кнопка смотреть схемы
@dp.callback_query_handler(lambda x: x.data == "look_schemes")
async def look_schemes(call: types.callback_query):
    user_page_change(call.message.chat.id, "look_schemes")
    await telegram_bot.send_message(text="Что делаем?)", reply_markup=look_schemes_kb, chat_id=call.message.chat.id)


# кнопка новые схемы
@dp.callback_query_handler(lambda x: x.data.startswith("new_schemes"))
async def best_schemes(call: types.callback_query):
    user_page_change(call.message.chat.id, "new_schemes")
    params = get_params(call)
    keyboard = InlineKeyboardMarkup()
    new_line = True
    req = db_request(
        "SELECT id, name FROM schemes WHERE schemes.state <> -1 ORDER BY post_date DESC").fetchall()
    if "page" in params.keys():
        current_page = int(params['page'])
    else:
        current_page = 1

    for i in range(10 * (current_page - 1), min(current_page * 10, len(req))):
        button = InlineKeyboardButton(text=req[i][1], callback_data=f"view_id:{req[i][0]}&back:new_schemes&page:{current_page}")
        if new_line:
            keyboard.add(button)
        else:
            keyboard.insert(button)
        new_line = not new_line

    preview_page = InlineKeyboardButton(text="Предыдущая страница",
                                        callback_data=f"new_schemes&page:{current_page - 1}")
    next_page = InlineKeyboardButton(text="Следующая страница",
                                     callback_data=f"new_schemes&page:{current_page + 1}")
    back = InlineKeyboardButton(text="Назад", callback_data="look_schemes")
    if current_page != 1 and current_page * 10 < len(req):
        keyboard.add(preview_page)
        keyboard.insert(next_page)
    elif current_page == 1:
        keyboard.add(next_page)
    elif current_page * 10 > len(req):
        keyboard.add(preview_page)
    keyboard.add(back)
    await telegram_bot.send_message(text=f"Самые новые схемы (Страница {current_page}/{ceil(len(req) / 10)}):",
                                    reply_markup=keyboard,
                                    chat_id=call.message.chat.id)


# кнопка лучшие схемы
@dp.callback_query_handler(lambda x: x.data.startswith("best_schemes"))
async def best_schemes(call: types.callback_query):
    user_page_change(call.message.chat.id, "best_schemes")
    params = get_params(call)
    keyboard = InlineKeyboardMarkup()
    new_line = True
    req = db_request(
        "SELECT id, name FROM schemes WHERE schemes.state <> -1 ORDER BY (SELECT count(*) as likes_count FROM likes WHERE scheme = "
        "schemes.id) DESC ").fetchall()
    if "page" in params.keys():
        current_page = int(params['page'])
    else:
        current_page = 1

    for i in range(10 * (current_page - 1), min(current_page * 10, len(req))):
        button = InlineKeyboardButton(text=req[i][1], callback_data=f"view_id:{req[i][0]}&back:best_schemes&page:{current_page}")
        if new_line:
            keyboard.add(button)
        else:
            keyboard.insert(button)
        new_line = not new_line

    preview_page = InlineKeyboardButton(text="Предыдущая страница",
                                        callback_data=f"best_schemes&page:{current_page - 1}")
    next_page = InlineKeyboardButton(text="Следующая страница",
                                     callback_data=f"best_schemes&page:{current_page + 1}")
    back = InlineKeyboardButton(text="Назад", callback_data="look_schemes")
    if current_page != 1 and current_page * 10 < len(req):
        keyboard.add(preview_page)
        keyboard.insert(next_page)
    elif current_page == 1:
        keyboard.add(next_page)
    elif current_page * 10 > len(req):
        keyboard.add(preview_page)
    keyboard.add(back)
    await telegram_bot.send_message(text=f"Лучшие схемы по рейтингу (Страница {current_page}/{ceil(len(req) / 10)}):",
                                    reply_markup=keyboard,
                                    chat_id=call.message.chat.id)


# кнопка мои схемы
@dp.callback_query_handler(lambda x: x.data == "my_schemes")
async def new_schemes(call: types.callback_query):
    user_page_change(call.message.chat.id, "my_schemes")
    keyboard = InlineKeyboardMarkup()
    new_line = True

    schemes = db_request(
        f"SELECT id, name FROM schemes WHERE author = {call.message.chat.id} AND state <> -1 ORDER BY "
        f"post_date DESC LIMIT 10 ").fetchall()
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


# поиск схемы
@dp.callback_query_handler(lambda x: "find_scheme" in x.data)
async def find_scheme(call: types.callback_query):
    user_page_change(call.message.chat.id, "find_scheme")
    await telegram_bot.send_message(chat_id=call.from_user.id, text="Отправь название схемы")


@dp.callback_query_handler(lambda x: "add_like:" in x.data or "delete_like:" in x.data)
async def look_scheme(call: types.callback_query):
    params = get_params(call)
    if "add_like" in params.keys():
        db_request(f'INSERT INTO likes VALUES ({call.message.chat.id}, {params["add_like"]})')
    else:
        db_request(f'DELETE FROM likes WHERE user = {call.message.chat.id} and scheme = {params["delete_like"]}')
    await look_scheme(call)


@dp.callback_query_handler(lambda x: "delete_comm:" in x.data)
async def look_scheme(call: types.callback_query):
    params = get_params(call)
    db_request(f"DELETE FROM comments WHERE scheme ={params['delete_comm']} AND chat = {call.message.chat.id}")
    await look_scheme(call)


# просмотр схемы
@dp.callback_query_handler(lambda x: "view_id:" in x.data)
async def look_scheme(call: types.callback_query):
    params = get_params(call)
    user_page_change(call.message.chat.id, f"view:{params['view_id']}")
    user, scheme = call.from_user.id, params["view_id"]
    req = list(db_request(
        f'SELECT count(*) as likes_count, comments_tbl.comments_count FROM likes LEFT JOIN (SELECT count(*) as comments_count, scheme, chat FROM comments WHERE scheme = {scheme} AND chat = {user}) as comments_tbl ON likes.user = comments_tbl.chat WHERE likes.user = {user} AND likes.scheme = {scheme} UNION ALL SELECT likes_tbl.likes_count, count(*) as comments_count FROM comments LEFT JOIN (SELECT count(*) as likes_count, scheme, user FROM likes WHERE scheme = {scheme} AND user = {user}) as likes_tbl ON comments.chat = likes_tbl.user WHERE comments.chat= {user} AND comments.scheme = {scheme}').fetchall())
    is_like, is_comm = req[0][0], req[1][1]
    keyboard = InlineKeyboardMarkup()
    if is_like != 0:
        keyboard.add(InlineKeyboardButton(text="Убрать лайк",
                                          callback_data=f"delete_like:{params['view_id']}&back:{params['back']}&view_id:{params['view_id']}"))
    else:
        keyboard.add(InlineKeyboardButton(text="Поставить лайк",
                                          callback_data=f"add_like:{params['view_id']}&back:{params['back']}&view_id:{params['view_id']}"))
    if is_comm != 0:
        keyboard.insert(InlineKeyboardButton(text="Удалить коментарии",
                                             callback_data=f"delete_comm:{params['view_id']}&back:{params['back']}&view_id:{params['view_id']}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data=f"{params['back']}&page:{params['page']}"))

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
        try:
            await telegram_bot.forward_message(chat_id=call.from_user.id, from_chat_id=from_chat_id,
                                               message_id=message_id)
        except Exception:
            pass


# редактирование схемы
@dp.callback_query_handler(lambda x: "edit_id:" in x.data)
async def edit_scheme(call: types.callback_query):
    user_page_change(call.message.chat.id, "edit")
    params = get_params(call)
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Изменить", callback_data=f"change:{params['edit_id']}"))
    keyboard.insert(
        InlineKeyboardButton(text="Удалить", callback_data=f"submit_delete:{params['edit_id']}&back:{params['back']}"))
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


# удалять или нет?
@dp.callback_query_handler(lambda x: "submit_delete:" in x.data)
async def submit_delete(call: types.callback_query):
    user_page_change(call.message.chat.id, "submit_delete")
    params = get_params(call)
    name = db_request(f"SELECT name FROM schemes WHERE id = {params['submit_delete']}").fetchone()[0]

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Да", callback_data=f"delete:{params['submit_delete']}"))
    keyboard.insert(
        InlineKeyboardButton(text="Нет", callback_data=f"edit_id:{params['submit_delete']}&back:{params['back']}"))

    await telegram_bot.send_message(text=f"Вы уверенны что хотите удалить схему {name}?", chat_id=call.message.chat.id,
                                    reply_markup=keyboard)


# удаление
@dp.callback_query_handler(lambda x: "delete:" in x.data)
async def delete(call: types.callback_query):
    params = get_params(call)
    db_request(f"UPDATE schemes SET state = -1 WHERE id = {params['delete']}")
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Обратно в меню", callback_data=f"look_schemes"))
    await telegram_bot.send_message(text=f"Схема удалена", chat_id=call.message.chat.id, reply_markup=keyboard)


@dp.callback_query_handler(lambda x: "search_page:" in x.data)
async def search_page(call: types.callback_query):
    params = get_params(call)
    current_page = int(params['search_page'])
    res = db_request(
        f"SELECT id, name FROM schemes WHERE lower_name like '%{params['req']}%' ORDER BY post_date DESC").fetchall()
    keyboard = InlineKeyboardMarkup()
    new_line = True
    for i in range((current_page - 1) * 10, min(10 * current_page, len(res))):
        button = InlineKeyboardButton(text=res[i][1], callback_data=f"view_id:{res[i][0]}&back:look_schemes")
        if new_line:
            keyboard.add(button)
        else:
            keyboard.insert(button)
        new_line = not new_line
    preview_page = InlineKeyboardButton(text="Предыдущая страница",
                                        callback_data=f"search_page:{current_page - 1}&req:{params['req']}")
    next_page = InlineKeyboardButton(text="Следующая страница",
                                     callback_data=f"search_page:{current_page + 1}&req:{params['req']}")

    back = InlineKeyboardButton(text="Назад", callback_data="look_schemes")
    if current_page != 1 and current_page * 10 < len(res):
        keyboard.add(preview_page)
        keyboard.insert(next_page)
    elif current_page == 1:
        keyboard.add(next_page)
    elif current_page * 10 > len(res):
        keyboard.add(preview_page)
    keyboard.add(back)

    await telegram_bot.send_message(text=f"Страница {current_page}/{ceil(len(res) / 10)} по запросу '{params['req']}'",
                                    chat_id=call.from_user.id,
                                    reply_markup=keyboard)


@dp.message_handler(content_types=["text"])
async def on_message(msg: types.Message):
    if "view" in get_user_state(msg.from_user.id):
        db_request(
            f"INSERT INTO comments VALUES ({get_user_state(msg.from_user.id).split(':')[1]}, {msg.from_user.id}, {msg.message_id})")
        await telegram_bot.send_message(text="Комментарий добавлен", chat_id=msg.chat.id)
    if "find_scheme" in get_user_state(msg.from_user.id):
        res = db_request(
            f"SELECT id, name FROM schemes WHERE lower_name like '%{msg.text}%' ORDER BY post_date DESC").fetchall()
        keyboard = InlineKeyboardMarkup()
        new_line = True
        if len(res) != 0:
            for i in range(min(10, len(res))):
                button = InlineKeyboardButton(text=res[i][1], callback_data=f"view_id:{res[i][0]}&back:look_schemes")
                if new_line:
                    keyboard.add(button)
                else:
                    keyboard.insert(button)
                new_line = not new_line

            if len(res) > 10:
                keyboard.add(
                    InlineKeyboardButton(text="Следующая страница", callback_data=f"search_page:2&req:{msg.text}"))
            keyboard.add(InlineKeyboardButton(text="Назад", callback_data=f"look_schemes"))
            await telegram_bot.send_message(text=f'По запросу "{msg.text}" найдено {len(res)} схем:',
                                            chat_id=msg.from_user.id, reply_markup=keyboard)
        else:
            await telegram_bot.send_message(text=f"Ничего не найдено(", chat_id=msg.from_user.id,
                                            reply_markup=look_schemes_kb)


executor.start_polling(dp, skip_updates=True)
