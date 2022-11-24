import os

import openpyxl as opx

from aiogram.types import InputFile
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text, ForwardedMessageFilter, ChatTypeFilter
from aiogram.dispatcher import FSMContext
import FSM
from sqldb import *

import config
import murkups

bot = Bot(token=config.TOKEN_API)
dp = Dispatcher(bot, storage=FSM.storage)


@dp.message_handler(commands=["start"])
async def start_com(mes: types.Message):
    if mes.chat.type == "group":
        return
    await mes.answer("Добро пожаловать в бота! (Текст нужно заменить)\nВыберите команду:",
                     reply_markup=murkups.mainkb)

@dp.message_handler(Text("Выйти", ignore_case=True), state="*")
@dp.message_handler(Text("Назад", ignore_case=True), state="*")
async def back_find_employee(mes: types.Message, state: FSMContext):
    if mes.chat.type == "group":
        return
    await state.finish()
    await mes.answer("Главное меню", reply_markup=murkups.mainkb)


@dp.message_handler(Text("Отменить", ignore_case=True), state="*")
async def back_send_offer(mes: types.Message, state: FSMContext):
    if mes.chat.type == "group":
        return
    await state.finish()
    await mes.answer("Выберите команду: ", reply_markup=murkups.changekb)

@dp.message_handler(Text("Отменить добавление", ignore_case=True), state=FSM.AdminSendFileDB.waitFileExel)
@dp.message_handler(Text("Отменить удаление", ignore_case=True), state=[FSM.AdminSendFileDB.waitToRemove,
                                                                        FSM.AdminSendFileDB.removeByID,
                                                                        FSM.AdminSendFileDB.removeBySurname,
                                                                        FSM.AdminSendFileDB.waitID])
async def stop_admin(mes: types.Message, state: FSMContext):
    if mes.chat.type == "group":
        return
    await FSM.AdminSendFileDB.waitCommand.set()
    await mes.answer("Выберите команду: ", reply_markup=murkups.adminKBdb)

@dp.message_handler(commands="admin")
async def admin_panel_db(mes:types.Message):
    if mes.chat.type == "group":
        return
    list_usernames = cur.execute("SELECT id_login_tg FROM admins").fetchall()
    if not mes.from_user.username in [log[0] for log in list_usernames]:
        await mes.answer(f"@{mes.from_user.username}, к сожаленю у вас нет доступа к этой команде!")
        return
    await mes.answer(f"Здравствуйте, {mes.from_user.first_name }.\nДобро пожаловать в Админ панель!", reply_markup=murkups.adminKBdb)
    await FSM.AdminSendFileDB.waitCommand.set()

@dp.message_handler(Text("Показать всех", ignore_case=True), state=FSM.AdminSendFileDB.waitCommand)
async def show_all_employye_db(mes: types.Message):
    list_employee = cur.execute("SELECT * FROM employee").fetchall()
    if len(list_employee)==0:
        await mes.answer("База данных пуста!")
        return
    m = ""
    for emp in list_employee:
        m+=f"<b>ID-{emp[0]}</b>\n├<b>ФИО:</b> {emp[2]} {emp[3]} {emp[4]}\n├<b>Telegram:</b> @{emp[1]}\n├<b>Телефон:</b> {emp[5]}\n├<b>Дата рождения:</b> {emp[6]}\n└<b>В отпуске:</b> {emp[7]}\n\n"
    await mes.answer("Список всех записей в БД:\n\n"+m, parse_mode=types.ParseMode.HTML)

@dp.message_handler(Text("Добавить", ignore_case=True), state=FSM.AdminSendFileDB.waitCommand)
async def add_employye_db(mes:types.Message):
    await mes.answer("Заполните шаблон и отправьте в чат.", reply_markup=murkups.stopAddKB)
    await bot.send_document(mes.from_user.id, InputFile("Шаблон для добавления в БД.xlsx"))
    await FSM.AdminSendFileDB.waitFileExel.set()

