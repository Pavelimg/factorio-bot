from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_page_kb = InlineKeyboardMarkup()
main_page_kb.add(InlineKeyboardButton(text="Профиль", callback_data="profile"))
main_page_kb.add(InlineKeyboardButton(text="Новая схема", callback_data="new_scheme"))
main_page_kb.insert(InlineKeyboardButton(text="Смотреть схемы", callback_data="look_schemes"))

look_schemes_kb = InlineKeyboardMarkup()
look_schemes_kb.add(InlineKeyboardButton(text="Найти схему", callback_data="find_scheme"))
look_schemes_kb.add(InlineKeyboardButton(text="Лучшие схемы", callback_data="best_schemes"))
look_schemes_kb.insert(InlineKeyboardButton(text="Мои схемы", callback_data="my_schemes"))
look_schemes_kb.add(InlineKeyboardButton(text="Новые схемы", callback_data="new_schemes"))
look_schemes_kb.insert(InlineKeyboardButton(text="Главная страница", callback_data="main_menu"))
