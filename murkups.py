from aiogram import types

Exit = types.KeyboardButton("Выйти")
back = types.KeyboardButton("Назад")


stopoffer = types.KeyboardButton("Отменить")
stopKbOffer = types.ReplyKeyboardMarkup(resize_keyboard=True).add(stopoffer)
#Клавиатура при команде start
mainkb = types.ReplyKeyboardMarkup(resize_keyboard=True)
mainkb.add("Предложить изменения/Что то улучшить").add ("Найти сотрудника")

#Клавиатура по изменению/улучшению
changekb = types.ReplyKeyboardMarkup(resize_keyboard=True)
changekb.row("Готов участвовать в реализации идеи!", "Анонимно с модерацией").add(back)

#Клавиатура для Найти сотрудника
findemployeb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(back)

#Клавиатура админа для работы с базой данных
adminKBdb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("Показать всех", "Добавить", "Удалить").add(Exit)
stopDeleteKB = types.ReplyKeyboardMarkup(resize_keyboard=True).add("Отменить удаление")
stopAddKB = types.ReplyKeyboardMarkup(resize_keyboard=True).add("Отменить добавление")

#Клавиатура админа для выбора метода удаления
adminKBremove = types.ReplyKeyboardMarkup(resize_keyboard=True).add("По ID","По фамилии").add("Отменить удаление")

#Клавиатура для отправки ответа
moderChatKB = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Ответить", callback_data="moder"))