@dp.message_handler(content_types=types.ContentType.DOCUMENT, state=FSM.AdminSendFileDB.waitFileExel)
async def work_with_exel(mes:types.Message):
    file = await bot.get_file(mes.document.file_id)
    await bot.download_file(file.file_path, f"data/{mes.message_id}.xlsx")
    wb = opx.open(f"data/{mes.message_id}.xlsx")
    sheet = wb.active
    for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row ):
        try:
            cur.execute("INSERT INTO employee (id_login_tg, surname, name, patronymic, phone_numb, birthday, vacation) VALUES (?,?,?,?,?,?,?)",
                        (row[0].value,row[1].value,row[2].value,row[3].value,row[4].value,row[5].value,row[6].value))
            con.commit()
        except Exception:
            await mes.answer(f"Сотрудник @{row[0].value} уже есть в базе данных!")
    await mes.answer("Добавление завершено.", reply_markup=murkups.adminKBdb)
    await FSM.AdminSendFileDB.waitCommand.set()
    os.remove(f"data/{mes.message_id}.xlsx")



@dp.message_handler(Text("Удалить", ignore_case=True), state=FSM.AdminSendFileDB.waitCommand)
async def remove_employye_db(mes:types.Message):
    list_employee = cur.execute("SELECT * FROM employee").fetchall()
    if len(list_employee)==0:
        await mes.answer("База данных пуста!")
        return
    m = ""
    for emp in list_employee:
        m += f"<b>ID-{emp[0]}</b>\n├<b>ФИО:</b> {emp[2]} {emp[3]} {emp[4]}\n└<b>Telegram:</b> @{emp[1]}\n"
    await mes.answer(m, parse_mode=types.ParseMode.HTML)
    await mes.answer("Выберите действия", reply_markup=murkups.adminKBremove)
    await FSM.AdminSendFileDB.waitToRemove.set()

@dp.message_handler(Text("По ID", ignore_case=True), state=FSM.AdminSendFileDB.waitToRemove)
async def send_remove_by_id(mes:types.Message):
    await mes.answer("Отправьте ID сотрудника, которого хотели бы удалить", reply_markup=murkups.stopDeleteKB)
    await FSM.AdminSendFileDB.removeByID.set()

@dp.message_handler(state=FSM.AdminSendFileDB.removeByID)
async def remove_by_id(mes:types.Message):
    list_employee = cur.execute("SELECT id FROM employee").fetchall()
    delete=False
    try:
        for i in list_employee:
            if mes.text == str(i[0]):
                delete = True
        if not delete:
            await mes.answer("Сотрудник не найден.\nПопробуйте еще раз!")
            return
    except Exception:
        await mes.answer("Попробуйте еще раз!")
        return
    try:
        cur.execute(f"DELETE FROM employee WHERE id = {mes.text} ")
        con.commit()
        await mes.answer("Сотрудник успешно удален из базы данных!", reply_markup=murkups.adminKBdb)
        await FSM.AdminSendFileDB.waitCommand.set()
    except Exception:
        await mes.answer("Сотрудник не найден.\nПопробуйте еще раз!")
        return

@dp.message_handler(Text("По фамилии", ignore_case=True), state=FSM.AdminSendFileDB.waitToRemove)
async def send_remove_by_surname(mes:types.Message):
    await mes.answer("Отправьте фамилию сотрудника, которого хотели бы удалить", reply_markup=murkups.stopDeleteKB)
    await FSM.AdminSendFileDB.removeBySurname.set()

@dp.message_handler(state=FSM.AdminSendFileDB.removeBySurname)
async def remove_by_surname(mes:types.Message):
    list_surnames = cur.execute(f"SELECT * FROM employee WHERE surname LIKE '{mes.text}%'").fetchall()
    try:
        if len(list_surnames)== 1:
            cur.execute(f"DELETE FROM employee WHERE surname LIKE '{mes.text}%'")
            con.commit()
            m = ""

            for emp in list_surnames:
                m += f"<b>ID-{emp[0]}</b>\n├<b>ФИО:</b> {emp[2]} {emp[3]} {emp[4]}\n└<b>Telegram:</b> @{emp[1]}\n"
            await mes.answer(m, parse_mode=types.ParseMode.HTML)
            await mes.answer("Сотрудник успешно удален из базы данных!", reply_markup=murkups.adminKBdb)
            await FSM.AdminSendFileDB.waitCommand.set()
        else:
            m = ""
            for emp in list_surnames:
                m += f"<b>ID-{emp[0]}</b>\n├<b>ФИО:</b> {emp[2]} {emp[3]} {emp[4]}\n└<b>Telegram:</b> @{emp[1]}\n"
            await mes.answer(m, parse_mode=types.ParseMode.HTML)
            await mes.answer(f"Найдено сотрудников с такой фамилией: {len(list_surnames)}\nОтправьте ID нужного сотрудника")
            await FSM.AdminSendFileDB.waitID.set()
    except Exception:
        await mes.answer("Сотрудник не найден.\nПопробуйте еще раз!")
        return
@dp.message_handler(state=FSM.AdminSendFileDB.waitID)
async def remove_id(mes:types.Message):
    list_surnames = cur.execute(f"SELECT * FROM employee WHERE id={mes.text}").fetchall()
    try:
        cur.execute(f"DELETE FROM employee WHERE id={mes.text}")
        con.commit()
        m = ""
        for emp in list_surnames:
            m += f"<b>ID-{emp[0]}</b>\n├<b>ФИО:</b> {emp[2]} {emp[3]} {emp[4]}\n└<b>Telegram:</b> @{emp[1]}\n"
        await mes.answer(m, parse_mode=types.ParseMode.HTML)
        await mes.answer("Сотрудник успешно удален из базы данных!", reply_markup=murkups.adminKBdb)
        await FSM.AdminSendFileDB.waitCommand.set()
    except Exception:
        await mes.answer("Сотрудник не найден!.\nВозможно введен неверный ID, попробуйте еще раз!")
        return



@dp.message_handler(state=FSM.AdminSendFileDB.waitFileExel, content_types=types.ContentType.DOCUMENT)
async def test_save(mes: types.Message, state: FSMContext):
    file = await bot.get_file(mes.document.file_id)
    await bot.download_file(file.file_path, "data/file.xlsx")

    os.remove("data/file.xlsx")
    await state.finish()



@dp.message_handler(commands="id_chat")
async def id_chat(mes: types.Message):
    list_usernames = cur.execute("SELECT id_login_tg FROM admins").fetchall()
    if not mes.from_user.username in [log[0] for log in list_usernames]:
        await mes.answer(f"@{mes.from_user.username}, к сожаленю у вас нет доступа к этой команде!")
        return
    await bot.send_message(mes.from_user.id, mes.chat.id)


@dp.message_handler(Text("Анонимно с модерацией", ignore_case=True))
async def anonim_with_moder(mes: types.Message):
    await mes.answer(f"Отправьте свой вопрос в чат.\nОн будет <b>анонимно</b> отправлен модератору.",
                     parse_mode=types.ParseMode.HTML,
                     reply_markup=murkups.stopKbOffer)
    await FSM.contactModer.waitMessage.set()

@dp.message_handler(state=FSM.contactModer.waitMessage, )
async def send_to_moder(mes:types.Message, state: FSMContext):
    # date_string = datetime.datetime.now().strftime('%d.%m.%y %H:%M:%S')
    for m in config.MEF_employee:
        await bot.send_message(m, f"<b>Поступила новая анонимная просьба!\n\nТекст обращения:</b>\n{mes.text}",
                           parse_mode=types.ParseMode.HTML,)
    await mes.answer("Сообщение отправлено модератору!", reply_markup=murkups.changekb)
    await state.finish()

# @dp.callback_query_handler()
# async def chat_with_moder_and_user(call:types.CallbackQuery):
#     user_id = call.message.text[call.message.text.find(": ") + 2:call.message.text.find("Д")]
#     if call.from_user.id == config.MEF_employee:
#         await bot.send_message(config.MEF_employee, f"Отправьте ответ пользователю <code>{user_id}</code>",
#                                parse_mode=types.ParseMode.HTML, reply_markup=murkups.stopKbOffer)
#         with open("data/user_id.txt", "w") as file:
#             file.write(user_id)
#         await FSM.contactModer.moder_to_user.set()
#     else:
#         await bot.send_message(call.from_user.id, f"Отправьте ответ модератору", reply_markup=murkups.stopKbOffer)
#         await FSM.contactModer.user_to_moder.set()
# @dp.message_handler(state=FSM.contactModer.moder_to_user)
# async def moder_to_user(mes:types.Message, state: FSMContext):
#     with open("data/user_id.txt", "r") as file:
#         user_id = file.read()
#     await bot.send_message(user_id, f"<b>Ответ модератора:</b>\n\n{mes.text}",
#                            parse_mode=types.ParseMode.HTML, reply_markup=murkups.moderChatKB)
#     await mes.reply(f"Ответ пользователю <code>{user_id}</code> отправлен!",  reply_markup=murkups.mainkb,
#                     parse_mode=types.ParseMode.HTML)
#     os.remove("data/user_id.txt")
#     await state.finish()

# @dp.message_handler(state=FSM.contactModer.user_to_moder)
# async def user_to_moder(mes:types.Message, state:FSMContext):
#     date_string = datetime.datetime.now().strftime('%d.%m.%y %H:%M:%S')
#     await bot.send_message(config.MEF_employee,f"<b>Пользователь: <code>{mes.from_user.id}</code>\nДата: {date_string}</b>\n\n" + mes.text,
#                                         reply_markup=murkups.moderChatKB, parse_mode=types.ParseMode.HTML)
#     await mes.reply("Ответ отправлен!", reply_markup=murkups.mainkb)
#     await state.finish()




@dp.message_handler(Text("Готов участвовать в реализации идеи!", ignore_case=True))
async def offer(mes: types.Message):
    if mes.chat.type == "group":
        return
    await mes.answer("Отправьте свое предложение.", reply_markup=murkups.stopKbOffer)
    await FSM.SendOffer.waitOffer.set()


@dp.message_handler(state=FSM.SendOffer.waitOffer)
async def send_offet_chat(mes: types.Message, state: FSMContext):
    await bot.send_message(config.chat_id,
                           f"Предложение от @{mes.from_user.username}\nДавайте поддержим!\n\nПредложение:\n{mes.text}")
    await mes.answer("Предложение успешно отправлено!", reply_markup=murkups.mainkb)
    await state.finish()


@dp.message_handler(Text("Предложить изменения/Что то улучшить", ignore_case=True))
async def change_com(mes: types.Message):
    if mes.chat.type == "group":
        return
    await mes.answer("Выберите команду:", reply_markup=murkups.changekb)


@dp.message_handler(Text("Найти сотрудника", ignore_case=True))
async def change_com(mes: types.Message):
    if mes.chat.type == "group":
        return
    list_usernames = cur.execute("SELECT id_login_tg FROM employee").fetchall()
    if not mes.from_user.username in [log[0] for log in list_usernames]:
        await mes.answer(f"@{mes.from_user.username}, к сожаленю у вас нет доступа к этой команде!")
        return
    await mes.answer(f"Введите фамилию сотрудника:", reply_markup=murkups.findemployeb)
    await FSM.findemployee.textfind.set()


@dp.message_handler(state=FSM.findemployee.textfind, content_types=types.ContentType.TEXT)
async def find_emp(mes: types.Message):
    try:
        list_employee = cur.execute(f"SELECT * FROM employee WHERE surname LIKE '{mes.text}%'").fetchall()
        m = ""
        for emp in list_employee:
            m += f"<b>{emp[0]}</b> {emp[2]} {emp[3]} {emp[4]}\n"
        await mes.answer(m, parse_mode=types.ParseMode.HTML)
    except Exception as ex:
        await mes.answer("Сотрудников с такой фамилией не найдено!\nВведите фамилию еще раз:")
        return
    await mes.answer("Введите номер нужного сотрудника:")
    await FSM.findemployee.numemp.set()


@dp.message_handler(state=FSM.findemployee.numemp, content_types=types.ContentType.TEXT)
async def print_emp(mes: types.Message, state: FSMContext):
    try:
        emp = cur.execute(f"SELECT * FROM employee WHERE id = '{mes.text}'").fetchone()
        text = f"<b>Телеграм:</b> @{emp[1]}\n<b>ФИО:</b> {emp[2]} {emp[3]} {emp[4]}\n<b>Номер телефона:</b> {emp[5]}\n<b>День рождения:</b> {emp[6]}\n<b>Сейчас в отпуске:</b> {emp[7]}"
        await mes.answer(text, parse_mode=types.ParseMode.HTML, reply_markup=murkups.mainkb)
    except Exception as ex:
        await mes.answer("Неверно введен номер!\nВведите номер еще раз:")
        return
    await state.finish()


@dp.message_handler()
async def error_command(mes: types.Message):
    if mes.chat.type == "group":
        return
    await mes.answer("Не знаю что на это и ответить!")



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

